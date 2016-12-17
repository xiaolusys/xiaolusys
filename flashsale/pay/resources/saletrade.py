# coding: utf8
from __future__ import absolute_import, unicode_literals

from import_export import fields
from import_export import resources
from ..models import SaleOrder

class SaleOrderResource(resources.ModelResource):
    tid = fields.Field()
    status_display   = fields.Field()
    receiver_name = fields.Field()
    receiver_state = fields.Field()
    receiver_city = fields.Field()

    class Meta:
        model = SaleOrder
        fields = ('oid', 'tid', 'payment', 'status_display', 'pay_time', 'title', 'num', 'receiver_name', 'receiver_state', 'receiver_city')
        export_order = fields


    def dehydrate_tid(self, obj):
        return obj.sale_trade.tid

    def dehydrate_status_display(self, obj):
        return obj.get_status_display()

    def dehydrate_receiver_name(self, obj):
        return obj.sale_trade.receiver_name

    def dehydrate_receiver_state(self, obj):
        return obj.sale_trade.receiver_state

    def dehydrate_receiver_city(self, obj):
        return obj.sale_trade.receiver_city