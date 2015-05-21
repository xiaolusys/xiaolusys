#-*- encoding:utf8 -*-
import time
import datetime
import calendar
from django.conf import settings
from django.db import models
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings

from shopback.users.models import User
from shopapp.weixin.models import WeiXinUser,WeixinUnionID
from flashsale.pay.models import TradeCharge,SaleTrade,SaleOrder,SaleRefund,Customer
from .service import FlashSaleService
import logging

__author__ = 'meixqhi'

logger = logging.getLogger('celery.handler')


@task()
def task_Update_Sale_Customer(unionid,openid=None,app_key=None):
    
    if openid and app_key:
        WeixinUnionID.objects.get_or_create(openid=openid,app_key=app_key,unionid=unionid)
        
    try:
        profile, state = Customer.objects.get_or_create(unionid=unionid)
        
        wxuser = WeiXinUser.objects.get(models.Q(openid=openid)|models.Q(unionid=unionid))
        profile.nick   = wxuser.nickname
        profile.mobile = wxuser.mobile
        profile.openid = profile.openid or openid or ''
        profile.save()
            
    except Exception,exc:
        pass
    
from shopback.trades.models import MergeTrade

  
@task()
def task_Push_SaleTrade_Finished(pre_days=10):
    
    day_date = datetime.datetime.now() - datetime.timedelta(days=pre_days)
    
    strades = SaleTrade.objects.filter(status=SaleTrade.WAIT_BUYER_CONFIRM_GOODS)
    for strade in strades:
        mtrades = MergeTrade.objects.filter(tid=strade.tid,type=MergeTrade.SALE_TYPE)
        if mtrades.count() > 0:
            mtrade = mtrades[0]
            
            if mtrade.sys_status in (MergeTrade.INVALID_STATUS,
                                     MergeTrade.EMPTY_STATUS,):
                strade.status =  SaleTrade.TRADE_CLOSED
                strade.save()
            
            elif mtrade.sys_status == MergeTrade.FINISHED_STATUS and (not mtrade.weight_time or mtrade.weight_time < day_date):
                strade.status =  SaleTrade.TRADE_FINISHED
                strade.save()


@task(max_retry=3,default_retry_delay=60)
def confirmTradeChargeTask(sale_trade_id,charge_time=None):
    
    try:
        strade = SaleTrade.objects.get(id=sale_trade_id)
        
        strade.charge_confirm(charge_time=charge_time)
        
        saleservice = FlashSaleService(strade)
        saleservice.payTrade()
            
    except Exception,exc:
        raise pushTradeRefundTask.retry(exc=exc)
            



@task(max_retry=3,default_retry_delay=60)
def notifyTradePayTask(notify):

    try:
        order_no = notify['order_no'].split('_')[0]
        charge   = notify['id']
        
        tcharge,state = TradeCharge.objects.get_or_create(order_no=order_no,charge=charge)
        
        if tcharge.paid == True:
            return
         
        update_fields = set(['paid','refunded','channel','amount','currency','transaction_no',
                         'amount_refunded','failure_code','failure_msg','time_paid','time_expire'])
    
        for k,v in notify.iteritems():
            if k not in update_fields:
                continue
            
            if k in ('time_paid','time_expire'):
                v = v and datetime.datetime.fromtimestamp(v)
            
            if k in ('failure_code','failure_msg'):
                v = v or ''
            
            hasattr(tcharge,k) and setattr(tcharge,k,v)
            
        tcharge.save()
        
        strade = SaleTrade.objects.get(tid=order_no)
        
        confirmTradeChargeTask(strade.id)
    
    except Exception,exc:
        raise pushTradeRefundTask.retry(exc=exc)


from shopback.base import log_action, ADDITION, CHANGE 
from .options import getOrCreateSaleSeller

@task(max_retry=3,default_retry_delay=60)
def notifyTradeRefundTask(notify):
    
    try:
        refund_id = notify['id']
        
        seller = getOrCreateSaleSeller()
        srefund = SaleRefund.objects.get(refund_id=refund_id)
        
        log_action(seller.user.id,srefund,CHANGE,
                   u'%s(金额:%s)'%([u'退款成功',u'退款失败'][notify['succeed'] and 1 or 0],notify['amount']))
        
        if not notify['succeed']:
            logger.error('refund error:%s'%notify)
            return 
        
        srefund.status = SaleRefund.REFUND_SUCCESS
        srefund.save()
        
        sorder = SaleOrder.objects.get(id=srefund.order_id)
        sorder.refund_status = SaleRefund.REFUND_SUCCESS
        if sorder.sale_trade.status == SaleTrade.WAIT_SELLER_SEND_GOODS:
            sorder.status = SaleTrade.TRADE_CLOSED
        sorder.save()
        
        strade = sorder.sale_trade
        if strade.normal_orders.count() == 0:
            strade.status = SaleTrade.TRADE_CLOSED
            strade.save()
    
        saleservice = FlashSaleService(strade)
        saleservice.payTrade()
    
    except Exception,exc:
        raise pushTradeRefundTask.retry(exc=exc)
        

@task(max_retries=3,default_retry_delay=30)
def pushTradeRefundTask(refund_id):
    #退款申请
    try:
        sale_refund = SaleRefund.objects.get(id=refund_id)
        trade_id    = sale_refund.trade_id
        
        strade = SaleTrade.objects.get(id=trade_id)
        
        saleservice = FlashSaleService(strade)
        saleservice.payTrade()
        
    except Exception,exc:
        raise pushTradeRefundTask.retry(exc=exc)
        
            
            
                       
                        

            
            
  
