# -*- coding:utf-8 -*-
from django.contrib import admin
from flashsale.dinghuo.models import OrderList, OrderDetail, orderdraft
from django.http import HttpResponseRedirect
from flashsale.dinghuo import log_action, CHANGE
from shopback.base.options import DateFieldListFilter

class orderdetailInline(admin.TabularInline):
    model = OrderDetail
    fields = (
        'product_name', 'outer_id', 'product_chicun', 'buy_quantity', 'buy_unitprice', 'total_price',
        'arrival_quantity')
    extra = 3


class ordelistAdmin(admin.ModelAdmin):
    fieldsets = ((u'订单信息:', {
        'classes': ('expand',),
        'fields': ( 'supplier_name', 'express_company', 'express_no'
                   , 'receiver', 'status', 'note')
    }),)
    inlines = [orderdetailInline]
    list_display = ('id', 'buyer_name', 'order_amount', 'supplier_name', 'express_company', 'express_no'
                    , 'receiver', 'created', 'shenhe', 'note')
    list_filter = (('created',DateFieldListFilter),)
    search_fields = ['buyer_name']
    date_hierarchy = 'created'


        
    def shenhe(self, obj):
        symbol_link = obj.status or u'【空标题】'
        return '<a href="/sale/dinghuo/detail/{0}/" >{1}</a>'.format(int(obj.id), symbol_link)

    shenhe.allow_tags = True
    shenhe.short_description = "状态"

    def orderlist_ID(self, obj):
        symbol_link = obj.id or u'【空标题】'
        return '<a href="/sale/dinghuo/detail/{0}/" >{1}</a>'.format(int(obj.id), symbol_link)

    orderlist_ID.allow_tags = True
    orderlist_ID.short_description = "订单编号"


    # 测试action
    def test_order_action(self, request, queryset):
        for p in queryset:
            if p.status != "审核":
                p.status = "审核"
                p.save()
                log_action(request.user.id, p, CHANGE, u'审核订货单')

                self.message_user(request, u"已成功审核!")

        return HttpResponseRedirect(request.get_full_path())

    test_order_action.short_description = u"审核（批量 ）"

    actions = ['test_order_action']


admin.site.register(OrderList, ordelistAdmin)
admin.site.register(OrderDetail)
admin.site.register(orderdraft)

