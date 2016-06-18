# -*- encoding:utf-8 -*-
import time
import datetime
import calendar
from django.conf import settings
from django.db import models
from django.db import transaction
from celery.task import task
from celery.task.sets import subtask

from core.options import log_action, ADDITION, CHANGE
from shopback.items.models import ProductSku
from shopback.users.models import User
from shopapp.weixin.models import WeiXinUser, WeixinUnionID
from flashsale.dinghuo.models import OrderList, OrderDetail
from flashsale.pay.models import TradeCharge, SaleTrade, SaleOrder, SaleRefund, Customer,UserAddress
from common.utils import update_model_fields
from .service import FlashSaleService
from .options import get_user_unionid
import logging

import pingpp
pingpp.api_key = settings.PINGPP_APPKEY

__author__ = 'meixqhi'

logger = logging.getLogger('celery.handler')


@task()
def task_Update_Sale_Customer(unionid, openid=None, app_key=None):
    """ 更新特卖用户　微信授权信息 """
    if openid and app_key:
        WeixinUnionID.objects.get_or_create(openid=openid,
                                            app_key=app_key,
                                            unionid=unionid)

    try:
        profile, state = Customer.objects.get_or_create(unionid=unionid)
        wxusers = WeiXinUser.objects.filter(unionid=unionid)
        if wxusers.exists():
            wxuser = wxusers[0]
            # profile.openid = profile.openid or openid or ''
            profile.nick = wxuser.nickname or profile.nick
            profile.mobile = profile.mobile.strip() or wxuser.mobile
            profile.thumbnail = wxuser.headimgurl or profile.thumbnail
            update_model_fields(
                profile,
                update_fields=['nick', 'mobile', 'openid', 'thumbnail'])

    except Exception, exc:
        logger.debug(exc.message, exc_info=True)


@task()
def task_Refresh_Sale_Customer(user_params, app_key=None):
    """ 更新特卖用户　微信授权信息 """
    openid, unionid = user_params.get('openid'), user_params.get('unionid')
    if not unionid:
        return

    if openid and app_key:
        WeixinUnionID.objects.get_or_create(openid=openid,
                                            app_key=app_key,
                                            unionid=unionid)

    try:
        profiles = Customer.objects.filter(unionid=unionid,
                                           status=Customer.NORMAL)
        if not profiles.exists():
            return
        profile = profiles[0]
        wxusers = WeiXinUser.objects.filter(unionid=unionid)
        if not profile.mobile and wxusers.exists():
            profile.mobile = wxusers[0].mobile

        profile.nick = user_params.get('nickname') or profile.nick
        # profile.openid = profile.openid or user_params.get('openid') #not save weixin app auth openid
        profile.thumbnail = user_params.get('headimgurl') or profile.thumbnail
        update_model_fields(profile,
                            update_fields=['nick', 'mobile', 'thumbnail'])

    except Exception, exc:
        logger.debug(exc.message, exc_info=True)


@task()
def task_Merge_Sale_Customer(user, code):
    """ 根据当前登录用户，更新微信授权信息 """

    app_key = settings.WXPAY_APPID
    app_secret = settings.WXPAY_SECRET

    openid, unionid = get_user_unionid(code, appid=app_key, secret=app_secret)
    if not openid or not unionid:
        return

    WeixinUnionID.objects.get_or_create(openid=openid,
                                        app_key=app_key,
                                        unionid=unionid)
    try:
        profile, state = Customer.objects.get_or_create(user=user)
        wxuser = WeiXinUser.objects.get(models.Q(openid=openid) | models.Q(
            unionid=unionid))
        profile.nick = wxuser.nickname
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
                log_action(user.id, strade, CHANGE, u'用户订单转移至:%s' % user.id)
                strade.buyer_id = profile.id
                update_model_fields(strade, update_fields=['buyer_id'])

    except Exception, exc:
        logger.debug(exc.message, exc_info=True)


from shopback.trades.models import MergeTrade, MergeOrder


@task()
def task_Push_SaleTrade_Finished(pre_days=10):
    """
    定时将待确认状态小鹿特卖订单更新成已完成：
    1，查找明细订单对应的MergeOrder;
    2，根据MergeOrder父订单状态更新Saleorder状态；
    3，根据SaleTrade的所有SaleOrder状态更新SaleTrade状态;
    """
    day_date = datetime.datetime.now() - datetime.timedelta(days=pre_days)
    strades = SaleTrade.objects.filter(status__in=(
        SaleTrade.WAIT_SELLER_SEND_GOODS, SaleTrade.WAIT_BUYER_CONFIRM_GOODS,
        SaleTrade.TRADE_BUYER_SIGNED),
                                       pay_time__lte=day_date)
    for strade in strades:
        for sorder in strade.normal_orders:
            if sorder.is_finishable():
                sorder.status = SaleOrder.TRADE_FINISHED
                sorder.save()
        if strade.normal_orders.count() == 0:
            strade.status = SaleTrade.TRADE_CLOSED
            strade.save()

        normal_orders = strade.normal_orders
        finish_orders = strade.sale_orders.filter(
            status=SaleOrder.TRADE_FINISHED)
        if normal_orders.count() == finish_orders.count():
            strade.status = SaleTrade.TRADE_FINISHED
            strade.save()


@task(max_retries=3, default_retry_delay=60)
def confirmTradeChargeTask(sale_trade_id, charge_time=None):
    """ 订单确认付款,并更新状态 """
    strade = SaleTrade.objects.get(id=sale_trade_id)
    strade.charge_confirm(charge_time=charge_time)
    saleservice = FlashSaleService(strade)
    saleservice.payTrade()


@task(max_retries=3, default_retry_delay=60)
@transaction.atomic
def notifyTradePayTask(notify):
    """ 订单确认支付通知消息，如果订单分阶段支付，则在原单ID后追加:[tid]-[数字] """
    try:
        order_no = notify['order_no']
        charge = notify['id']
        paid = notify['paid']

        tcharge, state = TradeCharge.objects.get_or_create(order_no=order_no,
                                                           charge=charge)
        if not paid or tcharge.paid == True:
            return

        update_fields = set(
            ['paid', 'refunded', 'channel', 'amount', 'currency',
             'transaction_no', 'amount_refunded', 'failure_code', 'failure_msg',
             'time_paid', 'time_expire'])

        for k, v in notify.iteritems():
            if k not in update_fields:
                continue
            if k in ('time_paid', 'time_expire'):
                v = v and datetime.datetime.fromtimestamp(v)
            if k in ('failure_code', 'failure_msg'):
                v = v or ''
            hasattr(tcharge, k) and setattr(tcharge, k, v)
        tcharge.save()

        #         order_no_tuple  = order_no.split('-')
        #         is_post_confirm = False
        #         if len(order_no_tuple) > 1:
        #             is_post_confirm = True

        charge_time = tcharge.time_paid
        strade = SaleTrade.objects.get(tid=order_no)
        confirmTradeChargeTask(strade.id, charge_time=charge_time)

    except Exception, exc:
        logger.error('notifyTradePayTask:%s' % exc.message, exc_info=True)
        raise notifyTradePayTask.retry(exc=exc)


from .options import getOrCreateSaleSeller


@task(max_retries=3, default_retry_delay=60)
def notifyTradeRefundTask(notify):
    try:
        refund_id = notify['id']
        seller = getOrCreateSaleSeller()
        srefund = SaleRefund.objects.get(refund_id=refund_id)

        log_action(seller.user.id, srefund, CHANGE, u'%s(金额:%s)' %
                   ([u'退款失败', u'退款成功'][notify['succeed'] and 1 or 0],notify['amount']))
        if not notify['succeed']:
            srefund.feedback += notify.get('failure_msg', '') or ''
            srefund.save()
            logger.warn('refund fail:%s' % notify)
            return
        srefund.refund_confirm()
        strade = SaleTrade.objects.get(id=srefund.trade_id)
        if strade.is_Deposite_Order():
            return
        saleservice = FlashSaleService(strade)
        saleservice.payTrade()
    except Exception, exc:
        logger.error('notifyTradeRefundTask：%s' % exc.message, exc_info=True)
        raise notifyTradeRefundTask.retry(exc=exc)


@task(max_retries=3, default_retry_delay=30)
def pushTradeRefundTask(refund_id):
    """ 发货前申请,　检查是否极速退款 """
    try:
        sale_refund = SaleRefund.objects.get(id=refund_id)
        trade_id = sale_refund.trade_id

        strade = SaleTrade.objects.get(id=trade_id)
        saleservice = FlashSaleService(strade)
        saleservice.payTrade()
        from shopback.refunds.models import Refund

        seller = getOrCreateSaleSeller()
        sorder = SaleOrder.objects.get(id=sale_refund.order_id)
        refund, state = Refund.objects.get_or_create(id=refund_id,
                                                     tid=strade.tid,
                                                     oid=sorder.oid)
        refund.user = seller
        refund.title = sorder.title
        refund.payment = sale_refund.payment
        refund.buyer_nick = strade.buyer_nick or strade.receiver_name
        refund.mobile = strade.receiver_mobile
        if sale_refund.has_good_return:
            refund.status = Refund.REFUND_WAIT_RETURN_GOODS
            refund.has_good_return = sale_refund.has_good_return
        else:
            refund.status = Refund.REFUND_WAIT_SELLER_AGREE
        refund.save()

        if not sale_refund.is_postrefund():
            if sale_refund.is_fastrefund():
                sale_refund.refund_fast_approve()
            else:
                sale_refund.refund_charge_approve()
    except Exception, exc:
        logger.error('pushTradeRefundTask：%s'%exc.message, exc_info=True)
        raise pushTradeRefundTask.retry(exc=exc)


@task
def pull_Paid_SaleTrade(pre_day=1, interval=1):
    """ pre_day:表示从几天前开始；interval:表示从pre_day开始更新多少天的数据 """
    target = datetime.datetime.now() - datetime.timedelta(days=pre_day)
    pre_date = datetime.datetime(target.year, target.month, target.day)
    post_date = pre_date + datetime.timedelta(days=interval)
    page_size = 50
    has_next = True
    starting_after = None
    while has_next:
        if starting_after:
            resp = pingpp.Charge.all(limit=page_size,
                                     created={'gte': pre_date,
                                              'lte': post_date},
                                     starting_after=starting_after)
        else:
            resp = pingpp.Charge.all(limit=page_size,
                                     created={'gte': pre_date,
                                              'lte': post_date})
        e = None
        for e in resp['data']:
            # notifyTradePayTask.s(e)()
            try:
                notifyTradePayTask(e)
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
        if e:
            starting_after = e['id']
        has_next = resp['has_more']
        if not has_next:
            break


@task
def push_SaleTrade_To_MergeTrade():
    """ 更新特卖订单到订单列表 """

    saletrades = SaleTrade.objects.filter(
        status=SaleTrade.WAIT_SELLER_SEND_GOODS)
    for strade in saletrades:
        mtrades = MergeTrade.objects.filter(tid=strade.tid,
                                            type=MergeTrade.SALE_TYPE)
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
    page_size = 100
    has_next = True
    starting_after = None
    while has_next:
        if starting_after:
            resp = pingpp.RedEnvelope.all(limit=page_size,
                                          created={'gte': pre_date,
                                                   'lte': today},
                                          starting_after=starting_after)
        else:
            resp = pingpp.RedEnvelope.all(limit=page_size,
                                          created={'gte': pre_date,
                                                   'lte': today})
        e = None
        for e in resp['data']:
            envelop = Envelop.objects.get(id=e['order_no'])
            envelop.handle_envelop(e)
        if e:
            starting_after = e['id']

        has_next = resp['has_more']
        if not has_next:
            break


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
    weixin_user = WeixinUnionID.objects.filter(app_key=WXPAY_APPID,
                                               unionid=instance.unionid)
    openid = ''
    if weixin_user.exists():
        openid = weixin_user[0].openid
    mobile = instance.mobile
    downloads = AppDownloadRecord.objects.filter(Q(openid=openid) | Q(
        mobile=mobile)).filter(status=False)  # 没有成为用户的记录
    if downloads.exists():
        download = downloads[0]
        # 存在记录则计算当前用户到下载记录的妈妈粉丝上
        from_customer = Customer.objects.get(pk=download.from_customer)
        if not from_customer:  # 没有找到推荐人则返回
            return
        ins_xlmm = instance.getXiaolumm()
        if ins_xlmm:  # 如果当前用户是小鹿妈妈则返回，不记录小鹿妈妈自己为自己的粉丝
            return
        fans = XlmmFans.objects.filter(xlmm_cusid=from_customer.id,
                                       fans_cusid=instance.id)
        if fans.exists():  # 存在粉丝记录返回
            return
        else:
            XlmmFans.objects.createFansRecord(
                str(from_customer.id), str(instance.id))
            download.status = True
            download.save()


from flashsale.pay.models_user import BudgetLog, UserBudget
from django.db.models import Sum


@task(max_retries=3, default_retry_delay=6)
def task_budgetlog_update_userbudget(budget_log):
    customer_id = budget_log.customer_id
    bglogs = BudgetLog.objects.filter(customer_id=customer_id,
                                      status__in=[BudgetLog.CONFIRMED, BudgetLog.PENDING])
    records = bglogs.values('budget_type', 'status').annotate(total=Sum('flow_amount'))
    in_amount, out_amount = 0, 0
    for entry in records:
        if entry["budget_type"] == BudgetLog.BUDGET_IN and entry['status'] == BudgetLog.CONFIRMED:
            in_amount += entry["total"]
        if entry["budget_type"] == BudgetLog.BUDGET_OUT and entry['status'] == BudgetLog.CONFIRMED:
            out_amount += entry["total"]
    cash = in_amount - out_amount
    customers = Customer.objects.filter(id=customer_id)
    try:
        if not customers.exists():
            logger.warn('customer %s　not exists when create user budget!' %
                        customer_id)
        budgets = UserBudget.objects.filter(user=customer_id)
        if not budgets.exists():
            budget = UserBudget(user=customers[0],
                                amount=cash,
                                total_income=in_amount,
                                total_expense=out_amount)
            budget.save()
        else:
            budget = budgets[0]
            if budget.amount != cash:
                budget.amount = cash
            budget.total_income = in_amount
            budget.total_expense = out_amount
            budget.save()
    except Exception, exc:
        raise task_budgetlog_update_userbudget.retry(exc=exc)


from extrafunc.renewremind.tasks import send_message
from shopapp.smsmgr.models import SMSActivity
from django.contrib.admin.models import CHANGE


def make_refund_message(refund):
    """ 根据短信模板生成要发送或者推送的文本信息 """
    sms_activitys = SMSActivity.objects.none()
    refund_status = refund.status
    active_sms = SMSActivity.objects.filter(id__gte=5, id__lte=8)
    if refund_status == SaleRefund.REFUND_WAIT_RETURN_GOODS:  # 同意申请退货
        sms_activitys = active_sms.filter(id=5, status=True)

    if refund_status == SaleRefund.REFUND_REFUSE_BUYER:  # 拒绝申请退款
        sms_activitys = active_sms.filter(id=6, status=True)

    if refund_status == SaleRefund.REFUND_APPROVE:  # 等待返款
        sms_activitys = active_sms.filter(id=7, status=True)

    if refund_status == SaleRefund.REFUND_SUCCESS:  # 退款成功
        sms_activitys = active_sms.filter(id=8, status=True)

    if sms_activitys.exists():
        sms_activity = sms_activitys[0]
        message = sms_activity.text_tmpl.format(
            refund.title,  # 标题
            refund.refund_fee,  # 退款费用
            refund.get_status_display())  # 退款状态
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
        send_message(mobile=mobile,
                     message=message,
                     taskName=refund.get_status_display())


from flashsale.push.push_refund import push_refund_app_msg


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


from flashsale.push.push_usercoupon import user_coupon_release_push


@task
def task_release_coupon_push(customer_id):
    """ 特卖用户领取红包 """
    user_coupon_release_push(customer_id)
    return


from core.options import get_systemoa_user


def close_refund(refund):
    """ 关闭退款单 """

    order = SaleOrder.objects.get(id=refund.order_id)
    if order.status not in [SaleOrder.TRADE_BUYER_SIGNED,
                            SaleOrder.TRADE_FINISHED]:
        return  # 判断订单状态是否在　确认签收　和　交易成功　状态　否则　不去做关闭退款单操作

    old_status = refund.get_status_display()
    refund.status = SaleRefund.REFUND_CLOSED
    refund.save()  # 注意这里会触发model中的post_save信号

    from core.options import log_action
    msg = old_status + '修改为退款关闭状态(定时任务)'
    log_action(get_systemoa_user().id, refund, CHANGE, msg)
    # log_action(56, refund, CHANGE, msg)  # 本地
    return True


def close_15_refund(refund):
    """ 2016-5-4  提取 十五天之前 同意申请状态的退货单  如果交易 确认签收 交易完成 或者已经发货  关闭该退货单 """

    if refund.status != SaleRefund.REFUND_WAIT_RETURN_GOODS:
        return
    order = SaleOrder.objects.get(id=refund.order_id)
    if order.status not in [SaleOrder.TRADE_BUYER_SIGNED,
                            SaleOrder.TRADE_FINISHED,
                            SaleOrder.WAIT_BUYER_CONFIRM_GOODS]:
        return  # 判断订单状态是否在　确认签收　和　交易成功　已发货 状态　否则　不去做关闭退款单操作

    old_status = refund.get_status_display()
    refund.status = SaleRefund.REFUND_CLOSED
    refund.save()  # 注意这里会触发model中的post_save信号

    from core.options import log_action
    msg = old_status + '修改为退款关闭状态(定时任务)'
    log_action(get_systemoa_user().id, refund, CHANGE, msg)
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
    aggree_refunds = SaleRefund.objects.filter(
        status__in=[SaleRefund.NO_REFUND, SaleRefund.REFUND_WAIT_SELLER_AGREE,
                    SaleRefund.REFUND_WAIT_RETURN_GOODS,
                    SaleRefund.REFUND_REFUSE_BUYER],
        created__lte=time_point)  # 这里不考虑退货状态
    # good_status=SaleRefund.BUYER_RECEIVED)  # 已经发货没有退货的退款单
    res = map(close_refund, aggree_refunds)

    # 2016-5-4  提取 十五天之前 同意申请状态的退货单  如果交易 确认签收 交易完成 或者已经发货  关闭该退货单
    fifth_days_ago = datetime.datetime.now() - datetime.timedelta(days=15)
    refunds = SaleRefund.objects.filter(
        status=SaleRefund.REFUND_WAIT_RETURN_GOODS,
        created__lte=fifth_days_ago)  # 这里不考虑退货状态
    res = map(close_15_refund, refunds)


@task
def task_saleorder_update_package_sku_item(sale_order):
    from shopback.trades.models import PackageSkuItem
    from shopback.items.models import ProductSku
    items = PackageSkuItem.objects.filter(sale_order_id=sale_order.id)
    if items.count() <= 0:
        if not sale_order.is_pending():
            # we create PackageSkuItem only if sale_order is 'pending'.
            return
        ware_by = ProductSku.objects.get(id=sale_order.sku_id).ware_by
        sku_item = PackageSkuItem(sale_order_id=sale_order.id, ware_by=ware_by)
        attrs = ['num', 'oid', 'package_order_id', 'title', 'price', 'sku_id',
                 'num', 'total_fee', 'payment', 'discount_fee', 'refund_status',
                 'pay_time', 'status', 'pic_path']
        for attr in attrs:
            if hasattr(sale_order, attr):
                val = getattr(sale_order, attr)
                setattr(sku_item, attr, val)
        sku_item.outer_sku_id = sku_item.product_sku.outer_id
        sku_item.outer_id = sku_item.product_sku.product.outer_id

        sku_item.receiver_mobile = sale_order.sale_trade.receiver_mobile
        sku_item.sale_trade_id = sale_order.sale_trade.tid
        sku_item.sku_properties_name = sale_order.sku_name
        sku_item.save()
        return

    sku_item = items[0]
    if sku_item.is_finished():
        # if it's finished, that means the package is sent out,
        # then we dont do further updates, simply return.
        return

    # Now the sku_item has not been sent out yet, it can only stay in 3 states:
    # 1) CANCELED; 2) NOT_ASSIGNED; 3) ASSIGNED
    # And, sale_order can only have 3 states: cancel, confirmed, pending.
    if sale_order.is_canceled() or sale_order.is_confirmed():
        # If saleorder is canceled or confirmed before we send out package, we
        # then dont want to send out the package, simply cancel. Note: if the
        # order is confirmed, we assume the customer does not want the package
        # to be sent to him (most likely because it's not necessary, maybe she/he
        # bought a virtual product).
        assign_status = PackageSkuItem.CANCELED
    elif sale_order.is_pending():
        assign_status = PackageSkuItem.NOT_ASSIGNED

    if sku_item.assign_status != assign_status:
        sku_item.assign_status = assign_status
        sku_item.set_assign_status_time()
        sku_item.save()


@task()
def tasks_set_user_address_id(sale_trade):
    ua, state = UserAddress.objects.get_or_create(
        cus_uid=sale_trade.buyer_id,
        receiver_name=sale_trade.receiver_name,
        receiver_state=sale_trade.receiver_state,
        receiver_city=sale_trade.receiver_city,
        receiver_district=sale_trade.receiver_district,
        receiver_address=sale_trade.receiver_address,
        receiver_zip=sale_trade.receiver_zip,
        receiver_mobile=sale_trade.receiver_mobile,
        receiver_phone=sale_trade.receiver_phone)
    if ua.status != 'normal':
        ua.status = 'normal'
        ua.save()
    SaleTrade.objects.filter(id=sale_trade.id).update(user_address_id=ua.id)

@task()
def tasks_set_address_priority_logistics_code(address_id, logistics_company_id):

    from shopback.logistics.models import LogisticsCompany
    user_address = UserAddress.objects.filter(id=address_id).first()
    logistics_company = LogisticsCompany.objects.filter(id=logistics_company_id).first()
    if not user_address or not logistics_company:
        logger.warn('not update address logistics_code:address_id=%s, logistics_company=%s'%(address_id, logistics_company_id))
        return
    user_address.set_logistic_company(logistics_company.code)



@task()
def tasks_update_sale_trade_status(sale_trade_id):
    logger.warn('tasks_update_sale_trade_status check:' + str(sale_trade_id))
    sale_order_status = [s['status']
                         for s in SaleOrder.objects.filter(
                             sale_trade_id=sale_trade_id).values('status')]
    sale_order_status = list(set(sale_order_status))
    if SaleOrder.WAIT_SELLER_SEND_GOODS not in sale_order_status and (SaleOrder.WAIT_BUYER_CONFIRM_GOODS in sale_order_status\
            or SaleOrder.TRADE_BUYER_SIGNED in sale_order_status or SaleOrder.TRADE_FINISHED in sale_order_status):
        logger.warn('tasks_update_sale_trade_status right now:' + str(sale_trade_id))
        SaleTrade.objects.filter(id=sale_trade_id).update(status=SaleTrade.WAIT_BUYER_CONFIRM_GOODS)


@task()
def task_update_orderlist(sku_id):
    orderdetail = OrderDetail.objects.select_related('orderlist')\
      .filter(chichu_id=sku_id).exclude(orderlist__status=OrderList.ZUOFEI).order_by('-id').first()
    if not orderdetail:
        return

    sale_stats = SaleOrder.objects.filter(
        sku_id=sku_id,
        status=SaleOrder.WAIT_SELLER_SEND_GOODS,
        refund_status__lte=SaleRefund.REFUND_REFUSE_BUYER,
        pay_time__gt=datetime.datetime(2016, 4, 1)).exclude(
            outer_id__startswith='RMB').values('sku_id').annotate(
                sale_quantity=Sum('num'))

    if not sale_stats:
        sale_quantity = 0
    else:
        sale_quantity = sale_stats[0]['sale_quantity']

    if sale_quantity == orderdetail.buy_quantity:
        return

    orderlist = orderdetail.orderlist
    sku = ProductSku.objects.select_related('product').get(id=int(sku_id))
    now = datetime.datetime.now()
    buy_quantity = orderdetail.buy_quantity
    delta = buy_quantity - sale_quantity

    if orderlist.status == OrderList.SUBMITTING:
        orderdetail.buy_quantity = sale_quantity
        orderdetail.save()
        log_action(1, orderdetail, CHANGE, u'更新产品数量至%d(原%d)' % (sale_quantity,  buy_quantity))
        if delta:
            msg = '%s %s多拍%d件, 数量更新至%d(原%d)' % \
              (sku.product.name, sku.properties_name or sku.properties_alias, abs(delta), sale_quantity, buy_quantity)
        else:
            msg = '%s %s少拍%d件, 数量更新至%d(原%d)' % \
              (sku.product.name, sku.properties_name or sku.properties_alias, abs(delta), sale_quantity, buy_quantity)
        orderlist.note += '\n-->%s: %s' % (now.strftime('%m月%d %H:%M'), msg)

        n = 0
        amount = .0
        for orderdetail in orderlist.order_list.all():
            n += orderdetail.buy_quantity
            amount += float(orderdetail.buy_unitprice) * orderdetail.buy_quantity
        orderlist.order_amount = amount
        orderlist.save()
        if n <= 0:
            orderlist.note += '\n-->%s: 作废' % now.strftime('%m月%d %H:%M')
            orderlist.status = OrderList.ZUOFEI
            log_action(1, orderlist, CHANGE, u'作废')
            orderlist.save()
    else:
        if delta:
            msg = '%s %s多拍%d件, 待发货数现%d(原%d)' % \
              (sku.product.name, sku.properties_name or sku.properties_alias, abs(delta), sale_quantity, buy_quantity)
        else:
            msg = '%s %s少拍%d件, 待发货数现%d(原%d)' % \
              (sku.product.name, sku.properties_name or sku.properties_alias, abs(delta), sale_quantity, buy_quantity)
        orderlist.note += '\n-->%s: %s' % (now.strftime('%m月%d %H:%M'), msg)
        orderlist.save()
