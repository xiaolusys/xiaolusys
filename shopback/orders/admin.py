# -*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea

from shopback.orders.models import Order, Trade
from core.filters import DateFieldListFilter

class OrderInline(admin.TabularInline):
    model = Order
    fields = ('outer_id', 'outer_sku_id', 'title', 'buyer_nick', 'price', 'payment', 'num',
              'sku_properties_name', 'refund_id', 'refund_status', 'status')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '12'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }


class TradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller_nick', 'buyer_nick', 'type', 'payment', 'seller_id', 'created',
                    'consign_time', 'pay_time', 'end_time', 'modified', 'shipping_type',
                    'buyer_alipay_no', 'receiver_name', 'receiver_mobile', 'receiver_phone', 'status')
    list_display_links = ('id', 'buyer_nick', 'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    inlines = [OrderInline]

    list_filter = ('seller_nick', 'type', 'status', ('created', DateFieldListFilter))
    search_fields = ['id', 'buyer_nick']

    # --------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }


admin.site.register(Trade, TradeAdmin)


class OrderAdmin(admin.ModelAdmin):
    list_display = ('oid', 'seller_nick', 'buyer_nick', 'trade', 'price', 'num_iid'
                    , 'sku_id', 'num', 'outer_sku_id', 'sku_properties_name', 'payment'
                    , 'refund_id', 'is_oversold', 'refund_status', 'outer_id', 'cid', 'status')
    list_display_links = ('oid', 'trade', 'refund_id', 'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    # ordering = ['created_at']

    list_filter = ('status', 'refund_status' ,('created', DateFieldListFilter))
    search_fields = ['oid', 'buyer_nick', 'num_iid', 'sku_properties_name']


admin.site.register(Order, OrderAdmin)
