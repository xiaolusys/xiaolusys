# coding=utf-8
__author__ = 'jishu_linjie'
from flashsale.pay.signals import signal_saletrade_pay_confirm
from flashsale.pay.models import SaleTrade
from shopback.items.models import Product
from common.modelutils import update_model_fields
from django.db.models import F


def record_supplier_args(sender, obj, **kwargs):
    """ 随支付成功信号　更新供应商的销售额，　销售数量
        :arg obj -> SaleTrade instance
        :except None
        :return None
    """
    normal_orders = obj.normal_orders.all()
    for order in normal_orders:
        item_id = order.item_id
        pro = Product.objects.get(id=item_id)
        sal_p, supplier = pro.pro_sale_supplier()
        if supplier is not None:
            supplier.total_sale_num = F('total_sale_num') + order.num
            supplier.total_sale_amount = F("total_sale_amount") + order.payment
        update_model_fields(supplier, update_fields=['total_sale_num', 'total_sale_amount'])


signal_saletrade_pay_confirm.connect(record_supplier_args, sender=SaleTrade)


