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
        logger.debug(exc.message,exc_info=True)
    
from shopback.trades.models import MergeTrade

  
@task()
def task_Push_SaleTrade_Finished(pre_days=10):
    
    day_date = datetime.datetime.now() - datetime.timedelta(days=pre_days)
    
    strades = SaleTrade.objects.filter(status=SaleTrade.WAIT_BUYER_CONFIRM_GOODS)
    for strade in strades:
        mtrades = MergeTrade.objects.filter(tid=strade.tid,type=MergeTrade.SALE_TYPE)
        if mtrades.count() == 0:
            continue
        
        mtrade = mtrades[0]
        
        if mtrade.sys_status in (MergeTrade.INVALID_STATUS,
                                 MergeTrade.EMPTY_STATUS,):
            strade.status =  SaleTrade.TRADE_CLOSED
            strade.save()
        
        elif (mtrade.sys_status == MergeTrade.FINISHED_STATUS and 
              (not mtrade.weight_time or mtrade.weight_time < day_date)):
            sale_refunds = SaleRefund.objects.filter(trade_id=mtrade.id,status__gt=SaleRefund.REFUND_CLOSED)
            if sale_refunds.count() > 0:
                continue
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
        raise confirmTradeChargeTask.retry(exc=exc)
            



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
        raise notifyTradePayTask.retry(exc=exc)


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
        
        srefund.refund_Confirm()
        strade = MergeTrade.objects.get(id=srefund.trade_id)
    
        saleservice = FlashSaleService(strade)
        saleservice.payTrade()
    
    except Exception,exc:
        raise notifyTradeRefundTask.retry(exc=exc)
        

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
        
            
@task
def push_SaleTrade_To_MergeTrade():
    """ 更新特卖订单到订单列表 """
    
    saletrades = SaleTrade.objects.filter(status=SaleTrade.WAIT_SELLER_SEND_GOODS)
    for strade in saletrades:
        mtrades = MergeTrade.objects.filter(tid=strade.tid,type=MergeTrade.SALE_TYPE)
        if mtrades.count() > 0 and mtrades[0].modified >= strade.modified:
            continue
        saleservice = FlashSaleService(strade)
        saleservice.payTrade()
        
import pingpp
from flashsale.pay.models import Envelop

@task
def task_Pull_Red_Envelope(pre_day=7):
    """更新红包 
    {
      "status": "SENDING", 
      "body": "\u4e00\u4efd\u8015\u8018\uff0c\u4e00\u4efd\u6536\u83b7\uff0c\u8c22\u8c22\u4f60\u7684\u52aa\u529b\uff01", 
      "object": "red_envelope", 
      "description": "\u5c0f\u9e7f\u5988\u5988\u7f16\u53f7:2540,\u63d0\u73b0\u524d:12160", 
      "order_no": "4348", 
      "extra": {
        "nick_name": "\u4e0a\u6d77\u5df1\u7f8e\u7f51\u7edc\u79d1\u6280", 
        "send_name": "\u5c0f\u9e7f\u7f8e\u7f8e"
      }, 
      "app": "app_LOOajDn9u9WDjfHa", 
      "livemode": true, 
      "paid": true, 
      "created": 1434975877, 
      "transaction_no": "100000000020150622316876646289", 
      "currency": "cny", 
      "amount": 5000, 
      "received": null, 
      "recipient": "our5huB4NHz2D7XTkdWTcurQXsYc", 
      "id": "red_9ujLmDSqPG8Ov5ab1C9WXLuH", 
      "channel": "wx_pub", 
      "subject": "\u94b1\u5305\u63d0\u73b0"
    }
    """
    today = datetime.datetime.now()
    pre_date = today - datetime.timedelta(days=pre_day)
    
    pingpp.api_key = settings.PINGPP_APPKEY
    
    page_size = 100
    has_next = True
    starting_after = None
    while has_next:
        if starting_after:
            resp = pingpp.RedEnvelope.all(limit=page_size,
                                          created={'gte':pre_date,'lte':today},
                                          starting_after=starting_after)  
        else:
            resp = pingpp.RedEnvelope.all(limit=page_size,
                                          created={'gte':pre_date,'lte':today})  
        has_next = resp['has_more']
        if not has_next:
            break
        
        for e in resp['data']:
            env = Envelop.objects.get(id=e['order_no'])
            env.envelop_id = e['id']
            env.livemode   = e['livemode']
            if env.status in (Envelop.WAIT_SEND,Envelop.CANCEL) :
                env.status = Envelop.FAIL
            env.save()
        else:
            starting_after = e['id']
            
            
  
