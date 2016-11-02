from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from shopback.fenxiao.models import PurchaseOrder, FenxiaoProduct, SubPurchaseOrder

__author__ = 'meixqhi'


class SubPurchaseOrderInline(admin.TabularInline):
    model = SubPurchaseOrder
    fields = ('tc_order_id', 'item_outer_id', 'title', 'sku_outer_id', 'old_sku_properties',
              'num', 'price', 'order_200_status', 'status')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '12'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 20})},
    }


class FenxiaoProductAdmin(admin.ModelAdmin):
    list_display = ('pid', 'name', 'productcat_id', 'user', 'trade_type', 'standard_price', 'category', 'item_id',
                    'cost_price', 'outer_id', 'quantity', 'have_invoice', 'items_count', 'orders_count', 'created',
                    'modified', 'status')
    list_filter = ('user', 'trade_type', 'status',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    search_fields = ['pid', 'name', 'outer_id']


admin.site.register(FenxiaoProduct, FenxiaoProductAdmin)


class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('fenxiao_id', 'id', 'seller_id', 'supplier_username', 'distributor_username', 'logistics_id',
                    'logistics_company_name', 'trade_type', 'consign_time', 'created', 'pay_time', 'modified',
                    'pay_type', 'status')
    list_display_links = ('fenxiao_id', 'id', 'supplier_username', 'distributor_username')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    inlines = [SubPurchaseOrderInline]

    list_filter = ('shipping', 'pay_type', 'trade_type', 'status',)
    search_fields = ['fenxiao_id', 'id', 'supplier_username', 'distributor_username', 'tc_order_id']


admin.site.register(PurchaseOrder, PurchaseOrderAdmin)


class SubPurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('fenxiao_id', 'id', 'purchase_order', 'sku_id', 'tc_order_id', 'fenxiao_product',
                    'num', 'price', 'order_200_status', 'created', 'status')
    list_display_links = ('fenxiao_id', 'id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    list_filter = ('order_200_status', 'status',)
    search_fields = ['fenxiao_id', 'purchase_order__fenxiao_id', 'sku_id', 'tc_order_id', 'title']


admin.site.register(SubPurchaseOrder, SubPurchaseOrderAdmin)
