# coding=utf-8
from flashsale.pay.models import SaleTrade, SaleRefund, SaleOrder
from shopback.refunds.models_refund_rate import PayRefund24HRate
import datetime
from django.db.models import F
from flashsale.pay.signals import signal_saletrade_pay_confirm, signal_saletrade_refund_post
from common.modelutils import update_model_fields


def triger_24hour_pay(sender, obj, **kwargs):
    """ 确认付款　计算订单数量　填写到　24小时　退款率表中　"""
    today_date = datetime.date.today()
    pay_num = obj.normal_orders.all().count()  # 订单的数量
    rate24, state = PayRefund24HRate.objects.get_or_create(date_cal=today_date)
    if state:  # 新建记录　填写　付款成功数量
        rate24.pay_num = pay_num
    else:  # 有记录则累加
        rate24.pay_num += pay_num
    update_model_fields(rate24, update_fields=['pay_num'])
    rate24.calculate_rate()


signal_saletrade_pay_confirm.connect(triger_24hour_pay, sender=SaleTrade)


def triger_24hour_refund(sender, obj, **kwargs):
    order = SaleOrder.objects.get(id=obj.order_id)
    trade = order.sale_trade
    time_from = trade.pay_time
    time_to = trade.pay_time + datetime.timedelta(days=1)
    date_cal = datetime.date(time_from.year, time_from.month, time_from.day)
    # 判断提交申请的时间是否是在付款后24小时内产生的
    if obj.created <= time_from or obj.created >= time_to:
        return
    else:
        rate24, state = PayRefund24HRate.objects.get_or_create(date_cal=date_cal)
        if state:  # 新建记录　填写　付款成功数量
            rate24.ref_num = 1
        else:  # 有记录则累加
            rate24.ref_num += 1
        update_model_fields(rate24, update_fields=['ref_num'])
        rate24.calculate_rate()


signal_saletrade_refund_post.connect(triger_24hour_refund, sender=SaleRefund)
