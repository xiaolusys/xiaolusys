# coding=utf-8
from models_refund import SaleRefund
from django.db.models.signals import post_save
from models import SaleTrade, SaleOrder


def check_SaleRefund_Status(sender, instance, created, **kwargs):
    # created 表示实例是否创建 （修改）
    # 允许抛出异常
    order = SaleOrder.objects.get(id=instance.order_id)
    trade = SaleTrade.objects.get(id=instance.trade_id)

    if instance.status == SaleRefund.REFUND_SUCCESS:    # 退款成功  如果是退款关闭要不要考虑？？？
        # 如果是退款成功状态
        # 找到订单
        refund_num = instance.refund_num  # 退款数量
        order_num = order.num  # 订单数量
        if refund_num == order_num:  # 退款数量等于订单数量
            # 关闭这个比订单
            order.status = SaleOrder.TRADE_CLOSED  # 退款关闭
            order.save()
        """ 判断交易状态 """
        orders = trade.sale_orders.all()
        flag_re = 0
        flag_sys_cls = 0
        for orde in orders:
            if orde.status == SaleOrder.TRADE_CLOSED:
                flag_re += 1
            if orde.status == SaleOrder.TRADE_CLOSED:
                flag_sys_cls += 1
        if flag_re == orders.count():  # 所有订单都退款成功
            # 这笔交易 退款 关闭
            trade.status = SaleTrade.TRADE_CLOSED
            trade.save()
        if flag_sys_cls == orders.count() or flag_sys_cls + flag_re == orders.count():
            # 如果有系统关闭订单 并且 数量等于 订单数量 则交易关闭
            trade.status = SaleTrade.TRADE_CLOSED
            trade.save()

    """ 同步退款状态到订单，这里至更新 退款的状态到订单的 退款状态字段 """
    order.refund_status = instance.status
    order.save()  # 保存同步的状态


post_save.connect(check_SaleRefund_Status, sender=SaleRefund)
