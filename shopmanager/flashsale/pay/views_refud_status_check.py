# coding=utf-8
from models_refund import SaleRefund
from django.db.models.signals import post_save
from models import SaleTrade, SaleOrder


def check_SaleRefund_Status(sender, instance, created, **kwargs):
    # created 表示实例是否创建 （修改）
    # 允许抛出异常
    order = SaleOrder.objects.get(id=instance.order_id)
    trade = SaleTrade.objects.get(id=instance.trade_id)

    # 退款成功  如果是退款关闭要不要考虑？？？
    if instance.status == SaleRefund.REFUND_SUCCESS or instance.status == SaleRefund.REFUND_CLOSED:

        # 如果是退款成功状态
        # 找到订单
        refund_num = instance.refund_num  # 退款数量
        order_num = order.num  # 订单数量
        if refund_num == order_num:  # 退款数量等于订单数量
            # 关闭这个订单
            order.status = SaleOrder.TRADE_CLOSED  # 退款关闭
            order.save()
        """ 判断交易状态 """
        orders = trade.sale_orders.all()
        flag_re = 0
        for orde in orders:
            if orde.status == SaleOrder.TRADE_CLOSED:
                flag_re += 1

        if flag_re == orders.count():  # 所有订单都退款成功
            # 这笔交易 退款 关闭
            trade.status = SaleTrade.TRADE_CLOSED
            trade.save()

    """ 同步退款状态到订单，这里至更新 退款的状态到订单的 退款状态字段 """
    order.refund_status = instance.status
    order.save()  # 保存同步的状态


post_save.connect(check_SaleRefund_Status, sender=SaleRefund)
