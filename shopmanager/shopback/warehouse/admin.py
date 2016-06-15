# -*- coding:utf8 -*-
from django.contrib import admin
from .models import WareHouse, ReceiptGoods


class WareHouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'ware_name', 'city', 'address', 'in_active', 'extra_info')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('in_active',)
    search_fields = ['ware_name', 'city']


admin.site.register(WareHouse, WareHouseAdmin)


class ReceiptGoodsAdmin(admin.ModelAdmin):
    list_display = (
        "creator",
        "receipt_type",
        "weight",
        "weight_time",
        "express_no",
        "express_company_display",
        "created",
        "modified",
    )
    list_filter = (
        "creator",
        "receipt_type",
        "weight_time",
        "express_company",
        "created",
    )
    search_fields = [
        "=creator",
        "=express_no",
    ]

    def express_company_display(self, obj):
        if obj.logistic_company():
            return obj.logistic_company().name
        return ''

    express_company_display.allow_tags = True
    express_company_display.short_description = u'快递公司'


admin.site.register(ReceiptGoods, ReceiptGoodsAdmin)
