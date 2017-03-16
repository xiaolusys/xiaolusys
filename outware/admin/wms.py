# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from ..models import OutwareSkuStock

@admin.register(OutwareSkuStock)
class OutwareSkuStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'outware_supplier', 'sku_code', 'store_code', 'batch_no', 'push_sku_good_qty',
                    'push_sku_bad_qty', 'pull_good_available_qty', 'pull_good_lock_qty', 'pull_bad_qty')
    search_fields = ['=id','=sku_code']
    ordering = ('-created',)