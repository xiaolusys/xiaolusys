# coding=utf-8
from flashsale.pay.models import SaleTrade, SaleOrder
from flashsale.pay.models_user import Customer
from models_coupon import IntegralLog
from django.core.signals import request_finished
from django.db.models.signals import post_save
import logging
"""
当创建订单的时候创建积分待确认记录
"""


def add_Order_Integral(sender, instance, **kwargs):
    order_id = instance.id
    pic_link = instance.pic_path
    trade_id = instance.sale_trade_id
    order_status = instance.status
    order_content = '[{"order_id":"%s","pic_link":"%s","trade_id":"%s","order_status":"%s"}]' % (str(order_id), str(pic_link), str(trade_id), str(order_status))

    trade = SaleTrade.objects.get(id=instance.sale_trade_id)  # 由订单找交易
    cus = Customer.objects.get(id=trade.buyer_id)  # 由交易的buyer_id找
    buyer_id = trade.buyer_id
    orid = instance.id
    try:
        integrallog = IntegralLog.objects.get(integral_user=buyer_id, order_id=orid)
    except Exception,exc:
        # log = logging.getLogger('django.request')
        # log.error(exc.message, exc_info=True)
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


post_save.connect(add_Order_Integral, sender=SaleOrder)


# def my_callback(**kwargs):
# print 'abcdef'
# request_finished.connect(my_callback)

