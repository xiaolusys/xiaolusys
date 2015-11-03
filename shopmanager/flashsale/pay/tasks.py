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
from common.utils import update_model_fields
from .service import FlashSaleService
from .options import get_user_unionid
import logging

__author__ = 'meixqhi'

logger = logging.getLogger('celery.handler')


@task()
def task_Update_Sale_Customer(unionid,openid=None,app_key=None):
    """ 更新特卖用户　微信授权信息 """
    if openid and app_key:
        WeixinUnionID.objects.get_or_create(openid=openid,app_key=app_key,unionid=unionid)
        
    try:
        profile, state = Customer.objects.get_or_create(unionid=unionid)
        
        wxuser = WeiXinUser.objects.get(models.Q(openid=openid)|models.Q(unionid=unionid))
        profile.nick   = profile.nick.strip() or wxuser.nickname
        profile.mobile = profile.mobile.strip() or wxuser.mobile
        profile.openid = profile.openid or openid  
        profile.save()
            
    except Exception,exc:
        logger.debug(exc.message,exc_info=True)
        

@task()
def task_Merge_Sale_Customer(user, code):
    """ 根据当前登录用户，更新微信授权信息 """
    
    app_key     = settings.WXPAY_APPID
    app_secret  = settings.WXPAY_SECRET
    
    openid,unionid = get_user_unionid(code,appid=app_key,secret=app_secret)
    if not openid:
        return 
    
    WeixinUnionID.objects.get_or_create(openid=openid,app_key=app_key,unionid=unionid)
    
    try:
        profile, state = Customer.objects.get_or_create(user=user)
        wxuser = WeiXinUser.objects.get(models.Q(openid=openid)|models.Q(unionid=unionid))
        profile.nick   = wxuser.nickname
        profile.mobile = profile.mobile or wxuser.mobile
        profile.openid = profile.openid.strip() or openid
        profile.unionid = profile.unionid.strip() or unionid
        profile.save()
        
        customers = Customer.objects.filter(unionid=unionid)    
        for customer in customers:
            if customer.id == profile.id:
                continue
            customer.status = Customer.DELETE
            customer.save()
            
            strades = SaleTrade.objects.filter(buyer_id=customer.id)
            for strade in strades:
                log_action(user.id,  strade, CHANGE, u'用户订单转移至:%s'%user.id) 
                strade.buyer_id = profile.id
                update_model_fields(strade,update_fields=['buyer_id'])
            
    except Exception,exc:
        logger.debug(exc.message,exc_info=True)
        
    

    
from shopback.trades.models import MergeTrade,MergeOrder

@task()
def task_Push_SaleTrade_Finished(pre_days=10):
    """ 定时将待确认状态小鹿特卖订单更新成已完成
    1,查找明细订单对应的MergeOrder;
    2,根据MergeOrder父订单状态更新Saleorder状态；
    3,根据SaleTrade的所有SaleOrder状态更新SaleTrade状态;
    """
    
    day_date = datetime.datetime.now() - datetime.timedelta(days=pre_days)
    strades = SaleTrade.objects.filter(
        status__in=(SaleTrade.WAIT_SELLER_SEND_GOODS,SaleTrade.WAIT_BUYER_CONFIRM_GOODS),
        pay_time__gte=day_date
    )
    for strade in strades:
        for order in strade.normal_orders:
            trade_oid = order.oid
            morders = MergeOrder.objects.filter(
                oid=trade_oid,
                merge_trade__type=MergeTrade.SALE_TYPE,
                merge_trade__sys_status__in=MergeTrade.WAIT_WEIGHT_STATUS,
                sys_status=MergeOrder.NORMAL
            )
            if not morders.exists() and order.refund_status in SaleOrder.REFUNDABLE_STATUS :
                order.status = SaleOrder.TRADE_CLOSED
            else:
                morder = morders[0]
                mtrade = morder.merge_trade
                if mtrade.sys_status == MergeTrade.FINISHED_STATUS:
                    order.status = SaleOrder.WAIT_BUYER_CONFIRM_GOODS
            order.save()
        if strade.normal_orders.count() == 0 :
            strade.status = SaleTrade.TRADE_CLOSED
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
    """ 订单确认支付通知消息，如果订单分阶段支付，则在原单ID后追加:[tid]-[数字] """
    try:
        order_no = notify['order_no']
        charge   = notify['id']
        paid     = notify['paid']
        
        tcharge,state = TradeCharge.objects.get_or_create(order_no=order_no,charge=charge)
        if not paid or tcharge.paid == True :
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
        
        order_no_tuple  = order_no.split('-')
        is_post_confirm = False
        if len(order_no_tuple) > 1:
            is_post_confirm = True
            
        charge_time = tcharge.time_paid
        strade = SaleTrade.objects.get(tid=order_no_tuple[0])
        confirmTradeChargeTask(strade.id, charge_time=charge_time, post_charge=is_post_confirm)
    
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
                   u'%s(金额:%s)'%([u'退款失败',u'退款成功'][notify['succeed'] and 1 or 0],notify['amount']))
        
        if not notify['succeed']:
            srefund.feedback += notify.get('failure_msg','') or ''
            srefund.save()
            logger.error('refund error:%s'%notify)
            return 
        
        srefund.refund_Confirm()
        
        strade = SaleTrade.objects.get(id=srefund.trade_id)
        if strade.is_Deposite_Order():
            return
        
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

        from shopback.refunds.models import Refund
        
        seller = getOrCreateSaleSeller()
        sorder = SaleOrder.objects.get(id=sale_refund.order_id)
        refund,state  = Refund.objects.get_or_create(tid=strade.tid,
                                                     oid=sorder.oid)
        refund.user = seller
        refund.title = sorder.title
        refund.payment = sale_refund.payment
        refund.buyer_nick = strade.buyer_nick or strade.receiver_name
        refund.mobile     = strade.receiver_mobile
        if sale_refund.has_good_return:
            refund.status = Refund.REFUND_WAIT_RETURN_GOODS
            refund.has_good_return = sale_refund.has_good_return
        else:
            refund.status = Refund.REFUND_WAIT_SELLER_AGREE
        refund.save()
        
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
        
        for e in resp['data']:
            envelop = Envelop.objects.get(id=e['order_no'])
            envelop.handle_envelop(e)
        else:
            starting_after = e['id']
        
        has_next = resp['has_more']
        if not has_next:
            break
            

# 2015-10-7 修改该任务到新版本优惠券
from models_coupon_new import CouponsPool, UserCoupon, CouponTemplate
from django.db import transaction


def Update_CouponPoll_Status(type=None):
    today = datetime.datetime.today()
    # 定时更新优惠券的状态:超过截至时间的优惠券 将其状态修改为过期无效状态
    # 找到截至时间 是昨天的 优惠券
    deadline_time = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
    # 未发放的 已经发放的 可以使用的  （截至时间小于昨天的）
    cous = CouponsPool.objects.filter(template__type=type, template__deadline__lte=deadline_time,
                                      status__in=(CouponsPool.RELEASE, CouponsPool.UNRELEASE))
    for cou in cous:
        cou.status = CouponsPool.PAST  # 修改为无效的优惠券
        cou.save()


@task
@transaction.commit_on_success
def task_Update_CouponPoll_Status():
    # 修改C259_20　和　C150_10　类型的优惠券状态
    # 2015-10-7
    Update_CouponPoll_Status(type=CouponTemplate.C150_10)
    Update_CouponPoll_Status(type=CouponTemplate.C259_20)
