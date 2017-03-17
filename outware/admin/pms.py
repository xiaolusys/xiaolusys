# coding: utf8
from __future__ import absolute_import, unicode_literals


from django.contrib import admin
from django.shortcuts import redirect

from ..models import OutwareAccount, OutwareSupplier, OutwareSku, OutwareInboundOrder, OutwareInboundSku
from ..adapter.ware.pull.pms import union_sku_and_supplier

@admin.register(OutwareSupplier)
class OutwareSupplierAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'vendor_name', 'outware_account')
    search_fields = ['=id','=vendor_code']
    ordering = ('-modified',)


@admin.register(OutwareSku)
class OutwareSkuAdmin(admin.ModelAdmin):
    list_display = ('sku_code', 'ware_sku_code', 'outware_supplier', 'is_unioned')
    list_filter = ('is_unioned',)
    search_fields = ['=id','=sku_code']
    ordering = ('-created',)

    def union_sku_and_supplier(self, request, queryset):
        """ 更新订单到订单总表 """

        for ow_sku in queryset.filter(is_unioned=False).iterator():
            union_sku_and_supplier(ow_sku )

        self.message_user(request, u'已更新%s个订单到订单总表!' % queryset.count())
        origin_url = request.get_full_path()

        return redirect(origin_url)

    union_sku_and_supplier.short_description = u"关联sku与供应商"

    actions = ['union_sku_and_supplier']


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