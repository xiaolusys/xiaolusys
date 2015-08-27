# coding=utf-8
from flashsale.pay.models import SaleTrade, SaleOrder
from flashsale.pay.models_user import Customer
from models_coupon import IntegralLog, Integral
from django.core.signals import request_finished
from django.db.models.signals import post_save
import logging
import datetime
from django.db.models import ObjectDoesNotExist
"""
当创建订单的时候创建积分待确认记录
"""
INTEGRAL_START_TIME = datetime.datetime(2015, 7, 25, 0, 0, 0)


def get_IntegralLog(buyer_id, orid):
    try:
        integrallog = IntegralLog.objects.get(integral_user=buyer_id, order_id=orid)
        return integrallog
    except ObjectDoesNotExist:
        return False


def add_Order_Integral(sender, instance, created, **kwargs):
    # 记录要对应到商品上
    # 根据订单的状态来处理积分的状态
    order_created = instance.created       # Order创建时间
    order_id = instance.id
    pic_link = instance.pic_path
    trade_id = instance.sale_trade_id
    order_status = instance.status
    order_content = '[{"order_id":"%s","pic_link":"%s","trade_id":"%s","order_status":"%s"}]' % (
    str(order_id), str(pic_link), str(trade_id), str(order_status))
    trade = SaleTrade.objects.get(id=instance.sale_trade_id)  # 由订单找交易
    cus = Customer.objects.get(id=trade.buyer_id)  # 由交易的buyer_id找
    buyer_id = trade.buyer_id  # 用户ID
    orid = instance.id  # order id
    if instance.outer_id == 'RMB100' or instance.outer_id == 'RMB118':    # 代理费不需要生成积分
        return
    if order_created >= INTEGRAL_START_TIME and instance.status == SaleOrder.WAIT_SELLER_SEND_GOODS:
        # 生成时间必须是大于活动开始时间  AND  必须是已经付款的才有积分记录   # SaleOrder.WAIT_SELLER_SEND_GOODS  # 已经付款
        integrallog = get_IntegralLog(buyer_id, orid)
        if integrallog is False:
            integrallog = IntegralLog()
            integrallog.integral_user = buyer_id
            integrallog.order_id = orid
            integrallog.mobile = cus.mobile
            integrallog.log_value = int(instance.payment)
            integrallog.order = order_content
            integrallog.log_status = IntegralLog.PENDING
            integrallog.log_type = IntegralLog.ORDER_INTEGRA
            integrallog.in_out = IntegralLog.LOG_IN
            integrallog.save()
        else:
            integrallog.mobile = cus.mobile
            integrallog.log_value = int(instance.payment)
            integrallog.order = order_content
            integrallog.log_status = IntegralLog.PENDING
            integrallog.log_type = IntegralLog.ORDER_INTEGRA
            integrallog.in_out = IntegralLog.LOG_IN
            integrallog.save()
    elif instance.status == SaleOrder.TRADE_CLOSED and order_created >= INTEGRAL_START_TIME:
        # TRADE_CLOSED # 根据订单的状态来处理积分的状态  退款关闭的 积分要取消掉
        integrallog = get_IntegralLog(buyer_id, orid)
        if integrallog:
            integrallog.log_status = IntegralLog.CANCEL  # 取消积分
            integrallog.save()
    elif instance.status == SaleOrder.TRADE_FINISHED and order_created >= INTEGRAL_START_TIME:
        # 交易成功  # 修改积分状态为确认状态
        # 没有就创建  有则修改  该用户的积分累计记录
        integrallog = get_IntegralLog(buyer_id, orid)
        if integrallog:
            integrallog.log_status = IntegralLog.CONFIRM  # 确认积分
            integrallog.save()
            try:
                user_interal = Integral.objects.get(integral_user=buyer_id)
                user_interal.integral_value += int(instance.payment)
                user_interal.save()
            except ObjectDoesNotExist:
                user_interal = Integral()
                user_interal.integral_user = buyer_id
                user_interal.integral_value = int(instance.payment)
                user_interal.save()

post_save.connect(add_Order_Integral, sender=SaleOrder)
