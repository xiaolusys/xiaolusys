# coding: utf8
from __future__ import absolute_import, unicode_literals


from django.contrib import admin

from ..models import OutwareAccount, OutwareSupplier, OutwareSku, OutwareInboundOrder, OutwareInboundSku

@admin.register(OutwareSupplier)
class OutwareSupplierAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'vendor_name', 'outware_account')
    search_fields = ['=id','=vendor_code']
    ordering = ('-modified',)


@admin.register(OutwareSku)
class OutwareSkuAdmin(admin.ModelAdmin):
    list_display = ('sku_code', 'ware_sku_code', 'outware_supplier')
    search_fields = ['=id','=sku_code']
    ordering = ('-created',)


@admin.register(OutwareInboundOrder)
class OutwareInboundOrderAdmin(admin.ModelAdmin):
    list_display = ('inbound_code', 'store_code', 'order_type', 'outware_supplier' )
    list_filter = ('order_type',)
    search_fields = ['=id','=inbound_code']
    ordering = ('-created',)

@admin.register(OutwareInboundSku)
class OutwareInboundSkuAdmin(admin.ModelAdmin):
    list_display = ('outware_inboind', 'sku_code', 'batch_no', 'push_qty', 'pull_good_qty', 'pull_bad_qty')
    search_fields = ['=id','=sku_code', '=batch_no']
    ordering = ('-created',)