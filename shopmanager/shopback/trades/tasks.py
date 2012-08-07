#-*- coding:utf8 -*-
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime
from shopback.monitor.models import SystemConfig
from shopback.trades.models import MergeTrade,WAIT_CONFIRM_SEND_STATUS,SYSTEM_SEND_TAOBAO_STATUS,FINISHED_STATUS,AUDITFAIL_STATUS
from shopback.users.models import User
from auth import apis
import logging

logger = logging.getLogger('trades.handler')


@task()
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
            trade.reverse_audit_reason += '与淘宝后台同步确认发货失败，请查询淘宝该单状态是否改变,'
            trade.save()
        else:
            if response['delivery_online_send_response']['shipping']['is_success']:
                trade.sys_status = FINISHED_STATUS
                trade.consign_time = datetime.datetime.now()
                trade.save()
            else :
                logger.error('delivery trade(%s) fail,response:%s'%(trade.tid,response))
        