#-*- coding:utf8 -*-
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime
from shopback.monitor.models import SystemConfig
from shopback.trades.models import MergeTrade,MergeBuyerTrade,WAIT_CONFIRM_SEND_STATUS,SYSTEM_SEND_TAOBAO_STATUS\
    ,FINISHED_STATUS,AUDITFAIL_STATUS,ON_THE_FLY_STATUS,REGULAR_REMAIN_STATUS
from shopback.users.models import User
from auth import apis
import logging

logger = logging.getLogger('trades.handler')


@apis.single_instance_task(30*60,prefix='shopback.trades.tasks.')
def syncConfirmDeliveryTradeTask():
    system_config = SystemConfig.getconfig()
    status_list = [WAIT_CONFIRM_SEND_STATUS,SYSTEM_SEND_TAOBAO_STATUS] if system_config.is_confirm_delivery_auto else [SYSTEM_SEND_TAOBAO_STATUS]
    merge_trades = MergeTrade.objects.filter(sys_status__in = status_list)
    for trade in merge_trades:
        try:
            response = apis.taobao_logistics_online_send(tid=trade.tid,out_sid=trade.out_sid
                                          ,company_code=trade.logistics_company_code,tb_user_id=trades.seller_id)
        except Exception,exc:
            trade.sys_status = AUDITFAIL_STATUS
            trade.reverse_audit_reason += '--发货状态更新失败'.decode('utf8')
            trade.save()
        else:
            if response['delivery_online_send_response']['shipping']['is_success']:
                trade.sys_status = FINISHED_STATUS
                trade.consign_time = datetime.datetime.now()
                MergeTrade.objects.filter(tid=trade.tid).update(
                    sys_status=trade.sys_status,
                    consign_time=trade.consign_time,)
                
                merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid=trade.tid)
                for merge_buyer_trade in merge_buyer_trades:
                    try:
                        sub_merge_trade = MergeTrade.objects.get(tid=merge_buyer_trade.sub_tid,sys_status=ON_THE_FLY_STATUS)
                    except Exception,exc:
                        logger.error('飞行模式订单(tid:%d)未找到'%merge_buyer_trade.sub_tid)
                    else:
                        try:
                            apis.taobao_logistics_online_send(tid=merge_buyer_trade.sub_tid,out_sid=trade.out_sid
                                              ,company_code=trade.logistics_company_code,tb_user_id=trades.seller_id)
                        except Exception,exc:
                            sub_merge_trade.sys_status = AUDITFAIL_STATUS
                            sub_merge_trade.reverse_audit_reason += ('--主订单(id:%d)发货成功，但次订单(%d)发货失败'%(trade.tid,sub_merge_trade.main_tid)).decode('utf8')
                            sub_merge_trade.save()
                        else:
                            if response['delivery_online_send_response']['shipping']['is_success']:
                                sub_merge_trade.sys_status = FINISHED_STATUS
                                sub_merge_trade.consign_time = datetime.datetime.now()
                                MergeTrade.objects.filter(tid=sub_merge_trade.tid).update(
                                    sys_status=sub_merge_trade.sys_status,
                                    consign_time=sub_merge_trade.consign_time,
                                    )
                            else :
                                logger.error('delivery trade(%s) fail,response:%s'%(sub_merge_trade.tid,response))
            else :
                logger.error('delivery trade(%s) fail,response:%s'%(trade.tid,response))

       
@task()
def regularRemainOrderTask():
    #更新定时提醒订单
    dt = datetime.datetime.now()
    dt = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)
    MergeTrade.objects.filter(sys_status=REGULAR_REMAIN_STATUS,remind_time__lte=dt).update(sys_status=AUDITFAIL_STATUS)

        