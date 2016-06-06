# coding: utf-8
from django.contrib import admin
from core.filters import DateFieldListFilter
from flashsale.finance.models import Bill


class BillAdmin(admin.ModelAdmin):
    list_display = ('id','type','status','creater','bill_method','plan_amount','supplier','amount','pay_method','pay_taobao_link','receive_account','receive_name','pay_account','note')
    search_fields = ['id', "transcation_no"]

    list_filter = ["type", "status", "bill_method", "pay_method", ('created', DateFieldListFilter)]
    readonly_fields = ('status', 'creater', 'supplier')
    list_display_links = ['id',]
    list_select_related = True
    list_per_page = 25

admin.site.register(Bill, BillAdmin)