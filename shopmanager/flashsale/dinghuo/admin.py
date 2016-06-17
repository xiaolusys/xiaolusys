# -*- coding:utf-8 -*-
from django.contrib import admin
from django.contrib.auth.models import User
from flashsale.dinghuo.models import OrderList, OrderDetail, orderdraft, ProductSkuDetail, ReturnGoods, RGDetail, UnReturnSku
from django.http import HttpResponseRedirect
from functools import partial, reduce, update_wrapper
from core.options import log_action, CHANGE
from core.admin import BaseModelAdmin
from flashsale.dinghuo.filters import DateFieldListFilter
from flashsale.dinghuo.models_user import MyUser, MyGroup
from flashsale.dinghuo.models_stats import SupplyChainDataStats, SupplyChainStatsOrder, DailySupplyChainStatsOrder, \
    PayToPackStats
import time
from .filters import GroupNameFilter, OrderListStatusFilter, OrderListStatusFilter2, BuyerNameFilter, InBoundCreatorFilter
from flashsale.dinghuo import permissions as perms
from django.contrib.admin.views.main import ChangeList

from django.db import models
import re

import copy
import operator
import warnings
from collections import OrderedDict
from functools import partial, reduce, update_wrapper

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin import helpers, validation, widgets
from django.contrib.admin.checks import (
    BaseModelAdminChecks, InlineModelAdminChecks, ModelAdminChecks,
)
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.admin.utils import (
    NestedObjects, flatten_fieldsets, get_deleted_objects,
    lookup_needs_distinct, model_format_dict, quote, unquote,
)
from django.contrib.auth import get_permission_codename
from django.core import checks
from django.core.exceptions import (
    FieldDoesNotExist, FieldError, ImproperlyConfigured, PermissionDenied,
    ValidationError,
)
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import models, router, transaction
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields import BLANK_CHOICE_DASH
from django.db.models.fields.related import ForeignObjectRel
from django.db.models.sql.constants import QUERY_TERMS
from django.forms.formsets import DELETION_FIELD_NAME, all_valid
from django.forms.models import (
    BaseInlineFormSet, inlineformset_factory, modelform_defines_fields,
    modelform_factory, modelformset_factory,
)
from django.forms.widgets import CheckboxSelectMultiple, SelectMultiple
from django.http import Http404, HttpResponseRedirect
from django.http.response import HttpResponseBase
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.utils import six
from django.utils.decorators import method_decorator
from django.utils.deprecation import RemovedInDjango19Warning
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.html import escape, escapejs
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.text import capfirst, get_text_list
from django.utils.translation import string_concat, ugettext as _, ungettext
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.options import IncorrectLookupParameters
IS_POPUP_VAR = '_popup'
TO_FIELD_VAR = '_to_field'


HORIZONTAL, VERTICAL = 1, 2



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
        'id', 'buyer_select', 'order_amount', 'calcu_item_sum_amount', 'quantity', 'calcu_model_num',
        'created', 'shenhe', 'is_postpay',
        'changedetail', 'note_name', 'supplier', 'express_no', 'p_district', 'reach_standard', 'updated', 'last_pay_date',
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


class ReturnGoodsAdmin(BaseModelAdmin):
    list_display = ('id_link', "supplier_link","show_detail_num", "sum_amount",
                    "status", "status_contrl", "noter",  "transactor_name", "created",
                    "consign_time", "sid",  "consigner", 'show_memo', 'show_reason'
                    )
    search_fields = ['id', "supplier__id", "supplier__supplier_name", "transaction_number",
                     "noter", "consigner", "transactor_id", "sid"]

    list_filter = ["status", "noter", "consigner", "transactor_id",
                   ("created", DateFieldListFilter), ("modify", DateFieldListFilter)]
    readonly_fields = ('status', 'supplier')
    inlines = [RGDetailInline, ]
    list_display_links = []
    list_select_related = True
    list_per_page = 25
    # change_form_template = "admin/dinghuo/returngoods/change_form.html"
    def lookup_allowed(self, lookup, value):
        if lookup in ['supplier__supplier_name']:
            return True
        return super(ReturnGoodsAdmin, self).lookup_allowed(lookup, value)

    def id_link(self, obj):
        return ('<a href="%(url)s" target="_blank">'
                '%(show_text)s</a>') % {
                'url': '/admin/dinghuo/returngoods/%d/' % obj.id,
                'show_text': str(obj.id)
            }
    id_link.allow_tags = True
    id_link.short_description = u"ID"

    def detail_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = {'title': u'仓库退货单', 'transactors': ReturnGoods.transactors()}
        return self.detailform_view(request, object_id, form_url, extra_context)


    # def change_view(self, request, object_id, form_url='', extra_context=None):
    #     extra_context = {'title': u'仓库退货单', 'transactors': ReturnGoods.transactors()}
    #     return self.changeform_view(request, object_id, form_url, extra_context)

    def transactor_name(self, obj):
        return obj.transactor.username
    transactor_name.short_description = u"负责人"


    def supplier_link(self, obj):
        if not obj.supplier:
            return ''

        return ('<a href="%(url)s" target="_blank">'
                '%(show_text)s</a>') % {
                'url': '/admin/supplier/salesupplier/%d/' % obj.supplier_id,
                'show_text': obj.supplier.supplier_name
            }
    supplier_link.allow_tags = True
    supplier_link.short_description = u"供应商"

    def product_desc(self, obj):
        return '<br/>'.join([p.title() for p in obj.products])
    # def show_pic(self, obj):
    #     product_id = obj.product_id
    #     pro = Product.objects.get(id=product_id)
    #     try:
    #         suplier = SaleSupplier.objects.get(id=obj.supplier_id)
    #         supplier_name = suplier.supplier_name
    #         mobile = suplier.mobile
    #         address = suplier.address
    #     except SaleSupplier.DoesNotExist:
    #         supplier_name = u"none"
    #         mobile = u"none"
    #         address = u"none"
    #     js_str = u"'%s','%s','%s'" % (
    #         supplier_name or u"none", mobile or u"none", address or u"none")
    #     html = u'<img src="{0}" style="width:62px;height:100px"><a style="display:inline" onclick="supplier_admin({4})">供应商：{3}</a>' \
    #            u'<br><a target="_blank" href="/admin/items/product/?id={2}">{1}</a>'.format(pro.pic_path, pro.name,
    #                                                                                         product_id,
    #                                                                                         obj.supplier_id, js_str)
    #     return html

    product_desc.allow_tags = True
    product_desc.short_description = u"包含商品"

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
        print "nmb"
        return_num = 0
        dts = obj.rg_details.all()
        html = ''
        for dt in dts:
            skuid = dt.skuid
            num = dt.num
            return_num = return_num + num
            price = dt.price
            # sub_html = u'{0}  {1} - {2}<br>'.format(skuid, return_num, price)
            # html = html + sub_html
        html = u'{0}<br>'.format(return_num)
        return html

    show_detail_num.allow_tags = True
    show_detail_num.short_description = u"退货数量"

    # def deal_sum_amount(self, obj):
    #     html = u'<a onclick="change_sum_price({0},{2})">{1}</a>'.format(obj.id, obj.sum_amount, obj.return_num)
    #     return html
    #
    # deal_sum_amount.allow_tags = True
    # deal_sum_amount.short_description = u"退款总额"

    def status_contrl(self, obj):
        if obj.status == ReturnGoods.CREATE_RG:
            # 如果是创建状态则　显示　审核通过　作废退货　两个按钮
            html = u'<a cid="{0}" onclick="verify_ok(this)" style="margin-right:0px;">审核通过</a><br/>' \
                   u'<a cid="{0}" onclick="verify_no(this)">作废退货</a>'.format(obj.id,)
            return html
        elif obj.status == ReturnGoods.DELIVER_RG:
            # 如果是已经发货　　显示　退货成功　退货失败　两个按钮
            html = u'<a cid="{0}" onclick="send_ok(this)" style="margin-right:0px;">退货成功</a><br/>' \
                   u'<a cid="{0}" onclick="send_fail(this)">退货失败</a>'.format(obj.id,)
            return html
        else:
            return obj.get_status_display()

    status_contrl.allow_tags = True
    status_contrl.short_description = u"操作"

    def show_memo(self, obj):
        memo = u'{0}'.format(str(obj.memo).replace('\r', '<br><br>'))
        return memo

    show_memo.allow_tags = True
    show_memo.short_description = u"备注信息"

    def lookup_allowed(self, lookup, value):
        if lookup in ['rg_details__skuid']:
            return True
        return super(ReturnGoodsAdmin, self).lookup_allowed(lookup, value)

    def changelist_view(self, request, extra_context=None):
        """
        The 'change list' admin view for this model.
        """
        from django.contrib.admin.views.main import ERROR_FLAG
        opts = self.model._meta
        app_label = opts.app_label
        if not self.has_change_permission(request, None):
            raise PermissionDenied

        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)
        list_filter = self.get_list_filter(request)
        search_fields = self.get_search_fields(request)

        # Check actions to see if any are available on this changelist
        actions = self.get_actions(request)
        if actions:
            # Add the action checkboxes if there are any actions available.
            list_display = ['action_checkbox'] + list(list_display)

        ChangeList = self.get_changelist(request)
        try:
            cl = ChangeList(request, self.model, list_display,
                list_display_links, list_filter, self.date_hierarchy,
                search_fields, self.list_select_related, self.list_per_page,
                self.list_max_show_all, self.list_editable, self)

        except IncorrectLookupParameters:
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given
            # and the 'invalid=1' parameter was already in the query string,
            # something is screwed up with the database, so display an error
            # page.
            if ERROR_FLAG in request.GET.keys():
                return SimpleTemplateResponse('admin/invalid_setup.html', {
                    'title': _('Database error'),
                })
            return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

        # If the request was POSTed, this might be a bulk action or a bulk
        # edit. Try to look up an action or confirmation first, but if this
        # isn't an action the POST will fall through to the bulk edit check,
        # below.
        action_failed = False
        selected = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)

        # Actions with no confirmation
        if (actions and request.method == 'POST' and
                'index' in request.POST and '_save' not in request.POST):
            if selected:
                response = self.response_action(request, queryset=cl.get_queryset(request))
                if response:
                    return response
                else:
                    action_failed = True
            else:
                msg = _("Items must be selected in order to perform "
                        "actions on them. No items have been changed.")
                self.message_user(request, msg, messages.WARNING)
                action_failed = True

        # Actions with confirmation
        if (actions and request.method == 'POST' and
                helpers.ACTION_CHECKBOX_NAME in request.POST and
                'index' not in request.POST and '_save' not in request.POST):
            if selected:
                response = self.response_action(request, queryset=cl.get_queryset(request))
                if response:
                    return response
                else:
                    action_failed = True

        # If we're allowing changelist editing, we need to construct a formset
        # for the changelist given all the fields to be edited. Then we'll
        # use the formset to validate/process POSTed data.
        formset = cl.formset = None

        # Handle POSTed bulk-edit data.
        if (request.method == "POST" and cl.list_editable and
                '_save' in request.POST and not action_failed):
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(request.POST, request.FILES, queryset=cl.result_list)
            if formset.is_valid():
                changecount = 0
                for form in formset.forms:
                    if form.has_changed():
                        obj = self.save_form(request, form, change=True)
                        self.save_model(request, obj, form, change=True)
                        self.save_related(request, form, formsets=[], change=True)
                        change_msg = self.construct_change_message(request, form, None)
                        self.log_change(request, obj, change_msg)
                        changecount += 1

                if changecount:
                    if changecount == 1:
                        name = force_text(opts.verbose_name)
                    else:
                        name = force_text(opts.verbose_name_plural)
                    msg = ungettext("%(count)s %(name)s was changed successfully.",
                                    "%(count)s %(name)s were changed successfully.",
                                    changecount) % {'count': changecount,
                                                    'name': name,
                                                    'obj': force_text(obj)}
                    self.message_user(request, msg, messages.SUCCESS)

                return HttpResponseRedirect(request.get_full_path())

        # Handle GET -- construct a formset for display.
        elif cl.list_editable:
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(queryset=cl.result_list)

        # Build the list of media to be used by the formset.
        if formset:
            media = self.media + formset.media
        else:
            media = self.media

        # Build the action form and populate it with available actions.
        if actions:
            action_form = self.action_form(auto_id=None)
            action_form.fields['action'].choices = self.get_action_choices(request)
        else:
            action_form = None

        selection_note_all = ungettext('%(total_count)s selected',
            'All %(total_count)s selected', cl.result_count)

        context = dict(
            self.admin_site.each_context(request),
            module_name=force_text(opts.verbose_name_plural),
            selection_note=_('0 of %(cnt)s selected') % {'cnt': len(cl.result_list)},
            selection_note_all=selection_note_all % {'total_count': cl.result_count},
            title=cl.title,
            is_popup=cl.is_popup,
            to_field=cl.to_field,
            cl=cl,
            media=media,
            has_add_permission=self.has_add_permission(request),
            opts=cl.opts,
            action_form=action_form,
            actions_on_top=self.actions_on_top,
            actions_on_bottom=self.actions_on_bottom,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
            users=User.objects.filter(groups__id=5)
        )
        context.update(extra_context or {})

        request.current_app = self.admin_site.name

        return TemplateResponse(request, self.change_list_template or [
            'admin/%s/%s/change_list.html' % (app_label, opts.model_name),
            'admin/%s/change_list.html' % app_label,
            'admin/change_list.html'
        ], context)


    class Meta:
        # related_fkey_lookups = ['rg_details__skuid']
        css = {"all": (
        "css/admin_css.css", "css/return_goods.css", "https://cdn.bootcss.com/lightbox2/2.7.1/css/lightbox.css",
        )}
        js = ("js/tuihuo_ctrl.js", "https://cdn.bootcss.com/lightbox2/2.7.1/js/lightbox.js",
              "layer-v1.9.2/layer/layer.js", "layer-v1.9.2/layer/extend/layer.ext.js")


admin.site.register(ReturnGoods, ReturnGoodsAdmin)

class UnReturnSkuAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_outer_id', "product_name", "sku_properties_name", "supplier_sku", "supplier_name", "reason", "creater_name",
                    "created", "modified", "status")
    search_fields = ['product__name', "supplier__id", "supplier__supplier_name", "product__id",
                     "sku__id"]
    list_filter = ["status", "reason"]
    readonly_fields = ('product', 'sale_product', 'sku', 'supplier', 'creater')
    #inlines = [RGDetailInline, ]
    #list_display_links = ['id',]
    #list_select_related = True
    list_per_page = 50

    def product_outer_id(self, obj):
        return '<a href="/admin/items/product/?outer_id=%(outer_id)s">%(outer_id)s</a>' % {'outer_id': obj.product.outer_id}
    product_outer_id.short_description = '商品编码'
    product_outer_id.allow_tags = True

    def product_name(self, obj):
        return obj.product.name;
    product_name.short_description = '商品名称'

    def sku_properties_name(self, obj):
        return '<a href="/admin/items/productskustats/?sku_id=%(sku_id)d">%(properties_name)s</a>' % {
            'sku_id': obj.sku.id,
            'properties_name': obj.sku.properties_name or obj.sku.properties_alias or ''
        }
    sku_properties_name.allow_tags = True
    sku_properties_name.short_description = '规格'

    def supplier_sku(self, obj):
        return obj.sale_product.supplier_sku
    supplier_sku.short_description = '货号'

    def supplier_name(self, obj):
        return obj.supplier.supplier_name
    supplier_name.short_description = '供应商名称'

    def creater_name(self, obj):
        user = obj.creater
        last_name = user.last_name
        first_name = user.first_name
        if len(last_name) > 1:
            names = [first_name, last_name]
        else:
            names = [last_name, first_name]
        return ''.join(filter(None, names)) or user.username
    creater_name.short_description = '创建人'

    def lookup_allowed(self, lookup, value):
        if lookup in ['product___name', 'sale_product__name', 'supplier__supplier_name', 'sku__id']:
            return True
        return super(UnReturnSkuAdmin, self).lookup_allowed(lookup, value)
admin.site.register(UnReturnSku, UnReturnSkuAdmin)


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

    list_display = ('id', 'show_id', 'show_creator', 'supplier', 'express_no',
                    'memo', 'show_orderlists', 'created', 'modified', 'status')

    list_filter = ('status', 'created', InBoundCreatorFilter)

    search_fields = ('supplier__supplier_name', 'express_no')

    def show_creator(self, obj):
        from flashsale.dinghuo.views import InBoundViewSet
        return InBoundViewSet.get_username(obj.creator)
    show_creator.short_description = u'创建人'

    def show_id(self, obj):
        return '<a href="/sale/dinghuo/inbound/%(id)d" target="_blank">详情</a>' % {'id': obj.id}
    show_id.allow_tags = True
    show_id.short_description = u'详情'

    def show_orderlists(self, obj):
        tmp = []
        for orderlist_id in sorted(obj.orderlist_ids):
            tmp.append('<a href="/sale/dinghuo/changedetail/%(id)d/" target="_blank">%(id)d</a>' % {'id': int(orderlist_id)})
        return ','.join(tmp)
    show_orderlists.allow_tags = True
    show_orderlists.short_description = u'关联订货单'


class InBoundDetailAdmin(admin.ModelAdmin):
    fieldsets = ((
        u'详情', {
            'classes': ('expand', ),
            'fields': ('product_name', 'properties_name', 'arrival_quantity', 'inferior_quantity', 'status')
        }
    ), )
    list_display = ('id', 'show_inbound', 'product', 'sku', 'product_name', 'properties_name', 'arrival_quantity', 'inferior_quantity', 'created', 'modified', 'status')
    def show_inbound(self, obj):
        return '<a href="/sale/dinghuo/inbound/%(id)d" target="_blank">%(id)d</a>' % {
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


from flashsale.dinghuo.models_purchase import PurchaseRecord, PurchaseArrangement, PurchaseDetail, PurchaseOrder

class PurchaseRecordAdmin(admin.ModelAdmin):
   list_display = ('id', 'package_sku_item_id', 'oid', 'outer_id', 'outer_sku_id', 'sku_id', 'title',
                   'sku_properties_name', 'request_num', 'book_num', 'status', 'modified', 'created')
   search_fields = ('package_sku_item_id', 'oid', 'outer_id', 'title', 'sku_id')

admin.site.register(PurchaseRecord, PurchaseRecordAdmin)


class PurchaseArrangementAdmin(admin.ModelAdmin):
    list_display = ('id', 'package_sku_item_id', 'oid', 'purchase_order_unikey', 'outer_id', 'outer_sku_id', 'sku_id', 'title',
                    'sku_properties_name', 'num', 'status', 'purchase_order_status', 'initial_book', 'modified', 'created')


admin.site.register(PurchaseArrangement, PurchaseArrangementAdmin)


class PurchaseDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'outer_id', 'purchase_order_unikey', 'outer_sku_id', 'sku_id', 'title', 'sku_properties_name', 'book_num', 'need_num',
                    'extra_num', 'status', 'unit_price_display', 'modified', 'created')


admin.site.register(PurchaseDetail, PurchaseDetailAdmin)


class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'uni_key', 'supplier_id', 'supplier_name', 'book_num', 'need_num', 'arrival_num', 'status',
                    'modified', 'created')

admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
