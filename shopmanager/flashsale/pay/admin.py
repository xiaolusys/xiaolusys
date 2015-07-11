# -*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.conf import settings
from django.contrib.admin.views.main import ChangeList
from django.forms import TextInput, Textarea, FloatField
from django.http import HttpResponseRedirect

from shopback.base import log_action, User, ADDITION, CHANGE
from shopback.trades.filters import DateFieldListFilter
from .service import FlashSaleService
from .models import (SaleTrade,
                     SaleOrder,
                     TradeCharge,
                     Customer,
                     Register,
                     District,
                     UserAddress,
                     SaleRefund)

import logging

logger = logging.getLogger('django.request')


class SaleOrderInline(admin.TabularInline):
    model = SaleOrder
    fields = (
    'oid', 'outer_id', 'title', 'outer_sku_id', 'sku_name', 'payment', 'num', 'refund_fee', 'refund_status', 'status')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '16'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 20})},
    }

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = set(self.readonly_fields + ('oid',))
        if not request.user.is_superuser:
            readonly_fields.update(('outer_id', 'outer_sku_id'))
        return tuple(readonly_fields)


class SaleTradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tid', 'buyer_nick', 'channel', 'payment', 'pay_time', 'created', 'status', 'buyer_id')
    list_display_links = ('id', 'tid')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status', 'channel', ('pay_time', DateFieldListFilter), ('created', DateFieldListFilter))
    search_fields = ['tid', 'id', 'receiver_mobile']

    inlines = [SaleOrderInline]

    #-------------- 页面布局 --------------
    fieldsets = ((u'订单基本信息:', {
        'classes': ('expand',),
        'fields': (('tid', 'buyer_nick', 'channel', 'status')
                   , ('trade_type', 'total_fee', 'payment', 'post_fee')
                   , ('pay_time', 'consign_time', 'charge', 'openid')
                   , ('buyer_message', 'seller_memo')
                   )
    }),
                 (u'收货人及物流信息:', {
                     'classes': ('expand',),
                     'fields': (('receiver_name', 'receiver_state', 'receiver_city', 'receiver_district')
                                , ('receiver_address', 'receiver_zip', 'receiver_mobile', 'receiver_phone')
                                , ('logistics_company', 'out_sid'))
                 }),
                 )

    #--------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '16'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 35})},
    }

    def get_readonly_fields(self, request, obj=None):

        if not request.user.is_superuser:
            return self.readonly_fields + ('tid',)
        return self.readonly_fields

    def push_mergeorder_action(self, request, queryset):
        """ 更新订单到订单总表 """

        for strade in queryset:
            saleservice = FlashSaleService(strade)
            saleservice.payTrade()

        self.message_user(request, u'已更新%s个订单到订单总表!' % queryset.count())

        origin_url = request.get_full_path()

        return redirect(origin_url)

    push_mergeorder_action.short_description = u"更新订单到订单总表"

    actions = ['push_mergeorder_action']


admin.site.register(SaleTrade, SaleTradeAdmin)


class TradeChargeAdmin(admin.ModelAdmin):
    list_display = ('order_no', 'charge', 'channel', 'amount', 'time_paid', 'paid', 'refunded')
    list_display_links = ('order_no', 'charge',)

    list_filter = (('time_paid', DateFieldListFilter),)
    search_fields = ['order_no', 'charge']


admin.site.register(TradeCharge, TradeChargeAdmin)


class RegisterAdmin(admin.ModelAdmin):
    list_display = ('id', 'cus_uid', 'vmobile', 'vemail', 'created')
    list_display_links = ('id', 'cus_uid')
    #list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = (('created', DateFieldListFilter),)
    search_fields = ['id', 'cus_uid', 'vmobile', 'vemail']


admin.site.register(Register, RegisterAdmin)


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'nick', 'mobile', 'phone', 'created', 'modified', 'unionid')
    list_display_links = ('id', 'nick',)

    search_fields = ['id', 'mobile', 'openid', 'unionid']


admin.site.register(Customer, CustomerAdmin)


class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'full_name', 'parent_id', 'grade', 'sort_order')
    search_fields = ['id', 'parent_id', 'name']

    list_filter = ('grade',)


admin.site.register(District, DistrictAdmin)


class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'cus_uid', 'receiver_name', 'receiver_state',
                    'receiver_city', 'receiver_mobile', 'default', 'status')
    search_fields = ['cus_uid', 'receiver_mobile']

    list_filter = ('default', 'status')


admin.site.register(UserAddress, UserAddressAdmin)


class SaleRefundChangeList(ChangeList):
    def get_query_set(self, request):

        search_q = request.GET.get('q', '').strip()
        if search_q:

            refunds = SaleRefund.objects.none()
            trades = SaleTrade.objects.filter(tid=search_q)
            if trades.count() > 0 and search_q.isdigit():

                refunds = SaleRefund.objects.filter(models.Q(trade_id=trades[0].id) |
                                                    models.Q(order_id=search_q) |
                                                    models.Q(refund_id=search_q) |
                                                    models.Q(mobile=search_q) |
                                                    models.Q(trade_id=search_q))

            elif trades.count() > 0:
                refunds = SaleRefund.objects.filter(trade_id=trades[0].id)

            elif search_q.isdigit():
                refunds = SaleRefund.objects.filter(models.Q(order_id=search_q) |
                                                    models.Q(refund_id=search_q) |
                                                    models.Q(mobile=search_q) |
                                                    models.Q(trade_id=search_q))

            return refunds

        return super(SaleRefundChangeList, self).get_query_set(request)


from flashsale.xiaolumm.models import XiaoluMama, CarryLog


class SaleRefundAdmin(admin.ModelAdmin):
    list_display = (
    'refund_no', 'order_no', 'order_channel', 'title', 'refund_fee', 'has_good_return', 'has_good_change', 'created',
    'status')

    list_filter = ('status', 'good_status', 'has_good_return', 'has_good_change')

    search_fields = ['trade_id', 'order_id', 'refund_id', 'mobile']
    list_per_page = 20

    def order_no(self, obj):
        strade = SaleTrade.objects.get(id=obj.trade_id)
        return strade.tid

    order_no.allow_tags = True
    order_no.short_description = "交易编号"

    def order_channel(self, obj):
        strade = SaleTrade.objects.get(id=obj.trade_id)
        return strade.get_channel_display()

    order_channel.allow_tags = True
    order_channel.short_description = "支付方式"

    #-------------- 页面布局 --------------
    fieldsets = (('基本信息:', {
        'classes': ('expand',),
        'fields': (('refund_no', 'trade_id', 'order_id')
                   , ('buyer_id', 'title', 'sku_name',)
                   , ('payment', 'total_fee',)
                   , ('company_name', 'sid')
                   , ('reason', 'desc')
                   )
    }),
                 ('内部信息:', {
                     'classes': ('collapse',),
                     'fields': (('buyer_nick', 'mobile', 'phone',),
                                ('item_id', 'sku_id', 'refund_id', 'charge',))

                 }),
                 ('审核信息:', {
                     'classes': ('expand',),
                     'fields': (('has_good_return', 'has_good_change',)
                                , ('refund_num', 'refund_fee')
                                , ('feedback')
                                , ('good_status', 'status'))
                 }),)

    #--------定制控件属性----------------
    formfield_overrides = {
        models.FloatField: {'widget': TextInput(attrs={'size': '8'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 35})},
    }

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = set(self.readonly_fields or [])
        if not request.user.has_perm('pay.sale_refund_manage'):
            readonly_fields.update(('refund_no', 'trade_id', 'order_id', 'payment', 'total_fee',
                                    'reason', 'desc', 'refund_id', 'charge', 'status'))

        return readonly_fields

    def get_changelist(self, request, **kwargs):
        return SaleRefundChangeList

    def response_change(self, request, obj, *args, **kwargs):
        #订单处理页面
        opts = obj._meta
        # Handle proxy models automatically created by .only() or .defer()
        verbose_name = opts.verbose_name
        if obj._deferred:
            opts_ = opts.proxy_for_model._meta
            verbose_name = opts_.verbose_name

        pk_value = obj._get_pk_val()
        if request.POST.has_key("_refund_confirm"):
            try:

                if obj.status in (SaleRefund.REFUND_WAIT_SELLER_AGREE,
                                  SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                  SaleRefund.REFUND_CONFIRM_GOODS):

                    strade = SaleTrade.objects.get(id=obj.trade_id)
                    customer = Customer.objects.get(id=strade.buyer_id)

                    if strade.channel == SaleTrade.WALLET:
                        payment = int(obj.refund_fee * 100)
                        xlmm_queryset = XiaoluMama.objects.filter(openid=customer.unionid)
                        if xlmm_queryset.count() == 0:
                            raise Exception(u'妈妈unoind:%s' % customer.unionid)
                        xlmm = xlmm_queryset[0]
                        clogs = CarryLog.objects.filter(xlmm=xlmm.id,
                                                        order_num=strade.id,
                                                        log_type=CarryLog.REFUND_RETURN)
                        if clogs.count() > 0:
                            raise Exception(u'订单已经退款！！！')

                        CarryLog.objects.create(xlmm=xlmm.id,
                                                order_num=strade.id,
                                                buyer_nick=strade.buyer_nick,
                                                value=payment,
                                                log_type=CarryLog.REFUND_RETURN,
                                                carry_type=CarryLog.CARRY_IN,
                                                status=CarryLog.CONFIRMED)
                        xlmm_queryset.update(cash=models.F('cash') + payment)
                        obj.status = SaleRefund.REFUND_SUCCESS
                        obj.save()

                        obj.refund_Confirm()

                    elif obj.refund_fee > 0 and obj.charge:
                        import pingpp

                        pingpp.api_key = settings.PINGPP_APPKEY
                        ch = pingpp.Charge.retrieve(obj.charge)
                        re = ch.refunds.create(description=obj.refund_desc,
                                               amount=int(obj.refund_fee * 100))
                        obj.refund_id = re.id
                        obj.status = SaleRefund.REFUND_APPROVE
                        obj.save()

                    log_action(request.user.id, obj, CHANGE, '退款审核通过:%s' % obj.refund_id)
                    self.message_user(request, '退款单审核通过')
                else:
                    self.message_user(request, '退款单状态不可申审核')
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                self.message_user(request, '系统出错:%s' % exc.message)

            return HttpResponseRedirect("../%s/" % pk_value)

        elif request.POST.has_key("_refund_refuse"):
            try:
                if obj.status in (SaleRefund.REFUND_WAIT_SELLER_AGREE,
                                  SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                  SaleRefund.REFUND_CONFIRM_GOODS):

                    obj.status = SaleRefund.REFUND_REFUSE_BUYER
                    obj.save()
                    log_action(request.user.id, obj, CHANGE, '驳回重申')
                    self.message_user(request, '驳回成功')
                else:
                    self.message_user(request, '退款单状态不可申审核')
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                self.message_user(request, '系统出错:%s' % exc.message)

            return HttpResponseRedirect("../%s/" % pk_value)

        return super(SaleRefundAdmin, self).response_change(request, obj, *args, **kwargs)


admin.site.register(SaleRefund, SaleRefundAdmin)

from django.db.models import Sum
from django.shortcuts import redirect, render_to_response, RequestContext
from .models_envelope import Envelop
from .forms import EnvelopForm


class EnvelopAdmin(admin.ModelAdmin):
    list_display = ('id', 'receiver', 'get_amount_display', 'platform', 'subject',
                    'send_time', 'created', 'send_status', 'status')

    list_filter = ('status', 'send_status', 'platform', 'subject', 'livemode', ('created', DateFieldListFilter))
    search_fields = ['=receiver', '=envelop_id']
    list_per_page = 50
    form = EnvelopForm

    def send_envelop_action(self, request, queryset):
        """ 发送红包动作 """

        wait_envelop_qs = queryset

        envelop_ids = ','.join([str(e.id) for e in wait_envelop_qs])
        envelop_count = wait_envelop_qs.count()
        total_amount = wait_envelop_qs.aggregate(total_amount=Sum('amount')).get('total_amount') or 0

        origin_url = request.get_full_path()

        return render_to_response('pay/confirm_envelop.html',
                                  {'origin_url': origin_url,
                                   'envelop_ids': envelop_ids,
                                   'total_amount': total_amount / 100.0,
                                   'envelop_count': envelop_count},
                                  context_instance=RequestContext(request),
                                  mimetype="text/html")

    send_envelop_action.short_description = u"发送微信红包"

    def cancel_envelop_action(self, request, queryset):
        """ 取消红包动作 """

        wait_envelop_qs = queryset.filter(status__in=(Envelop.WAIT_SEND, Envelop.FAIL))
        envelop_ids = [e.id for e in wait_envelop_qs]

        for envelop in wait_envelop_qs:
            envelop.status = Envelop.CANCEL
            envelop.save()
            log_action(request.user.id, envelop, CHANGE, u'取消红包')

        envelop_qs = Envelop.objects.filter(id__in=envelop_ids, status=Envelop.CANCEL)

        self.message_user(request, u'已取消%s个红包!' % envelop_qs.count())

        origin_url = request.get_full_path()

        return redirect(origin_url)

    cancel_envelop_action.short_description = u"取消发送红包"

    actions = ['send_envelop_action', 'cancel_envelop_action']


admin.site.register(Envelop, EnvelopAdmin)

from flashsale.pay.models_custom import ModelProduct


class ModelProductAdmin(admin.ModelAdmin):

    list_display = ('name', 'head_imgs', 'content_imgs', 'buy_limit', 'per_limit', 'sale_time', 'status')

    list_filter = ('name', 'sale_time', 'status',
                   ('created',DateFieldListFilter))
    #-------------- 页面布局 --------------
    fieldsets = (('基本信息:', {'classes': ('expand',),
                    'fields': (('name',), ('head_imgs', 'content_imgs')
                               , ('buy_limit', 'per_limit', 'sale_time', 'status'))}),)
    search_fields = ['name', ]
    list_per_page = 50

admin.site.register(ModelProduct, ModelProductAdmin)

from flashsale.pay.models_custom import GoodShelf

class GoodShelfAdmin(admin.ModelAdmin):
    
    list_display = ('id','title','wem_posters','chd_posters','is_active',
                    'active_time','created')
    
    list_filter = ('is_active',('active_time',DateFieldListFilter),('created',DateFieldListFilter))
    search_fields = ['title']
    list_per_page = 50
   

admin.site.register(GoodShelf, GoodShelfAdmin)


