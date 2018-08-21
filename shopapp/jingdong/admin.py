# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from core.filters import DateFieldListFilter
from .models import JDShop, JDOrder, JDProduct, JDLogistic


class JDShopAdmin(admin.ModelAdmin):
    list_display = ('shop_id', 'vender_id', 'shop_name', 'open_time',
                    'order_updated', 'refund_updated')

    list_display_links = ('shop_id', 'shop_name')

    search_fields = ['shop_id', 'vender_id', 'shop_name']


admin.site.register(JDShop, JDShopAdmin)


class JDLogisticAdmin(admin.ModelAdmin):
    list_display = ('logistics_id', 'logistics_name', 'company_code',
                    'logistics_remark', 'sequence')

    list_display_links = ('logistics_name',)

    search_fields = ['logistics_id', 'logistics_name']


admin.site.register(JDLogistic, JDLogisticAdmin)


class JDProductAdmin(admin.ModelAdmin):
    list_display = ('ware_id', 'item_num', 'title', 'jd_price', 'stock_num'
                    , 'online_time', 'created', 'status', 'ware_status')

    list_display_links = ('ware_id', 'item_num')

    list_filter = ('status', 'ware_status', ('online_time', DateFieldListFilter))
    search_fields = ['ware_id', 'item_num', 'outer_id', 'title']


admin.site.register(JDProduct, JDProductAdmin)


class JDOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'shop', 'pin', 'pay_type', 'order_payment', 'freight_price',
                    'order_start_time', 'order_type', 'order_state')

    list_display_links = ('order_id', 'pin')

    list_filter = ('shop', 'pay_type', 'order_type', 'order_state')
    search_fields = ['order_id', 'pin']


admin.site.register(JDOrder, JDOrderAdmin)
