#-*- encoding:utf-8 -*-
import time
import datetime
import calendar
from django.conf import settings
from django.db import models
from django.db import transaction
from celery.task import task
from celery.task.sets import subtask

from core.options import log_action, ADDITION, CHANGE 
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
        wxusers = WeiXinUser.objects.filter(unionid=unionid)
        if wxusers.exists():
            wxuser = wxusers[0]
            profile.openid = profile.openid or openid or ''
            profile.nick   = wxuser.nickname or profile.nick
            profile.mobile = profile.mobile.strip() or wxuser.mobile
            profile.thumbnail = wxuser.headimgurl or profile.thumbnail
            update_model_fields(profile,update_fields=['nick','mobile','openid','thumbnail'])
            
    except Exception,exc:
        logger.debug(exc.message,exc_info=True)
        
@task()
def task_Refresh_Sale_Customer(user_params,app_key=None):
    """ 更新特卖用户　微信授权信息 """
    openid, unionid = user_params.get('openid'),user_params.get('unionid')
    if not unionid:
        return 
    
    if openid and app_key:
        WeixinUnionID.objects.get_or_create(openid=openid,app_key=app_key,unionid=unionid)
        
    try:
        profiles = Customer.objects.filter(unionid=unionid,status=Customer.NORMAL)
        if not profiles.exists():
            return
        profile = profiles[0]
        wxusers = WeiXinUser.objects.filter(unionid=unionid)
        if not profile.mobile and wxusers.exists():
            profile.mobile =  wxusers[0].mobile
            
        profile.nick   = user_params.get('nickname') or profile.nick
        profile.openid = profile.openid or user_params.get('openid')
        profile.thumbnail = user_params.get('headimgurl') or profile.thumbnail
        update_model_fields(profile,update_fields=['nick','mobile','openid','thumbnail'])
            
    except Exception,exc:
        logger.debug(exc.message, exc_info=True)


@task()
def task_Merge_Sale_Customer(user, code):
    """ 根据当前登录用户，更新微信授权信息 """
    
    app_key     = settings.WXPAY_APPID
    app_secret  = settings.WXPAY_SECRET
    
    openid,unionid = get_user_unionid(code,appid=app_key,secret=app_secret)
    if not openid or not unionid:
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
    """ 
    定时将待确认状态小鹿特卖订单更新成已完成：
    1，查找明细订单对应的MergeOrder;
    2，根据MergeOrder父订单状态更新Saleorder状态；
    3，根据SaleTrade的所有SaleOrder状态更新SaleTrade状态;
    """
    day_date = datetime.datetime.now() - datetime.timedelta(days=pre_days)
    strades = SaleTrade.objects.filter(
        status__in=(SaleTrade.WAIT_SELLER_SEND_GOODS,
                    SaleTrade.WAIT_BUYER_CONFIRM_GOODS,
                    SaleTrade.TRADE_BUYER_SIGNED),
        pay_time__lte=day_date
    )
    for strade in strades:
        for sorder in strade.normal_orders:
            if sorder.is_finishable():
                sorder.status = SaleOrder.TRADE_FINISHED
                sorder.save()
        if strade.normal_orders.count() == 0:
            strade.status = SaleTrade.TRADE_CLOSED
            strade.save()
            
        normal_orders = strade.normal_orders
        finish_orders = strade.sale_orders.filter(status=SaleOrder.TRADE_FINISHED)
        if normal_orders.count() == finish_orders.count():
            strade.status = SaleTrade.TRADE_FINISHED
            strade.save()
                    

@task(max_retry=3,default_retry_delay=60)
def confirmTradeChargeTask(sale_trade_id,charge_time=None):
    from shopback.items.models import ProductSku
    strade = SaleTrade.objects.get(id=sale_trade_id)
    strade.charge_confirm(charge_time=charge_time)
    saleservice = FlashSaleService(strade)
    saleservice.payTrade()
    for sale_order in strade.sale_orders.all():
        ProductSku.objects.get(id=sale_order.sku_id).assign_packages()


@task(max_retry=3,default_retry_delay=60)
@transaction.atomic
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
        
#         order_no_tuple  = order_no.split('-')
#         is_post_confirm = False
#         if len(order_no_tuple) > 1:
#             is_post_confirm = True
            
        charge_time = tcharge.time_paid
        strade = SaleTrade.objects.get(tid=order_no)
        confirmTradeChargeTask(strade.id, charge_time=charge_time)
    
    except Exception,exc:
        logger.error('notifyTradePayTask:%s'%exc.message,exc_info=True)
        raise notifyTradePayTask.retry(exc=exc)


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


import pingpp

@task 
def pull_Paid_SaleTrade(pre_day=1,interval=1):
    """ pre_day:表示从几天前开始；interval:表示从pre_day开始更新多少天的数据 """
    target    =  datetime.datetime.now() - datetime.timedelta(days=pre_day)
    pre_date  = datetime.datetime(target.year,target.month,target.day)
    post_date = pre_date + datetime.timedelta(days=interval)
    
    pingpp.api_key = settings.PINGPP_APPKEY
    
    page_size = 50
    has_next = True
    starting_after = None
    while has_next:
        if starting_after:
            resp = pingpp.Charge.all(limit=page_size,
                                     created={'gte':pre_date,'lte':post_date},
                                     starting_after=starting_after)  
        else:
            resp = pingpp.Charge.all(limit=page_size,
                                     created={'gte':pre_date,'lte':post_date})  
        e = None
        for e in resp['data']:
            #notifyTradePayTask.s(e)()
            notifyTradePayTask(e)
        
        if e:
            starting_after = e['id']
        
        has_next = resp['has_more']
        if not has_next:
            break
    
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
        e = None
        for e in resp['data']:
            envelop = Envelop.objects.get(id=e['order_no'])
            envelop.handle_envelop(e)
        if e:
            starting_after = e['id']
        
        has_next = resp['has_more']
        if not has_next:
            break
            

from models_coupon_new import CouponsPool, CouponTemplate, UserCoupon
from django.db import transaction


@task
@transaction.atomic
def task_Update_CouponPoll_Status():
    """ 定时更新券池中的优惠券到过期过期状态　"""
    today = datetime.datetime.today()
    # 定时更新优惠券的状态:　超过模板定义截至时间的优惠券 将其状态修改为过期无效状态
    deadline_time = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
    # 未发放的 已经发放的   截止日期在今天之前的　排除邮费和代理优惠券
    cous = CouponsPool.objects.filter(template__deadline__lte=deadline_time,
                                      status__in=(CouponsPool.RELEASE, CouponsPool.UNRELEASE)).exclude(
        template__type__in=(CouponTemplate.RMB118, CouponTemplate.POST_FEE_5,
                            CouponTemplate.POST_FEE_10, CouponTemplate.POST_FEE_15,
                            CouponTemplate.POST_FEE_20))
    cous.update(status=CouponsPool.PAST)  # 更新为过期优惠券


@task()
def task_ReleaseMamaLinkCoupon(saletrade):
    """
    发放优惠券
    规则：　当代理的专属链接有用户下单后则给该代理发放优惠券
    """
    extras_info = saletrade.extras_info
    mama_id = extras_info.get('mm_linkid')
    if not mama_id:
        return
    now = datetime.datetime.now()
    tpls = CouponTemplate.objects.filter(valid=True, way_type=CouponTemplate.XMM_LINK)
    tpls = tpls.filter(release_start_time__lte=now, release_end_time__gte=now)
    for tpl in tpls:
        if saletrade.payment >= tpl.release_fee:  # 订单满足发放费用发放
            coupon = UserCoupon()
            coupon.release_for_mama(mama_id=mama_id, template_id=tpl.id, trade_id=saletrade.id)


from django.db.models import Q
from flashsale.xiaolumm.models_fans import XlmmFans
from flashsale.promotion.models_freesample import AppDownloadRecord
from shopapp.weixin.models import WeixinUnionID
from django.conf import settings


@task
def task_Record_Mama_Fans(instance, created):
    """
    记录代理粉丝任务
    1. 不是新创建的用户则不去处理
    2. 没有unionid，则不去处理（目前APP下载记录中只是保存了通过微信授权的openid）
    3. 没有下载记录的不去处理
    4. 当前用户是代理的不去处理
    5. 已经是代理粉丝的用户不去处理
    6. 创建粉丝记录
    """
    if not created:
        return
    if not instance.unionid:
        return
    # 获取对应openid
    WXPAY_APPID = settings.WXPAY_APPID
    weixin_user = WeixinUnionID.objects.filter(app_key=WXPAY_APPID, unionid=instance.unionid)
    openid = ''
    if weixin_user.exists():
        openid = weixin_user[0].openid
    mobile = instance.mobile
    downloads = AppDownloadRecord.objects.filter(Q(openid=openid) |
                                                 Q(mobile=mobile)).filter(status=False)  # 没有成为用户的记录
    if downloads.exists():
        download = downloads[0]
        # 存在记录则计算当前用户到下载记录的妈妈粉丝上
        from_customer = Customer.objects.get(pk=download.from_customer)
        if not from_customer:  # 没有找到推荐人则返回
            return
        ins_xlmm = instance.getXiaolumm()
        if ins_xlmm:  # 如果当前用户是小鹿妈妈则返回，不记录小鹿妈妈自己为自己的粉丝
            return
        fans = XlmmFans.objects.filter(xlmm_cusid=from_customer.id, fans_cusid=instance.id)
        if fans.exists():  # 存在粉丝记录返回
            return
        else:
            XlmmFans.objects.createFansRecord(str(from_customer.id), str(instance.id))
            download.status = True
            download.save()


from flashsale.pay.models_user import BudgetLog, UserBudget
from django.db.models import Sum

@task()
def task_budgetlog_update_userbudget(budget_log):
    customer_id = budget_log.customer_id
    records = BudgetLog.objects.filter(customer_id=customer_id, status=BudgetLog.CONFIRMED).values('budget_type').annotate(total=Sum('flow_amount'))
    
    in_amount,out_amount=0,0
    for entry in records:
        if entry["budget_type"] == BudgetLog.BUDGET_IN:
            in_amount = entry["total"]
        if entry["budget_type"] == BudgetLog.BUDGET_OUT:
            out_amount = entry["total"]

    user_budget = UserBudget.objects.get(user=customer_id)

    cash = in_amount - out_amount
    if user_budget.amount !=  cash:
        user_budget.amount = cash
        user_budget.save()

from extrafunc.renewremind.tasks import send_message
from flashsale.push.mipush import mipush_of_ios, mipush_of_android
from flashsale.protocol import get_target_url
from flashsale.protocol import constants
from shopapp.smsmgr.models import SMSActivity
from django.contrib.admin.models import CHANGE


def make_refund_message(refund):
    """ 根据短信模板生成要发送或者推送的文本信息 """
    desc = None
    if refund.status == SaleRefund.REFUND_WAIT_RETURN_GOODS:  # 同意申请退货
        desc = '请登陆APP查看退货地址信息，补充退货单物流信息'
    if refund.status == SaleRefund.REFUND_REFUSE_BUYER:  # 拒绝申请退款
        desc = '需要您参与协商退款事宜.'
    if refund.status == SaleRefund.REFUND_APPROVE:  # 等待返款
        desc = '请留意您的钱款去向.'
    if refund.status == SaleRefund.REFUND_SUCCESS:  # 退款成功
        desc = '祝您购物愉快.'

    sms_activitys = SMSActivity.objects.filter(id=5, status=True)
    if sms_activitys.exists() and desc:
        sms_activity = sms_activitys[0]
        message = sms_activity.text_tmpl.format(refund.title,  # 标题
                                                refund.refund_fee,  # 退款费用
                                                refund.get_status_display(),
                                                desc)  # 退款状态
        return message
    else:
        return None


def send_refund_msg(refund):
    """ 发送同意退款信息 """
    customer = refund.get_refund_customer()
    # 优先使用购买用户的手机号
    if customer.mobile:
        mobile = customer.mobile
    else:
        mobile = refund.mobile
    message = make_refund_message(refund)
    if message:
        send_message(mobile=mobile, message=message, taskName=refund.get_status_display())


def push_refund_app_msg(refend):
    """ 发送同意app推送 """
    customer_id = refend.buyer_id
    if customer_id:
        target_url = get_target_url(constants.TARGET_TYPE_REFUNDS)
        message = make_refund_message(refend)
        if message:
            mipush_of_android.push_to_account(customer_id,
                                              {'target_url': target_url},
                                              description=message)
            mipush_of_ios.push_to_account(customer_id,
                                          {'target_url': target_url},
                                          description=message)


@task
def task_send_msg_for_refund(refund):
    """
    退款单状态变化的时候
    发送推送以及短信消息给用户
    """
    if not isinstance(refund, SaleRefund):
        return
    send_refund_msg(refund)
    push_refund_app_msg(refund)


def close_refund(refund):
    """ 关闭退款单 """
    now = datetime.datetime.now()
    fifth_time = now - datetime.timedelta(days=30)  # days天前的时间

    order = SaleOrder.objects.get(id=refund.order_id)
    if order.status not in [SaleOrder.TRADE_BUYER_SIGNED, SaleOrder.TRADE_FINISHED]:
        return  # 判断订单状态是否在　确认签收　和　交易成功　状态　否则　不去做关闭退款单操作
    if refund.created >= fifth_time:  # 30天前的记录才关闭
        return False
    old_status = refund.get_status_display()
    refund.status = SaleRefund.REFUND_CLOSED
    refund.save()  # 注意这里会触发model中的post_save信号
    msg = old_status + '修改为退款关闭状态(定时任务)'
    from core.options import log_action
    log_action(863902, refund, CHANGE, msg)
    # log_action(56, refund, CHANGE, msg)  # 本地
    return True


@task
def task_close_refund(days=None):
    """
    指定时间之前的退款单 状态切换为关闭状态
    """
    if days is None:
        days = 30
    time_point = datetime.datetime.now() - datetime.timedelta(days=days)
    aggree_refunds = SaleRefund.objects.filter(status__in=[SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                                           SaleRefund.REFUND_CLOSED,
                                                           SaleRefund.REFUND_REFUSE_BUYER],
                                               created__lte=time_point,
                                               good_status=SaleRefund.BUYER_RECEIVED)  # 已经发货没有退货的退款单
    res = map(close_refund, aggree_refunds)


