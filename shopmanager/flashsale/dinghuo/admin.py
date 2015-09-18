# -*- coding:utf-8 -*-
from django.contrib import admin
from flashsale.dinghuo.models import OrderList, OrderDetail, orderdraft, ProductSkuDetail
from django.http import HttpResponseRedirect
from flashsale.dinghuo import log_action, CHANGE
from flashsale.dinghuo.filters import DateFieldListFilter
from flashsale.dinghuo.models_user import MyUser, MyGroup
from flashsale.dinghuo.models_stats import SupplyChainDataStats, SupplyChainStatsOrder, DailySupplyChainStatsOrder
import time
from .filters import GroupNameFilter, OrderListStatusFilter
from flashsale.dinghuo import permissions as perms
from django.contrib.admin.views.main import ChangeList
from django.db import models
import re


class orderdetailInline(admin.TabularInline):
    model = OrderDetail
    fields = ('product_id', 'chichu_id', 'product_name', 'outer_id', 'product_chicun', 'buy_quantity', 'buy_unitprice',
              'total_price', 'arrival_quantity')
    extra = 3

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_change_order_list_inline_permission(request.user):
            return self.readonly_fields + (
                'product_id', 'chichu_id', 'product_name', 'outer_id', 'product_chicun', 'buy_quantity',
                'arrival_quantity')
        return self.readonly_fields


class ordelistAdmin(admin.ModelAdmin):
    fieldsets = ((u'订单信息:', {
        'classes': ('expand',),
        'fields': ('supplier_name', 'supplier_shop', 'express_company', 'express_no'
                   , 'receiver', 'status', 'order_amount', 'note', 'p_district')
    }),)
    inlines = [orderdetailInline]

    list_display = (
        'id', 'buyer_name', 'order_amount', 'quantity', 'receiver', 'display_pic', 'created', 'shenhe',
        'changedetail', 'note_name', 'supply_chain', 'p_district', 'reach_standard', 'updated'
    )
    list_filter = (('created', DateFieldListFilter), GroupNameFilter, OrderListStatusFilter, 'buyer_name')
    search_fields = ['id', '=supplier_name', 'supplier_shop', 'express_no', 'note']
    date_hierarchy = 'created'

    def queryset(self, request):
        qs = super(ordelistAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.exclude(status='作废')

    def quantity(self, obj):
        alldetails = OrderDetail.objects.filter(orderlist_id=obj.id)
        quantityofoneorder = 0
        for detail in alldetails:
            quantityofoneorder += detail.buy_quantity
        return '{0}'.format(quantityofoneorder)

    quantity.allow_tags = True
    quantity.short_description = "商品数量"

    def supply_chain(self, obj):
        return u'<div style="width: 150px;overflow: hidden;white-space: nowrap;text-overflow: ellipsis;"><a href="{0}" target="_blank" >{1}</a></div>'.format(obj.supplier_name,
                                                               obj.supplier_shop or obj.supplier_name)

    supply_chain.allow_tags = True
    supply_chain.short_description = "供应商"

    def display_pic(self, obj):
        return u'<a href="#{0}" onclick="show_pic({0})" >图片{0}</a>'.format(obj.id)

    display_pic.allow_tags = True
    display_pic.short_description = "显示图片"

    def note_name(self, obj):
        return u'<pre style="width:300px;white-space: pre-wrap;word-break:break-all;">{0}</pre>'.format(
            obj.note)

    note_name.allow_tags = True
    note_name.short_description = "备注"

    def shenhe(self, obj):
        symbol_link = obj.get_status_display()
        return symbol_link

    shenhe.allow_tags = True
    shenhe.short_description = "状态"

    def changedetail(self, obj):
        symbol_link = u'【详情页】'
        return u'<a href="/sale/dinghuo/changedetail/{0}/" target="_blank" style="display: block;" >{1}</a>'.format(
            int(obj.id), symbol_link)

    changedetail.allow_tags = True
    changedetail.short_description = "更改订单"

    def orderlist_ID(self, obj):
        symbol_link = obj.id or u'【空标题】'
        return '<a href="/sale/dinghuo/detail/{0}/" >{1}</a>'.format(int(obj.id), symbol_link)

    orderlist_ID.allow_tags = True
    orderlist_ID.short_description = "订单编号"

    def get_readonly_fields(self, request, obj=None):
        if not perms.has_change_order_list_inline_permission(request.user):
            return self.readonly_fields + ('status', 'supplier_shop',)
        return self.readonly_fields

    # 批量审核
    def test_order_action(self, request, queryset):
        for p in queryset:
            if p.status != "审核":
                p.status = "审核"
                p.save()
                log_action(request.user.id, p, CHANGE, u'审核订货单')

                self.message_user(request, u"已成功审核!")

        return HttpResponseRedirect(request.get_full_path())

    test_order_action.short_description = u"审核（批量 ）"


    # 批量验货完成
    def action_quick_complete(self, request, queryset):
        count = 0
        for p in queryset:
            if p.status == OrderList.APPROVAL:
                p.status = OrderList.DEALED
                p.save()
                log_action(request.user.id, p, CHANGE, u'过期处理订货单')
                count += 1
        self.message_user(request, u"成功处理{0}个订货单!".format(str(count)))

        return HttpResponseRedirect(request.get_full_path())

    action_quick_complete.short_description = u"处理过期订货单（批量 ）"
    actions = ['test_order_action', 'action_quick_complete']

    def get_actions(self, request):

        user = request.user
        actions = super(ordelistAdmin, self).get_actions(request)

        if user.is_superuser:
            return actions
        else:
            del actions["action_quick_complete"]
            return actions

    def get_changelist(self, request, **kwargs):
        return OrderListChangeList

    class Media:
        css = {"all": ("css/admin_css.css", "https://cdn.bootcss.com/lightbox2/2.7.1/css/lightbox.css")}
        js = ("js/admin_js.js", "https://cdn.bootcss.com/lightbox2/2.7.1/js/lightbox.js")


class OrderListChangeList(ChangeList):

    def get_query_set(self, request):
        qs = self.root_query_set
        search_q = request.GET.get('q', '').strip()
        if search_q.isdigit():
            trades = qs.filter(models.Q(id=search_q))
            return trades
        return super(OrderListChangeList, self).get_query_set(request)


class orderdetailAdmin(admin.ModelAdmin):
    fieldsets = ((u'订单信息:', {
        'classes': ('expand',),
        'fields': (
            'product_id', 'outer_id', 'product_name', 'chichu_id', 'product_chicun', 'buy_quantity', 'arrival_quantity',
            'inferior_quantity', 'non_arrival_quantity')
    }),)

    list_display = (
        'id', 'orderlist', 'product_id', 'outer_id', 'product_name', 'chichu_id', 'product_chicun', 'buy_quantity',
        'arrival_quantity', 'inferior_quantity', 'non_arrival_quantity', 'created', 'updated'
    )
    list_filter = (('created', DateFieldListFilter),)
    search_fields = ['id', 'orderlist__id', 'product_id', 'outer_id']
    date_hierarchy = 'created'

    def queryset(self, request):
        qs = super(orderdetailAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.exclude(orderlist__status='作废')


admin.site.register(OrderList, ordelistAdmin)
admin.site.register(OrderDetail, orderdetailAdmin)
admin.site.register(orderdraft)


class myuserAdmin(admin.ModelAdmin):
    fieldsets = ((u'用户信息:', {
        'classes': ('expand',),
        'fields': ('user', 'group')
    }),)

    list_display = (
        'user', 'group'
    )
    list_filter = ('group',)
    search_fields = ['user__username']


admin.site.register(MyUser, myuserAdmin)
admin.site.register(MyGroup)


class SupplyChainDataStatsAdmin(admin.ModelAdmin):
    list_display = ('sale_quantity', 'cost_amount', 'turnover',
                    'order_goods_quantity', 'order_goods_amount',
                    'stats_time', 'group',
                    'created', 'updated')
    list_filter = ('group', 'created',)
    search_fields = ['group']
    ordering = ('-stats_time',)


admin.site.register(SupplyChainDataStats, SupplyChainDataStatsAdmin)


class SupplyChainStatsOrderAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'outer_sku_id', 'sale_time', 'shelve_time', 'sale_num', 'trade_general_time_name',
                    'ding_huo_num', 'order_deal_time_name',
                    'arrival_num', 'goods_arrival_time_name',
                    'goods_out_num', 'goods_out_time_name', "refund_amount_num", "refund_num")
    search_fields = ['product_id']

    def trade_general_time_name(self, obj):
        temp_data = obj.trade_general_time
        return time.strftime('%Y-%m-%d %H:%m', time.localtime(temp_data)) if temp_data > 0 else 0

    trade_general_time_name.allow_tags = True
    trade_general_time_name.short_description = "订单生成"

    def order_deal_time_name(self, obj):
        temp_data = obj.order_deal_time
        return time.strftime('%Y-%m-%d %H:%m', time.localtime(temp_data)) if temp_data > 0 else 0

    order_deal_time_name.allow_tags = True
    order_deal_time_name.short_description = "订货时间"

    def goods_arrival_time_name(self, obj):
        temp_data = obj.goods_arrival_time
        return time.strftime('%Y-%m-%d %H:%m', time.localtime(temp_data)) if temp_data > 0 else 0

    goods_arrival_time_name.allow_tags = True
    goods_arrival_time_name.short_description = "到货时间"

    def goods_out_time_name(self, obj):
        temp_data = obj.goods_out_time
        return time.strftime('%Y-%m-%d %H:%m', time.localtime(temp_data)) if temp_data > 0 else 0

    goods_out_time_name.allow_tags = True
    goods_out_time_name.short_description = "出货时间"


admin.site.register(SupplyChainStatsOrder, SupplyChainStatsOrderAdmin)


class DailySupplyChainStatsOrderAdmin(admin.ModelAdmin):
    list_display = (
        'product_id', 'sale_time', 'trade_general_time', 'order_deal_time', 'goods_arrival_time', 'goods_out_time',
        'ding_huo_num', 'sale_num', 'cost_of_product', 'sale_cost_of_product', 'return_num', 'inferior_num')
    search_fields = ['product_id']


admin.site.register(DailySupplyChainStatsOrder, DailySupplyChainStatsOrderAdmin)


class ProductSkuDetailAdmin(admin.ModelAdmin):
    list_display = (
        'product_sku', 'exist_stock_num', 'created')


admin.site.register(ProductSkuDetail, ProductSkuDetailAdmin)
from flashsale.dinghuo.models_stats import RecordGroupPoint


class RecordGroupPointAdmin(admin.ModelAdmin):
    list_display = (
        'group_name', 'point_type', 'point_content', 'get_point', 'record_time')
    search_fields = ['point_content']
    list_filter = ['group_name', ('record_time', DateFieldListFilter), 'point_type']

    def queryset(self, request):
        qs = super(RecordGroupPointAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.exclude(get_point='0')


admin.site.register(RecordGroupPoint, RecordGroupPointAdmin)