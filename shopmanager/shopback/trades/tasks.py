#-*- coding:utf8 -*-
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback import paramconfig as pcfg
from shopback.orders.models import Trade,Order
from shopback.trades.models import MergeTrade,MergeBuyerTrade,merge_order_remover
from shopback.base import log_action,User as DjangoUser, ADDITION, CHANGE
from shopback.users.models import User
from auth import apis
import logging

logger = logging.getLogger('trades.handler')


class SubTradePostException(Exception):

    def __init__(self,msg=''):
        self.msg  = msg

    def __str__(self):
        return self.msg
       
       
@task()
def sendTaobaoTradeTask(request_user_id,trade_id):
    """ 淘宝发货任务 """
    
    try:
        trade = MergeTrade.objects.get(id=trade_id)
        if trade.sys_status not in (pcfg.WAIT_PREPARE_SEND_STATUS,
                        pcfg.WAIT_CHECK_BARCODE_STATUS,pcfg.WAIT_SCAN_WEIGHT_STATUS):
            return
        if trade.type in (pcfg.DIRECT_TYPE,pcfg.EXCHANGE_TYPE):
            trade.sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS
            trade.status=pcfg.WAIT_BUYER_CONFIRM_GOODS
            trade.consign_time=datetime.datetime.now()
            trade.save()
            return 
        
        error_msg = ''
        main_post_success = False
        logistics_company_code = trade.logistics_company.code     
        try:
            merge_buyer_trades = []
            #判断是否有合单子订单
            if trade.has_merge:
                merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid=trade.tid)
                
            for sub_buyer_trade in merge_buyer_trades:
                sub_post_success = False
                try:
                    sub_trade = MergeTrade.objects.get(tid=sub_buyer_trade.sub_tid)
                    sub_trade.out_sid      = trade.out_sid
                    sub_trade.logistics_company = trade.logistics_company
                    sub_trade.save()
                    company_code = sub_trade.logistics_company.code if sub_trade.type==pcfg.COD_TYPE\
                         else pcfg.SUB_TRADE_COMPANEY_CODE
                    sub_trade.send_trade_to_taobao(company_code=company_code)
                except Exception,exc:
                    error_msg = exc.message
                else:
                    sub_post_success = True
                        
                if sub_post_success:
                    sub_trade.operator=trade.operator
                    sub_trade.sys_status=pcfg.FINISHED_STATUS
                    sub_trade.consign_time=datetime.datetime.now()
                    sub_trade.save()
                    log_action(request_user_id,sub_trade,CHANGE,u'订单发货成功')
                else:
                    sub_trade.append_reason_code(pcfg.POST_SUB_TRADE_ERROR_CODE)
                    sub_trade.sys_status=pcfg.WAIT_AUDIT_STATUS
                    sub_trade.is_picking_print=False
                    sub_trade.is_express_print=False
                    sub_trade.save()
                    log_action(request_user_id,sub_trade,CHANGE,u'订单发货失败：%s'%error_msg)
                    raise SubTradePostException(error_msg)
        
            trade.send_trade_to_taobao()
        except SubTradePostException,exc:
            trade.append_reason_code(pcfg.POST_SUB_TRADE_ERROR_CODE)
            trade.sys_status=pcfg.WAIT_AUDIT_STATUS
            trade.save()
            log_action(request_user_id,trade,CHANGE,u'子订单(%d)发货失败:%s'%(sub_trade.id,exc.message))
        except Exception,exc:
            error_msg = exc.message
        else:
            main_post_success = True
                
        if main_post_success:
            trade.sys_status=pcfg.WAIT_CHECK_BARCODE_STATUS
            trade.consign_time=datetime.datetime.now()
            trade.save()
            log_action(request_user_id,trade,CHANGE,u'订单发货成功')
        else:
            trade.append_reason_code(pcfg.POST_MODIFY_CODE)
            trade.sys_status=pcfg.WAIT_AUDIT_STATUS
            trade.is_picking_print=False
            trade.is_express_print=False
            trade.save()                                                                                       
            log_action(request_user_id,trade,CHANGE,u'订单发货失败:%s'%error_msg)
            merge_order_remover(trade.tid)   
    except Exception,exc:
        logger.error('post trade error====='+exc.message,exc_info=True)
        #sendTaobaoTradeTask.retry(countdown=5, exc=exc)

       
@task()
def regularRemainOrderTask():
    """更新定时提醒订单"""
    dt = datetime.datetime.now()
    MergeTrade.objects.filter(sys_status=pcfg.REGULAR_REMAIN_STATUS,remind_time__lte=dt).update(sys_status=pcfg.WAIT_AUDIT_STATUS)

@task
def saveTradeByTidTask(tid,seller_nick):
    user = User.objects.get(nick=seller_nick)
    Trade.get_or_create(tid,user.visitor_id)
    
@task()
def importTradeFromFileTask(fileName):
    """根据导入文件获取淘宝订单"""
    with open(fileName,'r') as f:
        for line in f:
            if line:
                try:
                    seller_nick,tid = line.split(',')
                    if tid:
                        subtask(saveTradeByTidTask).delay(tid,seller_nick.decode('gbk'))
                except:
                    pass
    
    
