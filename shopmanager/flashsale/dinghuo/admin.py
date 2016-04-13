# -*- coding:utf-8 -*-
from django.contrib import admin
from django.contrib.auth.models import User
from flashsale.dinghuo.models import OrderList, OrderDetail, orderdraft, ProductSkuDetail, ReturnGoods, RGDetail
from django.http import HttpResponseRedirect

from core.options import log_action, CHANGE
from flashsale.dinghuo.filters import DateFieldListFilter
from flashsale.dinghuo.models_user import MyUser, MyGroup
from flashsale.dinghuo.models_stats import SupplyChainDataStats, SupplyChainStatsOrder, DailySupplyChainStatsOrder, \
    PayToPackStats
import time
from .filters import GroupNameFilter, OrderListStatusFilter, OrderListStatusFilter2, BuyerNameFilter
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
        'fields': ('express_company', 'express_no', 'status', 'order_amount', 'note', 'p_district')
    }),)
    inlines = [orderdetailInline]

    list_display = (
        'id', 'buyer_select', 'order_amount', 'calcu_item_sum_amount', 'quantity', 'calcu_model_num', 'express_no',
        'created', 'shenhe', 'is_postpay', 'pay_status',
        'changedetail', 'note_name', 'supplier', 'p_district', 'reach_standard', 'updated', 'last_pay_date',
        'created_by'
    )
    list_filter = (('created', DateFieldListFilter), 'is_postpay', OrderListStatusFilter, 'pay_status', BuyerNameFilter,
                   'last_pay_date', 'created_by')
    search_fields = ['id', 'supplier__supplier_name', 'supplier_shop', 'express_no', 'note']
    date_hierarchy = 'created'

    list_per_page = 25

    def queryset(self, request):
        qs = super(ordelistAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.exclude(status='作废')

    def buyer_select(self, obj):
        part = ['<select class="buyer-select" orderlist-id="%d" onchange="buyer_select(this)">' % obj.id]
        part.append('<option value="0">-------------</option>')

        for user in User.objects.filter(is_staff=True,
                                        groups__name__in=(u'小鹿买手资料员', u'小鹿采购管理员', u'小鹿采购员', u'管理员', u'小鹿管理员')). \
                distinct().order_by('id'):
            username = '%s%s' % (user.last_name, user.first_name)
            username = username or user.username
            if user.id == obj.buyer_id:
                part.append('<option value="%d" selected>%s</option>' % (user.id, username))
            else:
                part.append('<option value="%d">%s</option>' % (user.id, username))
        part.append('</select>')
        return ''.join(part)

    buyer_select.allow_tags = True
    buyer_select.short_description = '负责人'

    def calcu_item_sum_amount(self, obj):
        amount = 0
        details = obj.order_list.all()
        for detail in details:
            pro = Product.objects.get(id=detail.product_id)
            amount += detail.buy_quantity * pro.cost
        return amount

    calcu_item_sum_amount.allow_tags = True
    calcu_item_sum_amount.short_description = "录入价"

    def calcu_model_num(self, obj):
        """计算显示款式数量"""
        dics = obj.order_list.all().values('outer_id').distinct()
        se = set()
        for i in dics:
            se.add(i['outer_id'][0:11]) if len(i['outer_id']) > 11 else se.add(i['outer_id'])
        return len(se)

    calcu_model_num.allow_tags = True
    calcu_model_num.short_description = "款数"

    def quantity(self, obj):
        alldetails = OrderDetail.objects.filter(orderlist_id=obj.id)
        quantityofoneorder = 0
        for detail in alldetails:
            quantityofoneorder += detail.buy_quantity
        return '{0}'.format(quantityofoneorder)

    quantity.allow_tags = True
    quantity.short_description = "商品数量"

    def supply_chain(self, obj):
        return u'<div style="width: 150px;overflow: hidden;white-space: nowrap;text-overflow: ellipsis;"><a href="{0}" target="_blank" >{1}</a></div>'.format(
            obj.supplier_name,
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

    test_order_action.short_description = u"审核(已付款)"

    def verify_order_action(self, request, queryset):
        for p in queryset:
            if p.status != '审核':
                p.status = '审核'
                p.is_postpay = True
                p.save()
                log_action(request.user.id, p, CHANGE, u'审核订货单')
                self.message_user(request, u'已成功审核!')
        return HttpResponseRedirect(request.get_full_path())

    verify_order_action.short_description = u'审核(待支付)'

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

    def action_receive_money(self, request, queryset):
        for order in queryset:
            if order.pay_status != u'正常':
                order.pay_status = u'正常'
                order.save()
                log_action(request.user.id, order, CHANGE, u'已收款')
        return HttpResponseRedirect(request.get_full_path())

    action_receive_money.short_description = u'收款（批量）'

    actions = ['test_order_action', 'verify_order_action', 'action_quick_complete', 'action_receive_money']

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
        js = ("https://cdn.bootcss.com/lightbox2/2.7.1/js/lightbox.js",
              "layer-v1.9.2/layer/layer.js", "layer-v1.9.2/layer/extend/layer.ext.js", "js/admin_js.js",
              "js/dinghuo_orderlist.js")


class OrderListChangeList(ChangeList):
    def get_queryset(self, request):
        qs = self.root_queryset
        search_q = request.GET.get('q', '').strip()
        if search_q.isdigit():
            trades = qs.filter(id=search_q)
            return trades
        return super(OrderListChangeList, self).get_queryset(request)


class orderdetailAdmin(admin.ModelAdmin):
    fieldsets = ((u'订单信息:', {
        'classes': ('expand',),
        'fields': (
            'product_id', 'outer_id', 'product_name', 'chichu_id', 'product_chicun', 'buy_quantity', 'arrival_quantity',
            'inferior_quantity', 'non_arrival_quantity')
    }),)

    list_display = (
        'id', 'link_order', 'product_id', 'outer_id', 'product_name', 'chichu_id', 'product_chicun', 'buy_quantity',
        'arrival_quantity', 'inferior_quantity', 'non_arrival_quantity', 'created', 'updated'
    )
    list_filter = (('created', DateFieldListFilter), OrderListStatusFilter2)
    search_fields = ['id', 'orderlist__id', 'product_id', 'outer_id', 'chichu_id']
    date_hierarchy = 'created'

    def link_order(self, obj):
        order_list = obj.orderlist.id
        link_str = u"<a href='/sale/dinghuo/changedetail/{0}/' target='_blank'>{1}</a>".format(order_list,
                                                                                               obj.orderlist.__unicode__())
        return link_str

    link_order.allow_tags = True
    link_order.short_description = "订货单"

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


class PayToPackStatsAdmin(admin.ModelAdmin):
    list_display = ('pay_date', 'packed_sku_num', 'total_days', 'avg_post_days', 'updated')


admin.site.register(PayToPackStats, PayToPackStatsAdmin)


class SupplyChainDataStatsAdmin(admin.ModelAdmin):
    list_display = ('sale_quantity', 'cost_amount', 'turnover',
                    'order_goods_quantity', 'order_goods_amount',
                    'stats_time', 'group',
                    'created', 'updated')
    list_filter = ('group', 'created',)
    search_fields = ['group']
    ordering = ('-stats_time',)


admin.site.register(SupplyChainDataStats, SupplyChainDataStatsAdmin)
from flashsale.dinghuo.models_stats import DailyStatsPreview


class DailyStatsPreviewAdmin(admin.ModelAdmin):
    list_display = ('sale_time', 'shelf_num', 'sale_num', "time_to_day",
                    'return_num', 'cost_of_product', 'sale_money', 'return_money')
    list_filter = ('created',)


admin.site.register(DailyStatsPreview, DailyStatsPreviewAdmin)


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
        'ding_huo_num', 'fahuo_num', 'sale_num', 'cost_of_product', 'sale_cost_of_product', 'return_num', 'return_pro',
        'inferior_num')
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


class RGDetailInline(admin.TabularInline):
    model = RGDetail
    fields = ("skuid", "return_goods", "num", "inferior_num", "price")


from shopback.items.models import Product
from supplychain.supplier.models import SaleSupplier
from flashsale.pay.models import SaleRefund


class ReturnGoodsAdmin(admin.ModelAdmin):
    list_display = ('id', "show_pic", "show_detail_num", "deal_sum_amount", "status_contrl",
                    "consign_time", "sid", "noter", "consigner", 'show_memo', 'show_reason')
    search_fields = ['id', "product_id", "supplier_id",
                     "noter", "consigner", "sid"]
    list_filter = ["noter", "consigner", "created", "modify", "status"]
    readonly_fields = ('status',)
    inlines = [RGDetailInline, ]
    list_display_links = ['show_detail_num', ]
    list_per_page = 10

    def queryset(self, request):
        qs = super(ReturnGoodsAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.exclude(status=ReturnGoods.OBSOLETE_RG)

    def show_pic(self, obj):
        product_id = obj.product_id
        pro = Product.objects.get(id=product_id)
        try:
            suplier = SaleSupplier.objects.get(id=obj.supplier_id)
            supplier_name = suplier.supplier_name
            mobile = suplier.mobile
            address = suplier.address
        except SaleSupplier.DoesNotExist:
            supplier_name = u"none"
            mobile = u"none"
            address = u"none"
        js_str = u"'%s','%s','%s'" % (
            supplier_name or u"none", mobile or u"none", address or u"none")
        html = u'<img src="{0}" style="width:62px;height:100px"><a style="display:inline" onclick="supplier_admin({4})">供应商：{3}</a>' \
               u'<br><a target="_blank" href="/admin/items/product/?id={2}">{1}</a>'.format(pro.pic_path, pro.name,
                                                                                            product_id,
                                                                                            obj.supplier_id, js_str)
        return html

    show_pic.allow_tags = True
    show_pic.short_description = u"产品图/名"

    def show_reason(self, obj):
        html = u''
        refs = SaleRefund.objects.filter(item_id=obj.product_id, good_status__in=(SaleRefund.BUYER_RECEIVED,
                                                                                  SaleRefund.BUYER_RETURNED_GOODS))
        if refs.count() >= 10:  # 最多显示10 个退货描述
            refs = refs[:10]
        for ref in refs:
            html += u'<br>' + ref.desc
        return html

    show_reason.allow_tags = True
    show_reason.short_description = u"原因"

    def show_detail_num(self, obj):
        dts = obj.rg_details.all()
        html = u'总：{0}<br><br>'.format(obj.return_num)
        for dt in dts:
            skuid = dt.skuid
            num = dt.num
            inferior_num = dt.inferior_num
            sub_html = u'{0} :{1} / {2}<br><br>'.format(skuid, num, inferior_num)
            html = html + sub_html
        return html

    show_detail_num.allow_tags = True
    show_detail_num.short_description = u"数量信息"

    def deal_sum_amount(self, obj):
        html = u'<a onclick="change_sum_price({0},{2})">{1}</a>'.format(obj.id, obj.sum_amount, obj.return_num)
        return html

    deal_sum_amount.allow_tags = True
    deal_sum_amount.short_description = u"退款总金额"

    def status_contrl(self, obj):
        cu_status = obj.get_status_display()
        if obj.status == ReturnGoods.CREATE_RG:
            # 如果是创建状态则　显示　审核通过　作废退货　两个按钮
            html = u'{1}-点击-><a cid="{0}" onclick="verify_ok(this)" style="margin-right:20px;">审核通过</a>　<br><br>或　' \
                   u'<a cid="{0}" onclick="verify_no(this)">作废退货</a>'.format(obj.id, cu_status)
            return html
        elif obj.status == ReturnGoods.VERIFY_RG:
            # 如果是审核通过　　显示　已经发货退货单的按钮
            html = u'{1}-点击-><a cid="{0}" onclick="already_send(this)">已经发货</a>'.format(obj.id, cu_status)
            return html
        elif obj.status == ReturnGoods.DELIVER_RG:
            # 如果是已经发货　　显示　退货成功　退货失败　两个按钮
            html = u'{1}-点击-><a cid="{0}" onclick="send_ok(this)" style="margin-right:20px;">退货成功</a>　<br><br>或　' \
                   u'<a cid="{0}" onclick="send_fail(this)">退货失败</a>'.format(obj.id, cu_status)
            return html
        else:
            return obj.get_status_display()

    status_contrl.allow_tags = True
    status_contrl.short_description = u"退货状态控制"

    def show_memo(self, obj):
        memo = u'{0}'.format(str(obj.memo).replace('\r', '<br><br>'))
        return memo

    show_memo.allow_tags = True
    show_memo.short_description = u"备注信息"

    class Media:
        css = {"all": (
        "css/admin_css.css", "css/return_goods.css", "https://cdn.bootcss.com/lightbox2/2.7.1/css/lightbox.css",
        )}
        js = ("js/tuihuo_ctrl.js", "https://cdn.bootcss.com/lightbox2/2.7.1/js/lightbox.js",
              "layer-v1.9.2/layer/layer.js", "layer-v1.9.2/layer/extend/layer.ext.js")


admin.site.register(ReturnGoods, ReturnGoodsAdmin)

from .models import SaleInventoryStat


class SaleInventoryStatAdmin(admin.ModelAdmin):
    list_display = ('stat_date', 'newly_increased', 'not_arrive', 'arrived', 'deliver', 'inventory')
    list_filter = ('category',)


admin.site.register(SaleInventoryStat, SaleInventoryStatAdmin)

from .models import InBound, InBoundDetail, OrderDetailInBoundDetail


class InBoundAdmin(admin.ModelAdmin):
    fieldsets = ((
        u'详情', {
            'classes': ('expand', ),
            'fields': ('express_no', 'sent_from', 'memo')
        }
    ), )

    list_display = ('id', 'show_id', 'supplier', 'express_no', 'sent_from',
                    'show_images', 'memo', 'show_orderlists', 'created', 'modified', 'status')

    list_filter = ('status', 'created')

    def show_id(self, obj):
        return '<a href="/sale/dinghuo/dinghuo_orderlist/list_for_inbound?inbound_id=%(id)d" target="_blank">详情</a>' % {'id': obj.id}
    show_id.allow_tags = True
    show_id.short_description = u'详情'

    def show_orderlists(self, obj):
        tmp = []
        for orderlist_id in obj.orderlist_ids:
            tmp.append('<a href="/sale/dinghuo/changedetail/%(id)d/">%(id)d</a>' % {'id': orderlist_id})
        return ''.join(tmp)

    show_orderlists.allow_tags = True
    show_orderlists.short_description = u'关联订货单'

    def show_images(self, obj):
        tpl = """
        <a href="%(url)s" target="_blank">
        <img src="%(url)s?imageMogr2/thumbnail/160/crop/160x160/format/jpg" style="width:100px;height:100px">
        </a>
        """
        images = []
        for url in obj.images:
            images.append(tpl % {'url': url})
        return ''.join(images)

    show_images.allow_tags = True
    show_images.short_description = u'图片'


class InBoundDetailAdmin(admin.ModelAdmin):
    fieldsets = ((
        u'详情', {
            'classes': ('expand', ),
            'fields': ('product_name', 'properties_name', 'arrival_quantity', 'inferior_quantity', 'status')
        }
    ), )
    list_display = ('id', 'show_inbound', 'product', 'sku', 'product_name', 'properties_name', 'arrival_quantity', 'inferior_quantity', 'created', 'modified', 'status')
    def show_inbound(self, obj):
        return '<a href="/sale/dinghuo/dinghuo_orderlist/list_for_inbound?inbound_id=%(id)d" target="_blank">%(id)d</a>' % {
            'id': obj.inbound_id}

    show_inbound.allow_tags = True
    show_inbound.short_description = u'入仓单ID'


class OrderDetailInBoundDetailAdmin(admin.ModelAdmin):
    list_display = (
    'show_orderdetail', 'show_inbounddetail', 'arrival_quantity', 'inferior_quantity', 'created', 'status')

    def show_orderdetail(self, obj):
        return '<a href="/admin/dinghuo/orderdetail/?id=%(id)d" target="_blank">%(id)d</a>' % {'id': obj.orderdetail_id}

    show_orderdetail.allow_tags = True
    show_orderdetail.short_description = u'订货明细ID'

    def show_inbounddetail(self, obj):
        return '<a href="/admin/dinghuo/inbounddetail/?id=%(id)d" target="_blank">%(id)d</a>' % {
            'id': obj.inbounddetail_id}

    show_inbounddetail.allow_tags = True
    show_inbounddetail.short_description = u'入仓明细ID'


admin.site.register(InBound, InBoundAdmin)
admin.site.register(InBoundDetail, InBoundDetailAdmin)
admin.site.register(OrderDetailInBoundDetail, OrderDetailInBoundDetailAdmin)
