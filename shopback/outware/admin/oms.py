# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from core.filters import DateFieldListFilter
from ..models import OutwareOrder, OutwareOrderSku, OutwarePackage, OutwarePackageSku

@admin.register(OutwareOrder)
class OutwareOrderAdmin(admin.ModelAdmin):
    list_display = ('outware_account', 'union_order_code', 'order_type', 'order_source', 'store_code', 'status', 'created')
    list_filter = ('order_type', 'status',)
    search_fields = ['=union_order_code']
    ordering = ('-modified',)


@admin.register(OutwareOrderSku)
class OutwareOrderSkuAdmin(admin.ModelAdmin):
    list_display = ('outware_account', 'origin_skuorder_no', 'union_order_code', 'sku_code', 'sku_qty', 'created')
    list_filter = (('created', DateFieldListFilter), )
    search_fields = ['=origin_skuorder_no', "=union_order_code", "=sku_code"]
    ordering = ('-modified',)


@admin.register(OutwarePackage)
class OutwarePackageAdmin(admin.ModelAdmin):
    list_display = ('id', 'outware_account', 'package_order_code', 'package_type',
                    'store_code', 'logistics_no', 'carrier_code', 'created')
    list_filter = ('package_type','store_code', 'carrier_code')
    search_fields = ['=package_order_code', "=logistics_no"]
    ordering = ('-modified',)


@admin.register(OutwarePackageSku)
class OutwarePackageSkuAdmin(admin.ModelAdmin):
    list_display = ('package', 'origin_skuorder_no', 'sku_code', 'batch_no', 'sku_qty', 'created')
    search_fields = ['=origin_skuorder_no', '=sku_code']
    ordering = ('-modified',)