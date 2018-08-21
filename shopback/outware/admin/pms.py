# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.db.models import Q
from django.shortcuts import redirect
from django.contrib.admin.views.main import ChangeList

from ..models import OutwareAccount, OutwareSupplier, OutwareSku, OutwareInboundOrder, OutwareInboundSku
from ..adapter.ware.pull.pms import union_sku_and_supplier

@admin.register(OutwareSupplier)
class OutwareSupplierAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'vendor_name', 'outware_account')
    search_fields = ['=id','=vendor_code']
    ordering = ('-modified',)

class OutwareSkuChangeList(ChangeList):
    def get_queryset(self, request):
        search_q = request.GET.get('q', '').strip()
        if search_q.lower().startswith(':'):
            model_code = search_q.repalce(':','')
            from shopback.items.models import ProductSku
            productskus = ProductSku.objects.filter(Q(product__model_id=model_code)|Q(product__outer_id__startswith=model_code))
            sku_codes = productskus.values_list('outer_id', flat=True)
            return OutwareSku.objects.filter(sku_code__in=sku_codes)

        return super(OutwareSkuChangeList, self).get_queryset(request)

@admin.register(OutwareSku)
class OutwareSkuAdmin(admin.ModelAdmin):
    list_display = ('sku_code', 'ware_sku_code', 'outware_supplier', 'sku_type', 'is_unioned',
                    'is_pushed_success', 'is_batch_mgt', 'is_expire_mgt', 'is_vendor_mgt', 'created')
    list_filter = ('is_unioned', 'is_batch_mgt', 'is_expire_mgt', 'is_vendor_mgt')
    search_fields = ['=id','=sku_code']
    ordering = ('-created',)

    def get_changelist(self, request, **kwargs):
        return OutwareSkuChangeList

    def is_pushed_success(self, obj):
        return obj.is_pushed_ok

    is_pushed_success.boolean = True
    is_pushed_success.short_description = '已接收'

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
    list_display = ('inbound_code', 'store_code', 'order_type', 'outware_supplier' ,'status', 'created')
    list_filter = ('order_type',)
    search_fields = ['=id','=inbound_code']
    ordering = ('-created',)

@admin.register(OutwareInboundSku)
class OutwareInboundSkuAdmin(admin.ModelAdmin):
    list_display = ('outware_inboind', 'sku_code', 'batch_no', 'push_qty', 'pull_good_qty', 'pull_bad_qty')
    search_fields = ['=id','=sku_code', '=batch_no']
    ordering = ('-created',)