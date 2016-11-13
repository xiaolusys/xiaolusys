# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
import re
import datetime
import logging

from celery import shared_task as task
from django.conf import settings
from django.db import models
from django.db import transaction

from common.utils import update_model_fields
from core.options import log_action
from flashsale.dinghuo.models import OrderList, OrderDetail
from flashsale.pay.models import CustomerShops, CuShopPros
from flashsale.pay.models import TradeCharge, SaleTrade, SaleOrder, SaleRefund, Customer,UserAddress, TeamBuy
from flashsale.pay.models.score import IntegralLog, Integral
from shopapp.weixin.models import WeiXinUser
from shopback.items.models import ProductSku
from .options import get_user_unionid
from .services import FlashSaleService

import pingpp
pingpp.api_key = settings.PINGPP_APPKEY

__author__ = 'meixqhi'
logger = logging.getLogger(__name__)


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


from shopback.trades.models import MergeTrade


@task()
def task_Push_SaleTrade_Finished(pre_days=10):
    """
    定时将待确认状态小鹿特卖订单更新成已完成：
    1，查找明细订单对应的MergeOrder;
    2，根据MergeOrder父订单状态更新Saleorder状态；
    3，根据SaleTrade的所有SaleOrder状态更新SaleTrade状态;
    """
    day_date = datetime.datetime.now() - datetime.timedelta(days=pre_days)
    sorders = SaleOrder.objects.filter(status__in=(
        SaleOrder.WAIT_BUYER_CONFIRM_GOODS, SaleOrder.TRADE_BUYER_SIGNED),
        pay_time__lte=day_date).select_related('sale_trade')
    for sorder in sorders:
        strade = sorder.sale_trade
        if sorder.is_finishable():
            sorder.status = SaleOrder.TRADE_FINISHED
            sorder.save(update_fields=['status'])

        normal_num = strade.normal_orders.count()
        if normal_num == 0:
            strade.status = SaleTrade.TRADE_CLOSED
            strade.save(update_fields=['status'])

        finish_orders = strade.sale_orders.filter(
            status=SaleOrder.TRADE_FINISHED)
        if normal_num == finish_orders.count():
            strade.status = SaleTrade.TRADE_FINISHED
            strade.save(update_fields=['status'])


@task(max_retries=3, default_retry_delay=60)
def confirmTradeChargeTask(sale_trade_id, charge_time=None, charge=None):
    """ 订单确认付款,并更新状态 """
    strade = SaleTrade.objects.get(id=sale_trade_id)
    strade.charge_confirm(charge_time=charge_time, charge=charge)
    saleservice = FlashSaleService(strade)
    saleservice.payTrade()


@task(max_retries=3, default_retry_delay=60)
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

        update_fields = set([
            'paid', 'refunded', 'channel', 'amount', 'currency',
            'transaction_no', 'amount_refunded', 'failure_code', 'failure_msg',
            'time_paid', 'time_expire'
        ])

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
        confirmTradeChargeTask(strade.id, charge_time=charge_time, charge=tcharge.charge)

    except Exception, exc:
        raise notifyTradePayTask.retry(exc=exc)


from .options import getOrCreateSaleSeller


@task(max_retries=3, default_retry_delay=60)
def notifyTradeRefundTask(notify):
    try:
        refund_id = notify['id']
        seller = getOrCreateSaleSeller()
        srefund = SaleRefund.objects.filter(refund_id=refund_id).first()
        if not srefund:
            logger.error('pingpp refund order notfound:%s'%notify)
            order_id = re.compile('oid:(?P<order_id>\d+)').search(srefund['description']).groupdict().get('order_id')
            saleorder = SaleOrder.objects.filter(id=order_id).first()
            if saleorder:
                srefund = SaleRefund.objects.filter(trade_id=saleorder.sale_trade.id,order_id=saleorder.id).first()

        if not srefund:
            return

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
        raise notifyTradeRefundTask.retry(exc=exc)


@task(max_retries=3, default_retry_delay=30)
def pushTradeRefundTask(refund_id):
    """ 发货前申请,　检查是否极速退款 """
    try:
        from shopback.refunds.models import Refund
        from shopback.warehouse.constants import WARE_THIRD
        from shopback.trades.models import PackageSkuItem

        salerefund = SaleRefund.objects.get(id=refund_id)
        trade_id = salerefund.trade_id

        strade = SaleTrade.objects.get(id=trade_id)
        saleservice = FlashSaleService(strade)
        saleservice.payTrade()

        seller = getOrCreateSaleSeller()
        sorder = SaleOrder.objects.get(id=salerefund.order_id)
        refund, state = Refund.objects.get_or_create(id=refund_id,
                                                     tid=strade.tid,
                                                     oid=sorder.oid)
        refund.user = seller
        refund.title = sorder.title
        refund.payment = salerefund.payment
        refund.buyer_nick = strade.buyer_nick or strade.receiver_name
        refund.mobile = strade.receiver_mobile
        if salerefund.has_good_return:
            refund.status = Refund.REFUND_WAIT_RETURN_GOODS
            refund.has_good_return = salerefund.has_good_return
        else:
            refund.status = Refund.REFUND_WAIT_SELLER_AGREE
        refund.save()
        # 不是发货后退款
        if not salerefund.is_postrefund:  # and not salerefund.saleorder.product.ware_by == WARE_THIRD: # 第三方仓库
            psi = PackageSkuItem.objects.filter(oid=sorder.oid).first()
            if psi and psi.is_booked():  # 已经订货 不做退款操作
                return
            salerefund.refund_approve()  # 退款给用户
    except Exception, exc:
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
        logger.info('pingpp-charge-resp: starting_after=%s, count=%s' %(starting_after, len(resp['data'])))
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


@task(max_retries=3, default_retry_delay=10)
def task_handle_envelope_notify(notify):
    try:
        envelop = Envelop.objects.get(id=notify['order_no'])
        envelop.handle_envelop(notify)
    except Exception, exc:
        raise task_handle_envelope_notify.retry(exc=exc)


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
            task_handle_envelope_notify(e)
        if e:
            starting_after = e['id']

        has_next = resp['has_more']
        if not has_next:
            break


from django.db.models import Q
from flashsale.xiaolumm.models.models_fans import XlmmFans
from flashsale.promotion.models import AppDownloadRecord
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
        fans = XlmmFans.objects.filter(fans_cusid=instance.id)
        if fans.exists():  # 存在粉丝记录返回
            return
        else:
            XlmmFans.objects.createFansRecord(
                str(from_customer.id), str(instance.id))
            download.status = True
            download.save()


from flashsale.pay.models import BudgetLog, UserBudget
from django.db.models import Sum

@task(max_retries=3, default_retry_delay=6)
def task_budgetlog_update_userbudget(budget_log):
    customer_id = budget_log.customer_id
    bglogs = BudgetLog.objects.filter(customer_id=customer_id).exclude(status=BudgetLog.CANCELED)
    records = bglogs.values('budget_type', 'status').annotate(total=Sum('flow_amount'))
    in_amount, out_amount = 0, 0
    for entry in records:
        if entry["budget_type"] == BudgetLog.BUDGET_IN and entry["status"] == BudgetLog.CONFIRMED:
            # 收入只计算confirmed
            in_amount += entry["total"]
        if entry["budget_type"] == BudgetLog.BUDGET_OUT:
            # 只出计算confirmed+pending
            out_amount += entry["total"]
    cash = in_amount - out_amount
    customers = Customer.objects.normal_customer.filter(id=customer_id)
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


from games.renewremind.tasks import send_message
from shopapp.smsmgr.models import SMSActivity
from django.contrib.admin.models import CHANGE


def make_refund_message(refund):
    """ 根据短信模板生成要发送或者推送的文本信息 """
    refund_status = refund.status
    active_sms = SMSActivity.objects.filter(id__gte=5, id__lte=8)
    status_tpl_map = {
        SaleRefund.REFUND_WAIT_RETURN_GOODS: 5,  # 同意申请退货
        SaleRefund.REFUND_REFUSE_BUYER: 6,  # 拒绝申请退款
        SaleRefund.REFUND_APPROVE: 7,  # 等待返款
        SaleRefund.REFUND_SUCCESS: 8  # 退款成功
    }
    try:
        tpl_id = status_tpl_map[refund_status]
    except KeyError as e:
        return
    sms_activity = active_sms.filter(id=tpl_id, status=True).first()

    status_display = refund.get_status_display()
    if tpl_id == 5:  # 同意退货的时候添加地址信息
        address = refund.get_return_address()
        status_display = ' '.join([status_display, u'退回地址:', address])
    message = sms_activity.text_tmpl.format(refund.title,  # 标题
                                            refund.refund_fee,  # 退款费用
                                            status_display)  # 退款状态
    return message


def send_refund_msg(refund):
    """ 发送同意退款信息 """
    customer = refund.customer
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
    user_coupon_release_push(customer_id, push_tpl_id=9)
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
@transaction.atomic
def task_saleorder_update_package_sku_item(sale_order):
    from shopback.trades.models import PackageSkuItem
    from shopback.items.models import ProductSku, SkuStock
    items = PackageSkuItem.objects.filter(sale_order_id=sale_order.id)
    if items.count() <= 0:
        if not sale_order.is_pending():
            # we create PackageSkuItem only if sale_order is 'pending'.
            return
        ware_by = ProductSku.objects.get(id=sale_order.sku_id).ware_by
        sku_item = PackageSkuItem(sale_order_id=sale_order.id, ware_by=ware_by)
        attrs = ['num', 'oid', 'package_order_id', 'title', 'price', 'sku_id',
                 'total_fee', 'payment', 'discount_fee', 'refund_status',
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
        stat = SkuStock.get_by_sku(sku_item.sku_id)
        assign_status = 1 if stat.realtime_quantity - stat.assign_num >= sku_item.num else 0
        sku_item.assign_status = assign_status
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
        if not sku_item.is_finished() and sku_item.assign_status != PackageSkuItem.CANCELED:
            sku_item.assign_status = PackageSkuItem.CANCELED
            sku_item.set_assign_status_time()
            sku_item.save()
    elif sale_order.is_pending():
        if sku_item.assign_status == PackageSkuItem.CANCELED:
            sku_item.assign_status = PackageSkuItem.NOT_ASSIGNED
            sku_item.clear_order_info()


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
    # logger.warn('tasks_update_sale_trade_status check:' + str(sale_trade_id))
    sale_order_status = [s['status']
                         for s in SaleOrder.objects.filter(
                             sale_trade_id=sale_trade_id).values('status')]
    sale_order_status = list(set(sale_order_status))
    # if SaleOrder.WAIT_SELLER_SEND_GOODS not in sale_order_status and (SaleOrder.WAIT_BUYER_CONFIRM_GOODS in sale_order_status\
    #         or SaleOrder.TRADE_BUYER_SIGNED in sale_order_status or SaleOrder.TRADE_FINISHED in sale_order_status):
    #     logger.warn('tasks_update_sale_trade_status right now:' + str(sale_trade_id))
    #     SaleTrade.objects.filter(id=sale_trade_id).update(status=SaleTrade.WAIT_BUYER_CONFIRM_GOODS)

    #新的逻辑如下,n个saleorder如何影响saletrade状态，付款后已支付》已发货》确认签收》退款关闭》交易成功》交易关闭。
    # 即如果还有1个saleorder处于已支付状态，那么saletrade就是已支付状态；其它状态类似。

    if SaleOrder.WAIT_SELLER_SEND_GOODS in sale_order_status:
        logger.warn('tasks_update_sale_trade_status right now:%s %s' % (sale_trade_id, SaleTrade.WAIT_SELLER_SEND_GOODS))
        SaleTrade.objects.filter(id=sale_trade_id).update(status=SaleTrade.WAIT_SELLER_SEND_GOODS)
    elif SaleOrder.WAIT_BUYER_CONFIRM_GOODS in sale_order_status:
        logger.warn(
            'tasks_update_sale_trade_status right now:%s %s' % (sale_trade_id, SaleTrade.WAIT_BUYER_CONFIRM_GOODS))
        SaleTrade.objects.filter(id=sale_trade_id).update(status=SaleTrade.WAIT_BUYER_CONFIRM_GOODS)
    elif SaleOrder.TRADE_BUYER_SIGNED in sale_order_status:
        logger.warn(
            'tasks_update_sale_trade_status right now:%s %s' % (sale_trade_id, SaleTrade.TRADE_BUYER_SIGNED))
        SaleTrade.objects.filter(id=sale_trade_id).update(status=SaleTrade.TRADE_BUYER_SIGNED)
    elif SaleOrder.TRADE_CLOSED in sale_order_status:
        logger.warn(
            'tasks_update_sale_trade_status right now:%s %s' % (sale_trade_id, SaleTrade.TRADE_CLOSED))
        SaleTrade.objects.filter(id=sale_trade_id).update(status=SaleTrade.TRADE_CLOSED)
    elif SaleOrder.TRADE_FINISHED in sale_order_status:
        all_finish = True
        for status in sale_order_status:
            if status != SaleOrder.TRADE_FINISHED:
                all_finish = False
                break
        if all_finish:
            logger.warn(
                'tasks_update_sale_trade_status right now:%s %s' % (sale_trade_id, SaleTrade.TRADE_FINISHED))
            SaleTrade.objects.filter(id=sale_trade_id).update(status=SaleTrade.TRADE_FINISHED)


@task()
def task_customer_update_weixinuserinfo(customer):
    if not customer.unionid:
        return

    from shopapp.weixin.models_base import WeixinUserInfo
    info = WeixinUserInfo.objects.filter(unionid=customer.unionid).first()
    if not info:
        info = WeixinUserInfo(unionid=customer.unionid,nick=customer.nick,thumbnail=customer.thumbnail)
        info.save()


@task()
def task_sync_xlmm_fans_nick_thumbnail(customer):
    """ 更新小鹿妈妈粉丝的头像和昵称 """
    from flashsale.xiaolumm.models import XlmmFans
    fans = XlmmFans.objects.filter(fans_cusid=customer.id).first()
    if not fans:
        return
    fans.update_nick_thumbnail(customer.nick, customer.thumbnail)


@task()
def task_sync_xlmm_mobile_by_customer(customer):
    """ 更新小鹿妈妈的手机号 """
    xlmm = customer.get_xiaolumm()
    if not xlmm:
        return
    mobile = customer.mobile if customer.mobile else ''
    xlmm.update_mobile(mobile.strip())


@task()
def task_add_product_to_customer_shop(customer):
    """
    为代理用户店铺添加　推送中的商品
    """
    if not customer:
        return
    xlmm = customer.getXiaolumm()
    if not xlmm:
        return
    from supplychain.supplier.models import SaleProductManageDetail
    from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
    from shopback.items.models import Product
    rebt = AgencyOrderRebetaScheme.objects.get(status=AgencyOrderRebetaScheme.NORMAL, is_default=True)
    today_date = datetime.date.today()
    shop = CustomerShops.objects.filter(customer=customer.id).first()
    if not shop:
        return
    # 当天推广的选品
    pms = SaleProductManageDetail.objects.filter(schedule_manage__sale_time=today_date,
                                                 is_promotion=True)
    for pm in pms:
        # 当天上架的　对应选品的商品
        pro = Product.objects.filter(sale_time=today_date,
                                     status=Product.NORMAL,
                                     sale_product=pm.sale_product_id,
                                     shelf_status=Product.UP_SHELF).first()  # 仅　添加一个产品
        if not pro:
            continue
        kwargs = {'agencylevel': xlmm.agencylevel,
                  'product_price_yuan': float(pro.agent_price)} if xlmm and pro.agent_price else {}
        rebet_amount = rebt.calculate_carry(**kwargs) if kwargs else 0  # 计算佣金
        cu_shop_prods = CuShopPros.objects.filter(customer=shop.customer)
        cu_shop_prod = cu_shop_prods.filter(product=pro.id).first()  # 该用户该产品
        if not cu_shop_prod:
            position = cu_shop_prods.count() + 1    # 位置加1
            cu_pro = CuShopPros(shop=shop.id,
                                customer=shop.customer,
                                product=pro.id,
                                model=pro.model_id,
                                name=pro.name,
                                pic_path=pro.pic_path,
                                std_sale_price=pro.std_sale_price,
                                agent_price=pro.agent_price,
                                remain_num=pro.remain_num,
                                carry_scheme=rebt.id,
                                carry_amount=rebet_amount,
                                position=position,
                                pro_category=pro.category.cid,
                                offshelf_time=pro.offshelf_time)
            cu_pro.save()


@task()
def task_add_user_order_integral(sale_order):
    """
    :arg sale_order : SaleOrder instance
    add user integral by sale_order
    """
    if sale_order.is_deposit():  # 代理费(虚拟商品)不需要生成积分
        return
    if sale_order.status < SaleOrder.WAIT_SELLER_SEND_GOODS or sale_order.status > SaleOrder.TRADE_CLOSED:
        # 订单状态小于已经付款　　大于　退款关闭　不添加积分
        return
    order_id = sale_order.id
    pic_link = sale_order.pic_path
    trade_id = sale_order.sale_trade_id
    order_status = sale_order.status
    order_content = {
        "order_id": str(order_id),
        "pic_link": str(pic_link),
        "trade_id": str(trade_id),
        "order_status": str(order_status)
    }
    trade = SaleTrade.objects.get(id=sale_order.sale_trade_id)  # 由订单找交易
    cus = Customer.objects.get(id=trade.buyer_id)  # 由交易的buyer_id找
    buyer_id = trade.buyer_id  # 用户ID
    integral_log = IntegralLog.objects.filter(integral_user=buyer_id,
                                              in_out=IntegralLog.LOG_IN,
                                              order_id=sale_order.id).first()

    if sale_order.status in (SaleOrder.WAIT_SELLER_SEND_GOODS,
                             SaleOrder.WAIT_BUYER_CONFIRM_GOODS,
                             SaleOrder.TRADE_BUYER_SIGNED,
                             SaleOrder.TRADE_FINISHED):  # 已经付款　已经发货　确认签收　交易成功
        if integral_log:
            if sale_order.status == SaleOrder.TRADE_FINISHED:  # 交易成功　积分确定
                integral_log.log_status = IntegralLog.CONFIRM
                integral_log.save(update_fields=['log_status'])
        else:  # 还没有积分记录
            integral_log = IntegralLog(integral_user=buyer_id,
                                       order_id=sale_order.id,
                                       mobile=cus.mobile,
                                       log_value=int(sale_order.payment),
                                       order=order_content,
                                       log_status=IntegralLog.PENDING,
                                       log_type=IntegralLog.ORDER_INTEGRA,
                                       in_out=IntegralLog.LOG_IN)
            integral_log.save()
    elif sale_order.status == SaleOrder.TRADE_CLOSED:  # 退款关闭的 积分要取消掉
        if integral_log:
            integral_log.log_status = IntegralLog.CANCEL  # 取消积分
            integral_log.save(update_fields=['log_status'])


@task()
def task_calculate_total_order_integral(integral_log):
    """
    :arg integral_log IntegralLog instance
    calculate the IntegralLog user total point
    """
    user = integral_log.integral_user
    logs = IntegralLog.objects.filter(integral_user=user, log_status=IntegralLog.CONFIRM)
    in_out = logs.values('in_out').annotate(t_log_value=Sum('log_value'))
    total_point = 0
    for d in in_out:
        if d['in_out'] == IntegralLog.LOG_IN:
            total_point = total_point + d['t_log_value']
        elif d['in_out'] == IntegralLog.LOG_OUT:
            total_point = total_point - d['t_log_value']
    user_intergral = Integral.objects.filter(integral_user=user).first()
    if user_intergral:
        user_intergral.update_integral_value(total_point)
        return
    Integral.create_integral(customer_id=user, integral_value=total_point)


@task()
def task_tongji_trade_source():
    from django_statsd.clients import statsd
    from django.db import connection
    cursor = connection.cursor()

    now = datetime.datetime.today()
    today = datetime.datetime(now.year, now.month, now.day).strftime('%Y-%m-%d')

    # 有　mm_linkid，是小鹿妈妈分享的链接
    sql = """
        SELECT count(*) FROM flashsale_trade
        where extras_info not REGEXP '"mm_linkid": 0'
        and pay_time > %s
    """
    cursor.execute(sql, today)
    share_trades_count = cursor.fetchone()[0]

    # 没有 mm_linkid，但是买家是小鹿妈妈
    sql = """
        SELECT count(*)
        FROM flashsale_trade
        join flashsale_customer on flashsale_customer.id=flashsale_trade.buyer_id
        join xiaolumm_xiaolumama on flashsale_customer.unionid=xiaolumm_xiaolumama.openid
        where flashsale_trade.pay_time > %s
        and flashsale_trade.extras_info REGEXP '"mm_linkid": 0'
    """
    cursor.execute(sql, today)
    xiaolumm_trades_count = cursor.fetchone()[0]

    # 今日所有订单
    sql = """
        SELECT count(*) FROM flashsale_trade
        where pay_time > %s
    """
    cursor.execute(sql, today)
    all_trades_count = cursor.fetchone()[0]
    direct_count = all_trades_count - share_trades_count - xiaolumm_trades_count

    statsd.timing('xiaolumm.postpay_from_xiaolumama_count', share_trades_count + xiaolumm_trades_count)
    statsd.timing('xiaolumm.postpay_from_direct_count', direct_count)


@task()
def task_schedule_check_teambuy():
    _now = datetime.datetime.now()
    for teambuy in TeamBuy.objects.filter(limit_time__lt=_now, status=0):
        if teambuy.details.count() >= teambuy.limit_person_num:
            teambuy.set_status_success()
        else:
            teambuy.set_status_failed()
