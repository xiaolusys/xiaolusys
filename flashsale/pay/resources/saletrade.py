# coding: utf8
from __future__ import absolute_import, unicode_literals

from import_export import fields
from import_export import resources
from ..models import SaleTrade

class SaleTradeResource(resources.ModelResource):
    order_title = fields.Field()
    order_num   = fields.Field()

    class Meta:
        model = SaleTrade
        fields = ('tid', 'payment', 'pay_time', 'receiver_name' 'order_title', 'order_num', 'receiver_state', 'receiver_city')


    def dehydrate_order_title(self, obj):
        order = obj.normal_orders.first()
        if order:
            return order.title
        return ''

    def dehydrate_order_num(self, obj):
        order = obj.normal_orders.first()
        if order:
            return order.num
        return 0
