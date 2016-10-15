# coding: utf-8
import json
import time
import datetime
import cStringIO as StringIO
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db import models
from django.views.decorators.csrf import csrf_protect
from django.forms import TextInput, Textarea, Select
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import force_unicode
from core.utils.modelutils import get_class_fields
from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple
from django.conf import settings
from celery import chord
from shopback.items.models import Product, ProductSku
from shopback.trades.models import (PackageOrder,
                                    PackageSkuItem,
                                    MergeTrade,
                                    MergeOrder,
                                    MergeBuyerTrade,
                                    ReplayPostTrade,
                                    MergeTradeDelivery)
from shopback import paramconfig as pcfg
from shopback.fenxiao.models import PurchaseOrder
from shopback.trades.tasks import sendTaobaoTradeTask, sendTradeCallBack
from shopback.trades import permissions as perms
from .forms import YundaCustomerForm
from shopback.trades.filters import (TradeStatusFilter,
                                     OrderPendingStatusFilter)
from core.filters import DateFieldListFilter
from shopback.trades.service import TradeService
from core.admin import ApproxAdmin
from core.options import log_action, User, ADDITION, CHANGE
from shopback.trades import permissions as perms
from common.utils import (gen_cvs_tuple,
                          update_model_fields,
                          CSVUnicodeWriter,
                          parse_datetime,
                          pinghost)
import logging

# fang  2015-8-19
import re   
from shopback.trades.models import TradeWuliu,ReturnWuLiu
from shopback.trades.tasks import send_package_task, send_package_call_Back

logger = logging.getLogger('django.request')

PHONE_RE = re.compile('^(1[0-9]{10}|([0-9]{3,4}-)?[0-9-]{6,8})$')

__author__ = 'meixqhi'


class MergeOrderInline(admin.TabularInline):
    model = MergeOrder
    fields = ('oid', 'outer_id', 'outer_sku_id', 'title', 'price', 'payment', 'num',
              'sku_properties_name', 'out_stock', 'is_merge', 'is_rule_match',
              'is_reverse_order', 'gift_type', 'refund_id', 'refund_status', 'sys_status')

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = set(self.readonly_fields + ('tid', 'oid'))
        if not perms.has_modify_trade_permission(request.user):
            readonly_fields.update(('outer_id', 'outer_sku_id', 'is_merge',
                                    'is_reverse_order', 'operator', 'gift_type'))
            return tuple(readonly_fields)
        return tuple(readonly_fields)

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '12'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 20})},
    }


class MergeTradeChangeList(ChangeList):
    def get_ordering(self, request, queryset):
        ordering = super(MergeTradeChangeList, self).get_ordering(request, queryset)
        ordering.remove('-pk')
        return ordering

    def get_queryset(self, request):

        qs = self.root_queryset
        # 如果查询条件中含有邀请码
        search_q = request.GET.get('q', '').strip()
        if search_q:
            (self.filter_specs, self.has_filters, remaining_lookup_params,
             use_distinct) = self.get_filters(request)

            for filter_spec in self.filter_specs:
                new_qs = filter_spec.queryset(request, qs)
                if new_qs is not None:
                    qs = new_qs
            # Set ordering.
            ordering = self.get_ordering(request, qs)
            qs = qs.order_by(*ordering)

        if PHONE_RE.match(search_q):
            trades = qs.filter(
                models.Q(id=search_q) | models.Q(receiver_mobile=search_q))  # |models.Q(receiver_phone=search_q)
            return trades

        if search_q.isdigit():
            trades = qs.filter(models.Q(id=search_q) | models.Q(tid=search_q) | models.Q(out_sid=search_q))
            return trades

        if re.compile('^wx[\d]{20,28}$').match(search_q):

            tid = search_q.replace('wx', '')
            try:
                from shopback.users.models import User as Shop
                shops = Shop.objects.filter(type=Shop.SHOP_TYPE_WX).exclude(uid='wxmiaosha')
                if shops.count() > 0:
                    TradeService.createTrade(shops[0].uid, tid, MergeTrade.WX_TYPE)
            except:
                pass
            return qs.filter(tid=tid)

        if search_q:
            tid_list = ['%s-%s' % (search_q, i) for i in range(1, 8)]
            tid_list.append(search_q)
            trades = qs.filter(models.Q(tid__in=tid_list) | models.Q(out_sid=search_q))
            return trades

        return super(MergeTradeChangeList, self).get_queryset(request)


class MergeTradeAdmin(ApproxAdmin):
    list_display = ('trade_id_link', 'popup_tid_link', 'buyer_nick_link', 'type',
                    'payment', 'pay_time', 'consign_time', 'trade_ding_huo', 'sys_status', 'status',
                    'reason_code', 'is_picking_print', 'is_express_print', 'can_review', 'ware_by', 'weight_time')
    # list_display_links = ('trade_id_link','popup_tid_link')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    change_list_template = "admin/trades/change_list.html"
    # change_form_template  = "admin/trades/change_trade_form.html"

    ordering = ['-sys_status']
    list_per_page = 50

    def trade_id_link(self, obj):

        link_content = u'''<a href="{0}/">{1}</a><a href="javascript:void(0);" class="trade-tag" style="display:block" trade_id="{2}" data-toggle="tooltip" data-placement="right" >
        备注</a>'''.format(obj.id, obj.id, obj.id)
        if obj.sys_status == pcfg.WAIT_AUDIT_STATUS:
            link_content += u'<a href="javascript:void(0);" class="trade-regular" style="display:block" trade_id="%d" days="3" >延三天</a>' % obj.id
        return link_content

    trade_id_link.allow_tags = True
    trade_id_link.short_description = "ID"

    def popup_tid_link(self, obj):
        return u'<a href="%d/" onclick="return showTradePopup(this);"    >%s</a>' % (
            obj.id, obj.tid and str(obj.tid) or '--')

    popup_tid_link.allow_tags = True
    popup_tid_link.short_description = u"原单ID"

    def buyer_nick_link(self, obj):
        symbol_link = obj.buyer_nick

        if obj.can_change_order:
            symbol_link = u'<a href="javascript:void(0);" onclick=" showlayer(%d)">%s</a> ' % (obj.id, obj.buyer_nick)
        return symbol_link

    buyer_nick_link.allow_tags = True
    buyer_nick_link.short_description = u"买家昵称"

    def has_out_stock_fun(self, obj):
        has_out_stock = obj.has_out_stock  # 退货状态
        if has_out_stock:  # 表示缺货
            content = u'<select class="has_out_stock" cid="{0}" id="select_has_out_stock_{0} " style="width:70px" >' \
                      u"<option value='{4}' selected='selected'>{1}</option>" \
                      u"<option value='{3}'>{2}</option>" \
                      u'</select>'.format(obj.id, u'缺货', u'不缺货', 0, 1)
        else:
            content = u'<select class="has_out_stock" cid="{0}" id="select_has_out_stock_{0} " style="width:70px" >' \
                      u"<option value='{3}' selected='selected'>{2}</option>" \
                      u"<option value='{4}'>{1}</option>" \
                      u'</select>'.format(obj.id, u'缺货', u'不缺货', 0, 1)
            pass
        return content

    has_out_stock_fun.allow_tags = True
    has_out_stock_fun.short_description = u"是否缺货"

    def trade_ding_huo(self, obj):
        orders = obj.merge_orders.all()
        link_content = ""
        if orders.count() > 0:
            for one_order in orders:
                if one_order.sys_status == pcfg.IN_EFFECT:
                    link_content += "<a href='/admin/items/product/?q=" + one_order.outer_id + "' target='_blank'>" + one_order.outer_id + "</a><br>"
        return link_content

    trade_ding_huo.allow_tags = True
    trade_ding_huo.short_description = u"订货表"

    inlines = [MergeOrderInline]

    list_filter = (TradeStatusFilter, 'user', ('pay_time', DateFieldListFilter), 'type',
                   ('weight_time', DateFieldListFilter), 'ware_by',  # ('trade_from', BitFieldListFilter,),
                   'has_out_stock', 'has_rule_match', 'has_merge', 'has_sys_err', 'has_memo',
                   'is_picking_print', 'is_express_print', 'is_locked', 'is_charged', 'is_qrcode')

    search_fields = ['id', 'buyer_nick', 'tid', 'out_sid', 'receiver_mobile']

    class Media:
        css = {"all": ("admin/css/forms.css", "css/admin/dialog.css", "css/admin/checkorder.css")}
        #         js = ("jquery/jquery-1.8.13.min.js","script/admin/adminpopup.js","script/trades/new_checkTrade.js",
        #               "layer-v1.9.2/layer/layer.js","bootstrap/js/bootstrap.js","script/trades/select_stock.js",)
        js = ("closure-library/closure/goog/base.js", "script/admin/adminpopup.js", "script/base.js",
              "script/trades/checkorder.js",
              "script/trades/tradetags.js", "script/trades/new_checkTrade.js", "layer-v1.9.2/layer/layer.js",
              "bootstrap/js/bootstrap.js", "jquery/jquery-1.8.13.min.js", "script/trades/select_stock.js")

    form = YundaCustomerForm
    # --------设置页面布局----------------
    fieldsets = (('订单基本信息:', {
        'classes': ('collapse',),
        'fields': (('tid', 'user', 'type', 'status')
                   , ('buyer_nick', 'order_num', 'prod_num', 'trade_from')
                   , ('total_fee', 'payment', 'discount_fee', 'adjust_fee', 'post_fee')
                   , ('is_cod', 'seller_cod_fee', 'buyer_cod_fee', 'cod_fee', 'cod_status')
                   , ('is_brand_sale', 'is_force_wlb', 'buyer_rate', 'seller_rate', 'seller_can_rate'
                      , 'is_lgtype', 'lg_aging_type')
                   , ('send_time', 'lg_aging', 'step_paid_fee', 'step_trade_status')
                   , ('created', 'pay_time', 'consign_time')
                   , ('buyer_message', 'seller_memo', 'sys_memo')
                   )
    }),
                 ('收货人及物流信息:', {
                     'classes': ('expand',),
                     'fields': (('receiver_name', 'receiver_state', 'receiver_city', 'receiver_district')
                                , ('receiver_address', 'receiver_zip', 'receiver_mobile', 'receiver_phone')
                                , ('shipping_type', 'logistics_company', 'out_sid'))
                 }),
                 ('系统内部信息:', {
                     'classes': ('collapse',),
                     'fields': (('has_sys_err', 'has_memo', 'has_refund', 'has_out_stock', 'has_rule_match', 'has_merge'
                                 , 'is_send_sms', 'is_picking_print', 'is_express_print', 'can_review', 'is_qrcode')
                                ,
                                ('is_locked', 'is_charged', 'is_part_consign', 'priority', 'reason_code', 'refund_num')
                                , ('remind_time', 'weight_time', 'charge_time')
                                , ('ware_by', 'operator', 'scanner', 'weighter', 'weight')
                                , ('reserveo', 'reservet', 'reserveh', 'sys_status'))
                 }))

    # --------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '16'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 35})},
        BitField: {'widget': BitFieldCheckboxSelectMultiple},
    }

    def formfield_for_dbfield(self, db_field, **kwargs):
        #         if db_field.name == 'logistics_company':
        #             logistic_list = LogisticsCompany.normal_companys().values_list('id','name')
        #             return db_field.formfield(widget = Select(choices=logistic_list))
        return super(MergeTradeAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = self.readonly_fields
        if not request.user.has_perm('trades.can_trade_modify'):
            readonly_fields = readonly_fields + ('tid', 'reason_code', 'has_rule_match', 'has_merge', 'has_memo',
                                                 'payment', 'post_fee', 'user', 'type', 'trade_from', 'is_locked',
                                                 'is_charged', 'operator', 'can_review', 'is_picking_print',
                                                 'is_express_print', 'buyer_message', 'seller_memo', 'sys_memo',
                                                 'sys_status', 'status')
            if obj.sys_status == pcfg.WAIT_PREPARE_SEND_STATUS:
                readonly_fields = readonly_fields + ('priority',)
        return readonly_fields

    def get_actions(self, request):

        user = request.user
        actions = super(MergeTradeAdmin, self).get_actions(request)

        if not perms.has_delete_trade_permission(user) and 'delete_selected' in actions:
            del actions['delete_selected']
        if not perms.has_sync_post_permission(user) and 'push_trade_to_scan' in actions:
            del actions['push_trade_to_scan']
        if not perms.has_merge_order_permission(user) and 'merge_order_action' in actions:
            del actions['merge_order_action']
        if not perms.has_pull_order_permission(user) and 'pull_order_action' in actions:
            del actions['pull_order_action']
        if not perms.has_unlock_trade_permission(user) and 'unlock_trade_action' in actions:
            del actions['unlock_trade_action']
        if not perms.has_invalid_order_permission(user) and 'invalid_trade_action' in actions:
            del actions['invalid_trade_action']
        if not perms.has_export_logistic_permission(user) and 'export_logistic_action' in actions:
            del actions['export_logistic_action']
        if not perms.has_export_finance_permission(user) and 'export_finance_action' in actions:
            del actions['export_finance_action']
        if not perms.has_export_buyer_permission(user) and 'export_buyer_action' in actions:
            del actions['export_buyer_action']
        if not perms.has_export_orderdetail_permission(user) and 'export_orderdetail_action' in actions:
            del actions['export_orderdetail_action']
        if not perms.has_export_yunda_permission(user) and 'export_yunda_action' in actions:
            del actions['export_yunda_action']
        return actions

    def change_view(self, request, extra_context=None, **kwargs):

        return super(MergeTradeAdmin, self).change_view(request, extra_context)

    def get_changelist(self, request, **kwargs):
        return MergeTradeChangeList

    # 重写订单视图
    def changelist_view(self, request, extra_context=None, **kwargs):

        return super(MergeTradeAdmin, self).changelist_view(request, extra_context)

    def response_change(self, request, obj, *args, **kwargs):
        # 订单处理页面
        opts = obj._meta
        # Handle proxy models automatically created by .only() or .defer()
        verbose_name = opts.verbose_name
        if obj._deferred:
            opts_ = opts.proxy_for_model._meta
            verbose_name = opts_.verbose_name

        pk_value = obj._get_pk_val()
        operate_success = False
        if request.POST.has_key("_save_audit"):
            if (obj.sys_status == pcfg.WAIT_AUDIT_STATUS
                and not obj.reason_code
                and not obj.has_rule_match
                and not obj.has_refund
                and not obj.has_out_stock
                and obj.logistics_company
                and not obj.has_reason_code(pcfg.MULTIPLE_ORDERS_CODE)):
                try:
                    MergeTrade.objects.filter(id=obj.id, reason_code=''
                                              ).update(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS)
                except Exception, exc:
                    logger.error(exc.message, exc_info=True)
                    operate_success = False
                else:
                    operate_success = True

            if operate_success:
                from shopapp.memorule import ruleMatchPayment

                ruleMatchPayment(obj)

                msg = u"审核通过"
                self.message_user(request, msg)
                log_action(request.user.id, obj, CHANGE, msg)

                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"审核未通过（请确保订单状态为问题单,无退款,无问题编码"
                                           u",无匹配,无缺货, 未合单,已选择快递）")
                return HttpResponseRedirect("../%s/" % pk_value)

        elif request.POST.has_key("_invalid"):
            if obj.sys_status in (pcfg.WAIT_AUDIT_STATUS,
                                  pcfg.WAIT_CHECK_BARCODE_STATUS,
                                  pcfg.WAIT_SCAN_WEIGHT_STATUS):

                # 作废前需拆分订单
                if obj.sys_status == pcfg.WAIT_AUDIT_STATUS:
                    MergeTrade.objects.mergeRemover(obj)

                try:
                    MergeTrade.objects.reduceWaitPostNum(obj)
                except:
                    pass
                obj.sys_status = pcfg.INVALID_STATUS
                obj.save()
                msg = u"订单已作废"
                self.message_user(request, msg)

                log_action(request.user.id, obj, CHANGE, msg)

                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"作废未成功（请确保订单状态为问题单）")
                return HttpResponseRedirect("../%s/" % pk_value)

        elif request.POST.has_key("_uninvalid"):
            if obj.sys_status == pcfg.INVALID_STATUS:
                if obj.status == pcfg.WAIT_BUYER_CONFIRM_GOODS:
                    obj.sys_status = pcfg.WAIT_CHECK_BARCODE_STATUS
                    msg = u"订单反作废入待扫描状态"

                    MergeTrade.objects.updateWaitPostNum(obj)

                elif obj.status == pcfg.TRADE_FINISHED:
                    obj.sys_status = pcfg.FINISHED_STATUS
                    msg = u"订单反作废入已完成"

                else:
                    obj.sys_status = pcfg.WAIT_AUDIT_STATUS
                    msg = u"订单反作废入问题单"

                    MergeTrade.objects.updateWaitPostNum(obj)

                obj.save()

                self.message_user(request, msg)
                log_action(request.user.id, obj, CHANGE, msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"订单非作废状态,不需反作废")
                return HttpResponseRedirect("../%s/" % pk_value)

        elif request.POST.has_key("_regular"):
            if obj.sys_status == pcfg.WAIT_AUDIT_STATUS and obj.remind_time:
                obj.sys_status = pcfg.REGULAR_REMAIN_STATUS
                obj.save()
                msg = u"订单定时时间:%s" % obj.remind_time
                self.message_user(request, msg)
                log_action(request.user.id, obj, CHANGE, msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"订单不是问题单或没有设定提醒时间")
                return HttpResponseRedirect("../%s/" % pk_value)

        elif request.POST.has_key("_unregular"):
            if obj.sys_status == pcfg.REGULAR_REMAIN_STATUS:
                MergeTrade.objects.filter(id=obj.id).update(sys_status=pcfg.WAIT_AUDIT_STATUS,
                                                            remind_time=None)
                msg = u"订单定时已取消"
                self.message_user(request, msg)
                log_action(request.user.id, obj, CHANGE, msg)
                return HttpResponseRedirect("../%s/" % pk_value)
            else:
                self.message_user(request, u"订单不在定时提醒区,不需要取消定时")
                return HttpResponseRedirect("../%s/" % pk_value)

        elif request.POST.has_key("_split"):
            if obj.sys_status == pcfg.WAIT_AUDIT_STATUS:
                if obj.has_reason_code(pcfg.MULTIPLE_ORDERS_CODE):
                    obj.remove_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
                    msg = u"订单已取消需手动合并状态"
                elif obj.has_merge:
                    MergeTrade.objects.mergeRemover(obj)
                    msg = u"订单已取消合并状态"
                else:
                    msg = u'订单不需要取消合并'
                log_action(request.user.id, obj, CHANGE, msg)
            elif obj.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                    pcfg.WAIT_SCAN_WEIGHT_STATUS):
                obj.remove_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
                msg = u"订单已取消待合并状态"
                log_action(request.user.id, obj, CHANGE, msg)
            else:
                msg = u"该订单不在问题单,或待扫描状态,或没有合并子订单"
            self.message_user(request, msg)
            return HttpResponseRedirect("../%s/" % pk_value)

        elif request.POST.has_key("_save"):
            msg = u'%(name)s "%(obj)s" 保存成功.' % {'name': force_unicode(verbose_name),
                                                 'obj': force_unicode(obj)}
            self.message_user(request, msg)
            return HttpResponseRedirect("../%s/" % pk_value)

        elif request.POST.has_key("_finish"):
            if obj.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                  pcfg.WAIT_SCAN_WEIGHT_STATUS):

                MergeTrade.objects.updateProductStockByTrade(obj)

                obj.sys_status = pcfg.FINISHED_STATUS
                obj.weight_time = datetime.datetime.now()
                obj.weighter = request.user.username
                obj.save()

                msg = u'%(name)s "%(obj)s" 订单手动修改已完成.' % {'name': force_unicode(verbose_name),
                                                          'obj': force_unicode(obj)}
                log_action(request.user.id, obj, CHANGE, msg)
            else:
                msg = u"订单不在待扫描验货或待扫描称重,不能修改为已完成状态"
            self.message_user(request, msg)
            return HttpResponseRedirect("../%s/" % pk_value)

        elif request.POST.has_key("_rescan"):
            if obj.sys_status == pcfg.FINISHED_STATUS:
                obj.sys_status = pcfg.WAIT_CHECK_BARCODE_STATUS
                obj.save()

                for order in obj.inuse_orders.exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE):
                    outer_id = order.outer_id
                    outer_sku_id = order.outer_sku_id
                    order_num = order.num

                    if outer_sku_id:
                        psku = ProductSku.objects.get(product__outer_id=outer_id,
                                                      outer_id=outer_sku_id)
                        psku.update_quantity(order_num)
                        psku.update_wait_post_num(order_num)

                    else:
                        prod = Product.objects.get(outer_id=outer_id)
                        prod.update_collect_num(order_num)
                        prod.update_wait_post_num(order_num)

                msg = u'%(name)s "%(obj)s" 订单进入重新扫描状态.' % {'name': force_unicode(verbose_name),
                                                           'obj': force_unicode(obj)}
                log_action(request.user.id, obj, CHANGE, msg)
            else:
                msg = u"订单不在已完成,不能修改为待扫描状态"
            self.message_user(request, msg)
            return HttpResponseRedirect("../%s/" % pk_value)

        return super(MergeTradeAdmin, self).response_change(request, obj, *args, **kwargs)

    # --------定义action----------------

    def _handle_merge(self, user_id, sub_trade, main_trade):

        merge_success = MergeTrade.objects.mergeMaker(main_trade, sub_trade)
        if merge_success:
            sub_trade.out_sid = main_trade.out_sid
            sub_trade.logistics_company = main_trade.logistics_company
            sub_trade.sys_status = pcfg.ON_THE_FLY_STATUS
            sub_trade.operator = main_trade.operator
            sub_trade.save()

            if sub_trade.status == pcfg.WAIT_SELLER_SEND_GOODS:
                if main_trade.status in pcfg.ORDER_POST_STATUS:
                    try:
                        TradeService(user_id, sub_trade).sendTrade()
                    except Exception, exc:
                        log_action(user_id, sub_trade, CHANGE, u'订单发货失败:%s' % exc.message)
                        logger.error(u'订单发货失败:%s' % exc.message, exc_info=True)
                else:
                    mtd, state = MergeTradeDelivery.objects.get_or_create(seller=sub_trade.user,
                                                                          trade_id=sub_trade.id)
                    mtd.trade_no = sub_trade.tid
                    mtd.buyer_nick = sub_trade.buyer_nick
                    mtd.is_parent = False
                    mtd.is_sub = True
                    mtd.parent_tid = main_trade.id
                    mtd.status = MergeTradeDelivery.WAIT_DELIVERY
                    mtd.save()

        return merge_success

    # 合并订单
    def merge_order_action(self, request, queryset):

        trade_ids = [t.id for t in queryset]
        is_merge_success = False
        wlbset = queryset.filter(is_force_wlb=True)
        queryset = (queryset.filter(is_force_wlb=False)
                    .exclude(status__in=(pcfg.TRADE_CLOSED,
                                         pcfg.TRADE_CLOSED_BY_TAOBAO)))
        myset = queryset.exclude(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,
                                                 pcfg.ON_THE_FLY_STATUS,
                                                 pcfg.WAIT_PREPARE_SEND_STATUS,
                                                 pcfg.WAIT_CHECK_BARCODE_STATUS,
                                                 pcfg.WAIT_SCAN_WEIGHT_STATUS))
        postset = queryset.filter(sys_status__in=(pcfg.WAIT_CHECK_BARCODE_STATUS,
                                                  pcfg.WAIT_SCAN_WEIGHT_STATUS))
        if wlbset.count() > 0:
            is_merge_success = False
            fail_reason = u'有订单使用物流宝发货,若需在系统发货,请手动取消该订单物流宝状态'

        elif queryset.count() < 2 or myset.count() > 0 or postset.count() > 1:
            is_merge_success = False
            fail_reason = u'不符合合并条件（合并订单必须两单以上,订单状态在问题单或待扫描,未关闭状态）'

        else:
            from shopapp.memorule import ruleMatchPayment

            merge_trade_ids = []  # 合单成的订单ID
            fail_reason = ''
            is_merge_success = False

            if postset.count() == 1:
                main_trade = postset[0]
                main_full_addr = main_trade.buyer_full_address  # 主订单收货人地址
                sub_trades = queryset.filter(sys_status=pcfg.WAIT_AUDIT_STATUS).order_by('-has_merge')
                for trade in sub_trades:
                    if trade.id in merge_trade_ids:
                        continue
                    if trade.buyer_full_address != main_full_addr:
                        is_merge_success = False
                        fail_reason = (u'订单地址不同:%s' % MergeTrade.objects.diffTradeAddress(trade, main_trade))
                        break
                    if trade.has_merge and trade.sys_status == pcfg.WAIT_AUDIT_STATUS:
                        sub_tids = MergeBuyerTrade.objects.filter(
                            main_tid=trade.id).values_list('sub_tid')
                        MergeTrade.objects.mergeRemover(trade)

                        for strade in MergeTrade.objects.filter(id__in=[t[0] for t in sub_tids]):
                            if strade.id in merge_trade_ids:
                                continue
                            is_merge_success = self._handle_merge(request.user.id, strade, main_trade)
                            if is_merge_success:
                                merge_trade_ids.append(strade.id)

                    is_merge_success = self._handle_merge(request.user.id, trade, main_trade)
                    if is_merge_success:
                        merge_trade_ids.append(trade.id)

                if is_merge_success and len(merge_trade_ids) < sub_trades.count():
                    fail_reason = u'部分订单未合并成功'
                    is_merge_success = False

                elif is_merge_success:
                    # 合并后金额匹配
                    ruleMatchPayment(main_trade)
                    is_merge_success = True
                    log_action(request.user.id, main_trade, CHANGE,
                               u'合并订单(%s)' % ','.join([str(id) for id in merge_trade_ids]))
            else:
                audit_trades = queryset.filter(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,
                                                               pcfg.WAIT_PREPARE_SEND_STATUS)
                                               ).order_by('pay_time')
                if audit_trades.count() > 0:
                    merge_trades = audit_trades.filter(has_merge=True)
                    if merge_trades.count() > 0:
                        main_trade = merge_trades[0]
                    else:
                        main_trade = audit_trades[0]  # 主订单

                    queryset = queryset.exclude(id=main_trade.id)
                    main_full_addr = main_trade.buyer_full_address  # 主订单收货人地址

                    for trade in queryset:
                        if trade.id in merge_trade_ids:
                            continue

                        if trade.buyer_full_address != main_full_addr:
                            is_merge_success = False
                            fail_reason = (u'订单地址不同:%s' % MergeTrade.
                                           objects.diffTradeAddress(trade, main_trade))
                            break

                        if trade.has_merge and trade.sys_status == pcfg.WAIT_AUDIT_STATUS:
                            sub_tids = MergeBuyerTrade.objects.filter(
                                main_tid=trade.id).values_list('sub_tid')
                            MergeTrade.objects.mergeRemover(trade)

                            for strade in MergeTrade.objects.filter(id__in=[t[0] for t in sub_tids]):
                                if strade.id in merge_trade_ids:
                                    continue
                                is_merge_success = self._handle_merge(request.user.id,
                                                                      strade, main_trade)
                                if is_merge_success:
                                    merge_trade_ids.append(strade.id)

                        is_merge_success = self._handle_merge(request.user.id,
                                                              trade, main_trade)
                        if not is_merge_success:
                            fail_reason = u'订单合并错误'
                            break

                        merge_trade_ids.append(trade.id)
                if is_merge_success:
                    ruleMatchPayment(main_trade)
                    log_action(request.user.id, main_trade, CHANGE,
                               u'合并订单,主订单:%d,子订单:%s' % (main_trade.id,
                                                        ','.join([str(id) for id in merge_trade_ids])))

                elif merge_trade_ids:
                    MergeTrade.objects.mergeRemover(main_trade)

        trades = MergeTrade.objects.filter(id__in=trade_ids)
        return render_to_response('trades/mergesuccess.html',
                                  {'trades': trades,
                                   'merge_status': is_merge_success,
                                   'fail_reason': fail_reason},
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    merge_order_action.short_description = "合并订单".decode('utf8')

    # 更新下载订单
    def pull_order_action(self, request, queryset):

        queryset = queryset.filter(sys_status__in=(
            pcfg.WAIT_AUDIT_STATUS,
            pcfg.REGULAR_REMAIN_STATUS,
            pcfg.EMPTY_STATUS))
        pull_success_ids = []
        pull_fail_ids = []

        for trade in queryset:
            # 如果有合单,则取消合并
            if trade.has_merge:
                pull_fail_ids.append(trade.id)
                continue

            trade.sys_status = pcfg.EMPTY_STATUS
            trade.reason_code = ''
            trade.has_sys_err = False
            trade.has_merge = False
            trade.has_memo = False
            trade.has_rule_match = False
            trade.has_out_stock = False
            trade.has_refund = False
            trade.is_force_wlb = False
            trade.buyer_message = ''
            trade.seller_memo = ''
            trade.save()

            try:
                MergeTrade.objects.reduceWaitPostNum(trade)
            except:
                pass

            try:
                trade.merge_orders.all().delete()
                seller_id = trade.user.visitor_id

                TradeService(seller_id, trade.tid).payTrade(trade_merge_flag=False)

            except Exception, exc:
                logger.error(u'重新下单错误:%s' % exc.message, exc_info=True)
                trade.append_reason_code(pcfg.PULL_ORDER_ERROR_CODE)
                pull_fail_ids.append(trade.id)

            else:
                pull_success_ids.append(trade.id)
                log_action(request.user.id, trade, CHANGE, u'重新下载订单')

        success_trades = MergeTrade.objects.filter(id__in=pull_success_ids)
        fail_trades = MergeTrade.objects.filter(id__in=pull_fail_ids)

        return render_to_response('trades/repullsuccess.html',
                                  {'success_trades': success_trades,
                                   'fail_trades': fail_trades},
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    pull_order_action.short_description = "重新下单".decode('utf8')

    # 订单
    def push_trade_to_scan(self, request, queryset):

        try:
            user_id = request.user.id
            trade_ids = [t.id for t in queryset]
            if not trade_ids:
                self.message_user(request, u'没有可发货的订单')
                return

            replay_trade = ReplayPostTrade.objects.create(operator=request.user.username,
                                                          order_num=len(trade_ids),
                                                          trade_ids=','.join([str(i) for i in trade_ids]))

            send_tasks = chord([sendTaobaoTradeTask.s(user_id, trade.id)
                                for trade in queryset])(sendTradeCallBack.s(replay_trade.id), max_retries=300)

        except Exception, exc:
            logger.error(exc.message, exc_info=True)
            return HttpResponse('<body style="text-align:center;"><h1>发货请求执行出错:（%s）</h1></body>' % exc.message)

        response_dict = {'task_id': send_tasks.task_id, 'replay_id': replay_trade.id}

        return render_to_response('trades/send_trade_reponse.html',
                                  response_dict,
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    push_trade_to_scan.short_description = "同步发货".decode('utf8')

    def unlock_trade_action(self, request, queryset):
        """ 解除订单锁定 """
        trade_ids = [t.id for t in queryset]
        unlockable_trades = queryset.filter(
            sys_status__in=(pcfg.WAIT_AUDIT_STATUS,
                            pcfg.WAIT_PREPARE_SEND_STATUS),
            is_locked=True)

        for trade in unlockable_trades:
            operator = trade.operator
            trade.is_locked = False
            trade.operator = ''
            trade.save()

            log_action(request.user.id, trade, CHANGE,
                       u'解除订单锁定(前锁定人:%s)' % operator)

        success_trades = MergeTrade.objects.filter(id__in=trade_ids, is_locked=False)

        fail_trades = MergeTrade.objects.filter(id__in=trade_ids, is_locked=True)

        return render_to_response('trades/unlock_trade_status_template.html',
                                  {'success_trades': success_trades,
                                   'fail_trades': fail_trades},
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    unlock_trade_action.short_description = "订单解锁".decode('utf8')

    def invalid_trade_action(self, request, queryset):
        """ 订单作废 """

        for trade in queryset:
            trade.sys_status = pcfg.INVALID_STATUS
            trade.save()

            log_action(request.user.id, trade, CHANGE, u'订单作废')

        self.message_user(request, u"======= 订单批量作废成功 =======")

        return HttpResponseRedirect("./")

    invalid_trade_action.short_description = "订单作废".decode('utf8')

    def export_finance_action(self, request, queryset):
        """ 导出订单金额信息 """
        dt = datetime.datetime.now()
        lg_tuple = gen_cvs_tuple(queryset,
                                 fields=['tid', 'user__nick', 'buyer_nick', 'payment', 'post_fee', 'pay_time'],
                                 title=[u'淘宝单号', u'店铺ID', u'买家ID', u'实付款', u'实付邮费', u'付款日期'])

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        file_name = u'finance-%s-%s.csv' % (dt.month, dt.day)

        myfile = StringIO.StringIO()

        writer = CSVUnicodeWriter(myfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(lg_tuple)

        response = HttpResponse(myfile.getvalue(), content_type='application/octet-stream')
        myfile.close()
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
        return response

    export_finance_action.short_description = "导出金额信息".decode('utf8')

    def export_logistic_action(self, request, queryset):
        """ 导出订单快递信息 """
        dt = datetime.datetime.now()
        lg_tuple = gen_cvs_tuple(queryset,
                                 fields=['out_sid', 'tid', 'user__nick', 'receiver_name',
                                         'receiver_state', 'receiver_city', 'weight',
                                         'logistics_company', 'post_fee', 'weight_time'],
                                 title=[u'运单ID', u'原始单号', u'店铺', u'收货人', u'省', u'市',
                                        u'重量', u'快递', u'实付邮费', u'称重日期'])

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        file_name = u'logistic-%s-%s.csv' % (dt.month, dt.day)

        myfile = StringIO.StringIO()

        writer = CSVUnicodeWriter(myfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(lg_tuple)

        response = HttpResponse(myfile.getvalue(), content_type='application/octet-stream')
        myfile.close()
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name

        return response

    export_logistic_action.short_description = "导出快递信息".decode('utf8')

    def export_buyer_action(self, request, queryset):
        """ 导出订单买家信息 """
        dt = datetime.datetime.now()
        buyer_tuple = gen_cvs_tuple(queryset,
                                    fields=['user__nick', 'buyer_nick', 'receiver_state',
                                            'receiver_phone', 'receiver_mobile', 'pay_time'],
                                    title=[u'卖家', u'买家昵称', u'省', u'固话', u'手机', u'付款日期'])

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        file_name = u'buyer-%s-%s.csv' % (dt.month, dt.day)

        myfile = StringIO.StringIO()

        writer = CSVUnicodeWriter(myfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(buyer_tuple)

        response = HttpResponse(myfile.getvalue(), content_type='application/octet-stream')
        myfile.close()
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
        return response

    export_buyer_action.short_description = "导出买家信息".decode('utf8')

    def export_yunda_action(self, request, queryset):
        """ 导出订单快递信息 """
        dt = datetime.datetime.now()
        yundaset = queryset.filter(logistics_company__code__in=('YUNDA', 'YUNDA_QR'))
        yunda_tuple = []

        for s in yundaset:
            try:
                sl = []
                sl.append(s.weight_time and s.weight_time.strftime('%Y-%m-%d'))
                sl.append('%s' % s.logistics_company)
                sl.append(s.out_sid)
                sl.append(s.tid and str(s.tid) or '')
                sl.append(s.receiver_state)
                sl.append('%s%s%s' % (s.receiver_city, s.receiver_district, s.receiver_address))
                sl.append(s.receiver_name)
                sl.append(s.receiver_mobile or s.receiver_phone)
                if '.' in s.weight:
                    weight = s.weight
                else:
                    weight = '%.2f' % (float(s.weight) / 1000)
                sl.append(weight)

                yunda_tuple.append(sl)
            except:
                pass

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        file_name = u'yunda-%s-%s.csv' % (dt.month, dt.day)

        myfile = StringIO.StringIO()

        writer = CSVUnicodeWriter(myfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(yunda_tuple)

        response = HttpResponse(myfile.getvalue(), content_type='application/octet-stream')
        myfile.close()
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
        return response

    def export_orderdetail_action(self, request, queryset):
        """ 导出订单明细信息 """

        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        pcsv = []
        pcsv.append((u'订单序号', u'订单明细ID', u'订单ID', u'客户名称', u'商品编码', '商品名称', u'规格编码', u'规格名称',
                     u'拍下数量', u'留言', u'备注', u'付款时间', u'收货人', u'固话', u'手机', u'省', u'市', u'区', u'详细地址', u'快递方式'))

        trade_ids = []
        rindex = 1
        for itrade in queryset:
            trade_ids.append(itrade.id)

        for trade in queryset:
            index = 0
            for order in trade.print_orders:
                pcsv.append(('%s' % p for p in [(rindex, '')[index],
                                                order.oid,
                                                trade.tid,
                                                trade.receiver_name,
                                                order.outer_id,
                                                order.title,
                                                order.outer_sku_id,
                                                order.sku_properties_name,
                                                order.num,
                                                trade.buyer_message,
                                                '%s%s' % (trade.seller_memo, trade.sys_memo),
                                                trade.pay_time,
                                                trade.receiver_name,
                                                trade.receiver_phone,
                                                trade.receiver_mobile,
                                                trade.receiver_state,
                                                trade.receiver_city,
                                                trade.receiver_district,
                                                trade.receiver_address,
                                                trade.get_shipping_type_display()]))
                index = 1
            rindex += 1

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment;filename=orderdetail-%s.csv' % str(int(time.time()))

        return response

    export_orderdetail_action.short_description = u"导出订单明细"

    export_yunda_action.short_description = "导出韵达信息".decode('utf8')

    actions = ['push_trade_to_scan',
               'merge_order_action',
               'pull_order_action',
               'unlock_trade_action',
               'invalid_trade_action',
               'export_logistic_action',
               'export_buyer_action',
               'export_finance_action',
               'export_orderdetail_action',
               'export_yunda_action']


admin.site.register(MergeTrade, MergeTradeAdmin)


class MergeOrderChangeList(ChangeList):
    def get_queryset(self, request):

        from django.core.exceptions import SuspiciousOperation, ImproperlyConfigured
        from django.contrib.admin.options import IncorrectLookupParameters

        # 如果查询条件中含有邀请码
        search_q = request.GET.get('q', '').strip()
        if len(search_q.split()) > 1:
            outer_id, outer_sku_id = search_q.split()

            (self.filter_specs, self.has_filters, remaining_lookup_params,
             use_distinct) = self.get_filters(request)

            # Then, we let every list filter modify the queryset to its liking.
            qs = self.root_queryset
            for filter_spec in self.filter_specs:
                new_qs = filter_spec.queryset(request, qs)
                if new_qs is not None:
                    qs = new_qs

            qs = qs.filter(outer_id=outer_id, outer_sku_id=outer_sku_id)

            ordering = self.get_ordering(request, qs)
            qs = qs.order_by(*ordering)

            return qs

        if re.compile('^[\w]{1,36}$').match(search_q):
            filter_qs = models.Q(tid=search_q)
            if len(search_q) == 11 and search_q.isdigit():
                filter_qs |= models.Q(receiver_mobile=search_q)

            try:
                mts = MergeTrade.objects.filter(filter_qs)
                mtids = [m.id for m in mts]
            except:
                mtids = []

            if search_q.isdigit():
                mtids.append(int(search_q))

            qs = MergeOrder.objects.filter(models.Q(oid=search_q)
                                           | models.Q(merge_trade__in=mtids)
                                           | models.Q(outer_id=search_q))

            ordering = self.get_ordering(request, qs)
            qs = qs.order_by(*ordering)

            return qs

        if search_q:
            return MergeOrder.objects.none()

        return super(MergeOrderChangeList, self).get_queryset(request)


class MergeOrderAdmin(ApproxAdmin):
    list_display = (
    'id', 'package_sku_item_link_to', 'merge_trade_link', 'outer_id', 'outer_sku_id', 'sku_properties_name', 'price',
    'num',
    'payment', 'gift_type', 'pay_time', 'refund_status', 'trade_status_link', 'sys_status')
    list_display_links = ('id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    # date_hierarchy = 'created'
    # ordering = ['created_at']
    list_per_page = 50

    list_filter = ('sys_status', 'out_stock', 'is_rule_match',
                   'is_merge', 'gift_type', ('pay_time', DateFieldListFilter),
                   OrderPendingStatusFilter)
    search_fields = ['=id', '=oid', '=outer_id', 'outer_sku_id']

    # --------设置页面布局----------------
    fieldsets = (('订单明细基本信息:', {
        'classes': ('expend',),
        'fields': ('oid', 'outer_id', 'outer_sku_id', 'title', 'price', 'payment', 'num',
                   'sku_properties_name', 'out_stock', 'is_merge', 'is_rule_match', 'is_reverse_order',
                   'gift_type', 'pay_time', 'refund_id', 'refund_status', 'status', 'sys_status')
    }),)

    def merge_trade_link(self, obj):
        return '''%s-%s-<a href="%s" target="_blank">%s</a>''' % (obj.merge_trade.is_express_print and '[P]' or '[N]',
                                                                  obj.merge_trade.get_type_display(),
                                                                  '/admin/trades/mergetrade/?q=' + obj.merge_trade.tid,
                                                                  obj.merge_trade)

    merge_trade_link.allow_tags = True
    merge_trade_link.short_description = "交易信息"

    def trade_status_link(self, obj):
        return obj.merge_trade.get_sys_status_display()

    trade_status_link.allow_tags = True
    trade_status_link.short_description = "交易状态"

    PACKAGE_SKU_ITEM_LINK = (
        '<a href="%(pki_url)s" target="_blank">'
        '%(oid)s</a>')

    def package_sku_item_link_to(self, obj):
        return self.PACKAGE_SKU_ITEM_LINK % {
            'pki_url': '/admin/trades/packageskuitem/?oid=%s' % obj.oid,
            'oid': obj.oid
        }

    package_sku_item_link_to.allow_tags = True
    package_sku_item_link_to.short_description = u'SKU交易单号'

    def get_changelist(self, request, **kwargs):
        return MergeOrderChangeList


admin.site.register(MergeOrder, MergeOrderAdmin)


class MergeBuyerTradeAdmin(admin.ModelAdmin):
    list_display = ('sub_tid', 'main_tid', 'created')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    search_fields = ['sub_tid', 'main_tid']


admin.site.register(MergeBuyerTrade, MergeBuyerTradeAdmin)

from shopback.trades.tasks import uploadTradeLogisticsTask, deliveryTradeCallBack


class MergeTradeDeliveryAdmin(admin.ModelAdmin):
    list_display = ('trade_no', 'buyer_nick', 'seller_nick', 'is_parent', 'is_sub', 'created', 'message', 'status')

    list_filter = ('status', 'is_parent', 'is_sub', ('created', DateFieldListFilter))
    search_fields = ['trade_id', 'trade_no']

    def seller_nick(self, obj):
        return obj.seller.nick

    seller_nick.allow_tags = True
    seller_nick.short_description = "店铺昵称"

    # 淘宝后台同步发货
    def delivery_trade(self, request, queryset):

        try:
            pingstatus = pinghost(settings.TAOBAO_API_HOSTNAME)
            if pingstatus:
                return HttpResponse('<body style="text-align:center;"><h1>当前网络不稳定,请稍后再试...</h1></body>')

            user_id = request.user.id
            trade_ids = [t.id for t in queryset]
            if not trade_ids:
                self.message_user(request, u'没有可发货的订单')
                return

            send_tasks = chord([uploadTradeLogisticsTask.s(trade.trade_id, user_id) for trade in queryset])(
                deliveryTradeCallBack.s(), max_retries=300)

        except Exception, exc:
            return HttpResponse('<body style="text-align:center;"><h1>发货信息上传执行出错:（%s）</h1></body>' % exc.message)

        response_dict = {'task_id': send_tasks.task_id, 'origin_url': request.get_full_path()}

        return render_to_response('trades/delivery_trade_reponse.html',
                                  response_dict,
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    delivery_trade.short_description = "订单发货单号上传".decode('utf8')

    actions = ['delivery_trade']


admin.site.register(MergeTradeDelivery, MergeTradeDeliveryAdmin)


class ReplayPostTradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'operator', 'order_num', 'succ_num', 'receiver', 'fid',
                    'created', 'finished', 'rece_date', 'check_date', 'status')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    search_fields = ['id', 'operator', 'receiver', 'succ_ids']
    list_filter = ('status',)

    def replay_post(self, request, queryset):
        try:
            replay_trade = queryset.order_by('-created')[0]
        except:
            pass
        else:
            from shopback.trades.tasks import get_replay_results
            reponse_result = get_replay_results(replay_trade)
            reponse_result['post_no'] = reponse_result.get('post_no', None) or replay_trade.id

        return render_to_response('trades/trade_post_success.html', reponse_result,
                                  context_instance=RequestContext(request), content_type="text/html")

    replay_post.short_description = "重现发货清单".decode('utf8')

    def check_post(self, request, queryset):

        if queryset.count() != 1:
            return HttpResponse('<body style="text-align:center;"><h1>你只能对单条记录操作,请返回重新选择</h1></body>')
        replay_trade = queryset[0]

        trade_ids = replay_trade.succ_ids.split(',')
        trade_ids = [int(id) for id in trade_ids if id]
        wait_scan_trades = MergeTrade.objects.filter(id__in=trade_ids, sys_status__in=
        (pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS))

        is_success = wait_scan_trades.count() == 0
        if is_success:
            replay_trade.status = pcfg.RP_ACCEPT_STATUS
            replay_trade.check_date = datetime.datetime.now()
            replay_trade.save()

        return render_to_response('trades/trade_accept_check.html',
                                  {'trades': wait_scan_trades, 'is_success': is_success},
                                  context_instance=RequestContext(request), content_type="text/html")

    check_post.short_description = "验证是否完成".decode('utf8')

    def merge_post_result(self, request, queryset):

        if queryset.exclude(status=pcfg.RP_WAIT_ACCEPT_STATUS).count() > 0 or queryset.count() < 2:
            return HttpResponse('<body style="text-align:center;"><h1>有合并清单須在待接单状态,至少两个批次</h1></body>')

        username = request.user.username
        replaypost = ReplayPostTrade.objects.create(operator=username, status=pcfg.SMS_CREATED)
        replaypost.merge(queryset)

        from shopback.trades.tasks import get_replay_results
        reponse_result = get_replay_results(replaypost)
        reponse_result['post_no'] = reponse_result.get('post_no', None) or replaypost.id

        return render_to_response('trades/trade_post_success.html', reponse_result,
                                  context_instance=RequestContext(request), content_type="text/html")

    merge_post_result.short_description = "合并发货批次".decode('utf8')

    def split_post_result(self, request, queryset):
        queryset = queryset.filter(fid=-1, status=pcfg.RP_WAIT_ACCEPT_STATUS)
        if queryset.count() != 1:
            return HttpResponse('<body style="text-align:center;"><h1>请选择一条已合并过的发货记录进行拆分</h1></body>')
        replay_trade = queryset[0]

        replay_trade.split()

        self.message_user(request, '批次:%d,拆分成功!' % replay_trade.id)
        return

    split_post_result.short_description = "拆分发货批次".decode('utf8')

    actions = ['replay_post', 'check_post', 'merge_post_result', 'split_post_result']


admin.site.register(ReplayPostTrade, ReplayPostTradeAdmin)


class WuliuAdmin(admin.ModelAdmin):
    list_display = ('id', 'tid', 'logistics_company', 'out_sid', 'status', 'time', 'content', 'created',)
    search_fields = ['tid', 'out_sid']
    list_filter = ('status',)


admin.site.register(TradeWuliu, WuliuAdmin)

class ReturnWuliuAdmin(admin.ModelAdmin):
    list_display = ('id', 'tid', "rid",'logistics_company', 'out_sid', 'status', 'time', 'content', 'created',)
    search_fields = ['tid', 'out_sid']
    list_filter = ('status',)


admin.site.register(ReturnWuLiu, ReturnWuliuAdmin)


class PackageOrderAdmin(admin.ModelAdmin):
    list_display = (
    'pid', 'id_link', 'sys_status', 'type', 'out_sid', 'logistics_company_name', 'receiver_name', 'receiver_mobile', 'receiver_address_info',
    'payment', 'operator', 'is_picking_print', 'is_express_print', 'redo_sign',
    'is_send_sms', 'has_refund', 'ware_by', 'created', 'send_time', 'weight_time',
    'consign_time', 'weight', 'merge_trade_id')

    search_fields = ['pid', 'id', 'out_sid', 'receiver_name', 'receiver_mobile']
    list_filter = ('sys_status', 'ware_by', 'status', 'redo_sign', 'is_qrcode', ('weight_time', DateFieldListFilter),)
    change_list_template = "admin/trades/package_change_list.html"
    ordering = ['-sys_status']
    list_per_page = 50

    def id_link(self, obj):
        return "<a href='/admin/trades/packageskuitem?package_order_pid=%d'>%s</a>" % (obj.pid, obj.id)
    id_link.short_description = u'包裹码'
    id_link.allow_tags = True

    def receiver_address_info(self, obj):
        return obj.receiver_address_detail
    receiver_address_info.short_description = u'详细地址'

    def push_package_to_scan(self, request, queryset):
        try:

            user_id = request.user.id
            trade_ids = [t.pid for t in queryset]
            if not trade_ids:
                self.message_user(request, u'没有可发货的订单')
                return

            replay_trade = ReplayPostTrade.objects.create(operator=request.user.username,
                                                          order_num=len(trade_ids),
                                                          trade_ids=','.join([str(i) for i in trade_ids]))

            send_tasks = chord([send_package_task.s(user_id, order.pid)
                                for order in queryset])(send_package_call_Back.s(replay_trade.id), max_retries=300)

        except Exception, exc:
            logger.error(exc.message, exc_info=True)
            return HttpResponse('<body style="text-align:center;"><h1>发货请求执行出错:（%s）</h1></body>' % exc.message)

        response_dict = {'task_id': send_tasks.task_id, 'replay_id': replay_trade.id}

        return render_to_response('trades/send_package_reponse.html',
                                  response_dict,
                                  context_instance=RequestContext(request),
                                  content_type="text/html")

    push_package_to_scan.short_description = "同步发货".decode('utf8')

    def logistics_company_name(self, obj):
        return obj.logistics_company.name if obj.logistics_company else ''

    logistics_company_name.short_description = u"物流公司"

    actions = ['push_package_to_scan']

    class Media:
        css = {"all": ("admin/css/forms.css", "css/admin/dialog.css", "css/admin/checkorder.css")}
        #         js = ("jquery/jquery-1.8.13.min.js","script/admin/adminpopup.js","script/trades/new_checkTrade.js",
        #               "layer-v1.9.2/layer/layer.js","bootstrap/js/bootstrap.js","script/trades/select_stock.js",)
        js = ("closure-library/closure/goog/base.js", "script/admin/adminpopup.js", "script/base.js",
              "script/trades/checkpackage.js",
              "script/trades/tradetags.js", "script/trades/new_checkTrade.js", "layer-v1.9.2/layer/layer.js",
              "bootstrap/js/bootstrap.js", "jquery/jquery-1.8.13.min.js", "script/trades/select_stock.js")


admin.site.register(PackageOrder, PackageOrderAdmin)


class PackageSkuItemAdmin(admin.ModelAdmin):
    # TODO@HY self.sale_order.sale_trade.buyer_nick写法多次查询数据库，以后可以优化性能
    list_display = (
        'id', 'sale_order_link_to', 'oid', 'sale_trade_id_link', 'receiver_mobile', 'out_sid', 'logistics_company_name',
        'package_order_link_to', 'package_sku_item_link_to', 'assign_status', 'sys_status',
        'pay_time', 'assign_time', 'product_title_link_to', 'ware_by', 'sku_id_link_to', 'sku_link_to', 'num', 'price',
        'total_fee', 'payment', 'discount_fee', 'adjust_fee', 'purchase_order_unikey_link', 'orderlist_status', 'modified', 'created')

    search_fields = ['id', 'sale_order_id', 'sale_trade_id', 'receiver_mobile', 'out_sid', 'package_order_pid',
                     'package_order_id', 'oid', 'sku_id', 'purchase_order_unikey']
    list_filter = ('assign_status', 'status', 'ware_by')
    change_list_template = "admin/trades/package_change_list.html"
    ordering = ['-sys_status']
    list_per_page = 50
    readonly_fields = get_class_fields(PackageSkuItem)
    PACKAGE_ORDER_LINK = (
        '<a href="%(package_order_url)s" target="_blank">'
        '%(package_order_pid)s</a>')

    def purchase_order_unikey_link(self, obj):
        if obj.purchase_order_unikey:
            return '<a href="/admin/dinghuo/orderlist/?purchase_order_unikey=%s" target="_blank"> %s </a>' % (
            obj.purchase_order_unikey, obj.purchase_order_unikey)
        return ''

    purchase_order_unikey_link.allow_tags = True
    purchase_order_unikey_link.short_description = u'订货单'

    # def get_purchase_order(self):
    #     from flashsale.dinghuo.models import OrderList
    #     PackageSkuItem.objects.filter(assign_status)
    #     return OrderList.objects.filter()

    def orderlist_status(self, obj):
        from flashsale.dinghuo.models import OrderList
        ol = obj.order_list
        now = datetime.datetime.now()
        if not ol:
            return u'未订货'
        if ol.is_finished() and ol.third_package:
            try:
                delta = (now - ol.received_time).days
            except:
                delta = -1
            return u'第三方返货已通知%d天' % delta
        elif ol.is_finished():
            try:
                delta = (now - ol.received_time).days
            except:
                delta = -1
            return u'已到货%d天' % delta
        elif ol.stage == OrderList.STAGE_RECEIVE:
            try:
                delta = (now - ol.receive_time).days
            except:
                delta = -1
            return u'已订货%d天' % delta
        elif ol.stage == OrderList.STAGE_PAY:
            return u'待付款'
        elif ol.stage == OrderList.STAGE_CHECKED:
            return u'审核待付款'
        return u'异常'
    orderlist_status.short_description = u'订货状态'

    def get_actions(self, request):
        return [i for i in super(PackageSkuItemAdmin, self).get_actions(request) if i != 'delete_selected']

    def package_order_link_to(self, obj):
        if obj.package_order_pid:
            return self.PACKAGE_ORDER_LINK % {
                'package_order_url': '/admin/trades/packageorder/%d/' % obj.package_order_pid,
                'package_order_pid': obj.package_order_id
            }
        return ''

    package_order_link_to.allow_tags = True
    package_order_link_to.short_description = u'包裹商品'

    def sale_trade_id_link(self, obj):
        return '<a href="%(url)s" target="_blank"> %(text)s</a>' % {
            'url': '/admin/pay/saletrade/?tid=%s' % obj.sale_trade_id,
            'text': obj.sale_trade_id
        }

    sale_trade_id_link.allow_tags = True
    sale_trade_id_link.short_description = u'交易单号'

    def package_sku_item_link_to(self, obj):
        if obj.package_order_pid:
            return self.PACKAGE_ORDER_LINK % {
                'package_order_url': '/admin/trades/packageskuitem/?package_order_pid=%d' % obj.package_order_pid,
                'package_order_pid': obj.package_order_pid
            }
        return ''

    package_sku_item_link_to.allow_tags = True
    package_sku_item_link_to.short_description = u'包裹商品列表'

    SALE_ORDER_LINK = (
        '<a href="%(sale_order_url)s" target="_blank">'
        '%(sale_order_id)s</a>')

    def sale_order_link_to(self, obj):
        return self.SALE_ORDER_LINK % {
            'sale_order_url': '/admin/pay/saleorder/%d/' % obj.sale_order_id,
            'sale_order_id': obj.sale_order_id
        }

    sale_order_link_to.allow_tags = True
    sale_order_link_to.short_description = u'sku交易单'

    SKU_PREVIEW_TPL = (
        '<a href="%(sku_url)s" target="_blank">'
        '%(skucode)s</a>')

    def sku_id_link_to(self, obj):
        return self.SKU_PREVIEW_TPL % {
            'sku_url': '/admin/items/productskustats?sku_id=%s' % obj.sku_id,
            'skucode': obj.sku_id
        }

    sku_id_link_to.allow_tags = True
    sku_id_link_to.short_description = u'SKU库存'

    def sku_link_to(self, obj):
        return self.SKU_PREVIEW_TPL % {
            'sku_url': '/admin/items/productsku/%s/' % obj.sku_id,
            'skucode': obj.product_sku.BARCODE
        }

    sku_link_to.allow_tags = True
    sku_link_to.short_description = u'sku条码'

    PRODUCT_LINK = (
        '<a href="%(product_url)s" target="_blank">'
        '%(product_title)s</a>')

    def product_title_link_to(self, obj):
        return self.PRODUCT_LINK % {
            'product_url': '/admin/items/product/%d/' % obj.product_sku.product.id,
            'product_title': obj.title
        }

    product_title_link_to.allow_tags = True
    product_title_link_to.short_description = u'商品名称'


admin.site.register(PackageSkuItem, PackageSkuItemAdmin)
