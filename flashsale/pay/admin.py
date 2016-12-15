# coding: utf-8
import json
import datetime
import hashlib
from cStringIO import StringIO
from django.contrib import admin
from django.db import models
from django.conf import settings
from django.contrib.admin.views.main import ChangeList
from django.forms import TextInput, Textarea, FloatField
from django.http import HttpResponseRedirect

from core.options import log_action, User, ADDITION, CHANGE
from core.filters import DateFieldListFilter
from core.admin import ApproxAdmin, BaseModelAdmin, ExportActionModelAdmin
from core.managers import ApproxCountQuerySet
from core.upload import upload_public_to_remote, generate_public_url
from flashsale.pay.filters import MamaCreatedFilter
from .services import FlashSaleService, get_district_json_data
from .resources import SaleTradeResource
from .models import (
    SaleTrade,
    SaleOrder,
    TradeCharge,
    Customer,
    Register,
    District,
    DistrictVersion,
    UserAddress,
    SaleRefund,
    UserBudget,
    BudgetLog,
    SaleOrderSyncLog,
    FaqMainCategory,
    FaqsDetailCategory,
    SaleFaq,
    CuShopPros,
    CustomerShops,
    Envelop,
    Integral,
    IntegralLog,
    TeamBuy,
    ADManager
)

import cStringIO as StringIO
from common.utils import gen_cvs_tuple, CSVUnicodeWriter
from django.http import HttpResponse
import time
from django.db.models import Sum
from django.shortcuts import redirect, render
from .forms import EnvelopForm, CustomShareForm
from shopapp.weixin.models import WeixinUnionID

import logging

logger = logging.getLogger(__name__)


class SaleOrderInline(admin.TabularInline):
    model = SaleOrder
    fields = ('oid', 'outer_id', 'title', 'outer_sku_id', 'sku_name', 'payment',
              'num', 'discount_fee', 'refund_fee', 'refund_status', 'status', 'item_id')

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '16'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 20})},
    }

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = set(self.readonly_fields + ('oid',))
        if not request.user.is_superuser:
            readonly_fields.update(('outer_id', 'outer_sku_id', 'item_id'))
        return tuple(readonly_fields)


class SaleOrderAdmin(ApproxAdmin):
    list_display = (
    'id', 'show_trade', 'package_sku_item_link_to', 'outer_id', 'title',
    'outer_sku_id', 'sku_name', 'payment', 'pay_time','num', 'discount_fee',
    'refund_fee', 'refund_status', 'status', 'sign_time', 'item_id')
    list_display_links = ('id',)
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('status', 'refund_status', ('pay_time', DateFieldListFilter), ('sign_time', DateFieldListFilter))
    search_fields = ['=id', '^oid', '=sale_trade__tid', '=sale_trade__receiver_mobile', '=outer_id']

    def show_trade(self, obj):
        return '<a href="/admin/pay/saletrade/?id=%(trade_id)d">%(trade_id)d</a>' % {'trade_id': obj.sale_trade_id}

    show_trade.allow_tags = True
    show_trade.short_description = '订单ID'

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ('sale_trade', 'oid', 'buyer_id')

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


admin.site.register(SaleOrder, SaleOrderAdmin)


class SaleTradeAdmin(ExportActionModelAdmin):
    list_display = (
        'id_link', 'tid', 'buyer_nick', 'channel', 'order_type', 'is_boutique', 'total_fee', 'payment', 'pay_time', 'created', 'status',
        'buyer_info')
    list_display_links = ('tid', 'buyer_info')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = (
        'status', 'channel', 'is_boutique', 'has_budget_paid', 'order_type', ('pay_time', DateFieldListFilter),
        ('created', DateFieldListFilter))
    search_fields = ['=tid', '=id', '=receiver_mobile', '=buyer_id']
    list_per_page = 20
    inlines = [SaleOrderInline]
    resource_class = SaleTradeResource

    # -------------- 页面布局 --------------
    fieldsets = ((u'订单基本信息:', {
        'classes': ('expand',),
        'fields': (('tid', 'buyer_nick', 'channel', 'status')
                   , ('trade_type', 'order_type', 'pay_cash', 'has_budget_paid', 'is_boutique')
                   , ('total_fee', 'payment', 'post_fee', 'discount_fee')
                   , ('pay_time', 'consign_time', 'charge')
                   , ('buyer_id', 'openid', 'extras_info')
                   , ('buyer_message', 'seller_memo',)
                   )
    }),
                 (u'收货人及物流信息:', {
                     'classes': ('expand',),
                     'fields': (('receiver_name', 'receiver_state', 'receiver_city', 'receiver_district')
                                , ('receiver_address', 'receiver_zip', 'receiver_mobile', 'receiver_phone')
                                , ('logistics_company', 'out_sid'))
                 }),
                 )

    # --------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '16'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 35})},
    }

    def queryset(self, request):
        qs = super(BaseModelAdmin, self).queryset(request)
        return qs._clone(klass=ApproxCountQuerySet)

    def save_model(self, request, obj, form, change):
        if hasattr(obj, 'creator') and not getattr(obj, 'creator'):
            obj.creator = request.user.username
        obj.save()

    def detail_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = {'title': u'特卖订单详情'}
        return self.detailform_view(request, object_id, form_url, extra_context)

    def id_link(self, obj):
        return ('<a href="%(url)s" target="_blank">'
                '%(show_text)s</a>') % {
                   'url': '/admin/pay/saletrade/%d/' % obj.id,
                   'show_text': str(obj.id)
               }

    id_link.allow_tags = True
    id_link.short_description = u"ID"

    def buyer_info(self, obj):
        # type : () -> SaleTrade
        mama_id = obj.order_buyer.mama_id
        customer_i = u'<a target="_blank" href="/admin/pay/customer/?id=%s">C: %s</a>' % (obj.buyer_id, obj.buyer_id)
        mama_i = u'<a target="_blank" href="/admin/xiaolumm/xiaolumama/?id=%s">M: %s</a>' % (mama_id, mama_id)
        return u' | '.join([customer_i, mama_i])
    buyer_info.allow_tags = True
    buyer_info.short_description = u"用户id | 妈妈id"

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


class TradeChargeAdmin(BaseModelAdmin):
    list_display = ('id', 'order_no', 'charge', 'channel', 'amount', 'time_paid', 'paid', 'created', 'refunded')
    list_display_links = ('order_no', 'charge',)

    list_filter = (('time_paid', DateFieldListFilter), 'paid', 'refunded')
    search_fields = ['=order_no', '=charge']


admin.site.register(TradeCharge, TradeChargeAdmin)


class RegisterAdmin(ApproxAdmin):
    list_display = ('id', 'cus_uid', 'vmobile', 'created', 'modified')
    list_display_links = ('id', 'cus_uid')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = (('code_time', DateFieldListFilter), ('created', DateFieldListFilter), 'initialize_pwd')
    search_fields = ['=id', '=cus_uid', '=vmobile', '=vemail']


admin.site.register(Register, RegisterAdmin)


class CustomerAdmin(ApproxAdmin):
    list_display = ('id', 'user', 'mama_id', 'thumbnail_display', 'mobile', 'unionid', 'created', 'modified', 'status')
    list_display_links = ('id', 'thumbnail_display',)

    list_filter = ('status',)
    search_fields = ['=id', '=mobile', '=openid', '=unionid']

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ('user',)

    def thumbnail_display(self, obj):
        html = u'<p>%s</p><img src="%s" style="width:60px; height:60px">' % (obj.nick, obj.thumbnail)
        return html
    thumbnail_display.allow_tags = True
    thumbnail_display.short_description = u"粉丝昵称/头像"


admin.site.register(Customer, CustomerAdmin)


class DistrictAdmin(ApproxAdmin):
    list_display = ('id', 'name', 'full_name', 'parent_id', 'grade', 'zipcode', 'sort_order', 'is_valid')
    search_fields = ['=id', '=parent_id', '^name']

    list_filter = ('grade', 'is_valid')


admin.site.register(District, DistrictAdmin)


class DistrictVersionAdmin(ApproxAdmin):
    list_display = ('id', 'version', 'hash256', 'memo', 'status')
    search_fields = ['=id', '=version', '=hash256']

    list_filter = ('status',)

    def response_change(self, request, obj, *args, **kwargs):
        # 订单处理页面
        obj.status = False
        if not obj.download_url:
            try:
                districts_data = get_district_json_data()
                districts_jsonstring = json.dumps(districts_data, indent=2)
                string_io = StringIO.StringIO(districts_jsonstring)
                resp = upload_public_to_remote(obj.gen_filepath(), string_io)
                obj.hash256 = hashlib.sha1(districts_jsonstring).hexdigest()
                logger.info('upload public resp:%s' % resp)
                if resp.status_code != 200:
                    obj.memo += u'地址数据文件上传异常:%s' % resp.text_body
                    obj.save(update_fields=['memo', 'hash256'])
                    raise Exception(u'地址数据文件上传异常:%s' % resp.text_body)

                obj.download_url = generate_public_url(obj.gen_filepath())
                obj.status = True
                obj.save(update_fields=['download_url', 'memo', 'hash256', 'status'])
            except Exception, exc:
                self.message_user(request, u"区划版本更新失败：%s" % (exc.message))
                logger.error(u"区划版本更新失败：%s" % (exc.message), exc_info=True)

        return super(DistrictVersionAdmin, self).response_change(request, obj, *args, **kwargs)


admin.site.register(DistrictVersion, DistrictVersionAdmin)


class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'cus_uid', 'receiver_name', 'receiver_state',
                    'receiver_city', 'receiver_mobile', 'default', 'status')
    search_fields = ['=cus_uid', '^receiver_mobile']

    list_filter = ('default', 'status')


admin.site.register(UserAddress, UserAddressAdmin)


class SaleRefundChangeList(ChangeList):
    def get_queryset(self, request):
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
                                                    models.Q(sid=search_q) |
                                                    models.Q(trade_id=search_q))
            else:
                return super(SaleRefundChangeList, self).get_queryset(request)
            return refunds

        return super(SaleRefundChangeList, self).get_queryset(request)


from mall.xiaolupay import apis as xiaolupay

from flashsale.xiaolumm.models import XiaoluMama, CarryLog
from .filters import Filte_By_Reason
from .tasks import notifyTradeRefundTask


class SaleRefundAdmin(BaseModelAdmin):
    list_display = ('id_link', 'buyer_id', 'order_no', 'package_sku_item_link_to', 'channel', 'refund_channel',
                    'refund_fee_info', 'has_good_return', 'has_good_change', 'created',
                    'success_time',
                    'is_lackrefund', 'refund_pro_link')

    list_filter = (
        'status', 'good_status', 'channel', 'is_lackrefund', 'has_good_return', 'has_good_change', Filte_By_Reason,
        "created", "modified")
    list_display_links = []
    search_fields = ['=refund_no', '=trade_id', '=order_id', '=refund_id', '=mobile']
    list_per_page = 5

    def id_link(self, obj):
        return ('<a href="%(url)s" target="_blank">'
                '%(show_text)s</a>') % {
                   'url': '/admin/pay/salerefund/%d/' % obj.id,
                   'show_text': str(obj.id)
               }

    id_link.allow_tags = True
    id_link.short_description = u"ID"

    def detail_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = {'title': u'退件详情'}
        return self.detailform_view(request, object_id, form_url, extra_context)

    PACKAGE_SKU_ITEM_LINK = (
        '<a href="%(pki_url)s" target="_blank">'
        '%(oid)s</a>')

    def package_sku_item_link_to(self, obj):
        return '%s <br>' % obj.sku_id + self.PACKAGE_SKU_ITEM_LINK % {
            'pki_url': '/admin/trades/packageskuitem/?sale_order_id=%s' % obj.order_id,
            'oid': obj.order_id
        }

    package_sku_item_link_to.allow_tags = True
    package_sku_item_link_to.short_description = u'SKU/包裹Item'

    def refund_fee_info(self, obj):
        # type: (SaleRefund) -> text_type
        html1 = '<br><label>立即执行:<input type="checkbox" id="im-execute-%s" onclick="setCheckBox(%s)"/></label>' % (obj.id, obj.id)
        bls = obj.get_refund_budget_logs().values('id', 'flow_amount')
        bids = [str(i['id'])for i in bls]
        vs = [str(j['flow_amount'] / 100.0) for j in bls]
        html2 = "<a target='_blank' href='/admin/pay/budgetlog/?id__in=%s'>钱包:%s</a>" % (','.join(bids), ' | '.join(vs))

        postages = obj.get_refund_postage_budget_logs().values('id', 'flow_amount')
        pbids = [str(i['id']) for i in postages]
        pvs = [(j['flow_amount'] / 100.0) for j in postages]

        postage_input = '<input style="padding: 5px 0px; width: 50px" type="text" id="refundPostage-%s" value="%s" ' \
                        'onkeydown="return refundPostage(%s)"/>' % (obj.id, str(obj.postage_num / 100.0), obj.id)
        html3 = "<a target='_blank' href='/admin/pay/budgetlog/?id__in=%s'>邮费　 :%s</a>　%s" % (','.join(pbids),
                                                                                                str(sum(pvs)),
                                                                                                postage_input)

        coupons = obj.get_refund_coupons().values('id', 'value')
        cids = [str(i['id']) for i in coupons]
        cs = [str(j['value']) for j in coupons]
        html4 = "<a target='_blank' href='/admin/coupon/usercoupon/?id__in=%s'>优惠券 :%s</a>　" % (','.join(cids), ' | '.join(cs))

        ctpl = obj.refund_coupon_template
        coupon_selected = ctpl.value if ctpl else u'请选择'
        select = '<select style="padding: 0px 0px" id="refundCoupon-%s"onChange="refundCoupon(%s)">' \
                 '<option value="0" selected="selected">%s</option>' \
                 '<option value="7">￥5</option>' \
                 '<option value="2">￥10</option>' \
                 '<option value="8">￥15</option>' \
                 '<option value="10">￥20</option>' \
                 '</select>' % (obj.id, obj.id, coupon_selected)
        return '<br>'.join([str(obj.refund_fee), html2, html1, html3, html4 + select])

    refund_fee_info.allow_tags = True
    refund_fee_info.short_description = u'退款费用信息'

    def order_no(self, obj):
        # type: () -> text_type
        html1 = '订单:<a href="/admin/pay/saletrade/%s/change" target="_blank">%s</a><br>%s<br>%s' % (
        obj.trade_id, obj.sale_trade.tid, obj.title, obj.saleorder.get_status_display())
        html2 = '退款单:<a href="/admin/pay/salerefund/%s/change" target="_blank">%s</a><br>%s' % (obj.id, obj.refund_no, obj.get_status_display())
        return '<br><br>'.join([html1, html2])

    order_no.allow_tags = True
    order_no.short_description = "编号信息"

    def refund_pro_link(self, obj):
        html = obj.sid
        if obj.sid:  # 如果是退回了(在退回商品中有找到)
            if obj.refundproduct:
                html = "<a href='/admin/refunds/refundproduct/?out_sid={0}' style='color:green'>{0}></a>".format(
                    obj.refundproduct.out_sid)
            else:
                html = "<a style='color:red'>{0}</a>".format(obj.sid)
        return html

    refund_pro_link.allow_tags = True
    refund_pro_link.short_description = "退回快递单号"

    # -------------- 页面布局 --------------
    fieldsets = (
        ('基本信息:', {
            'classes': ('expand',),
            'fields': (
                ('refund_no', 'trade_id', 'order_id')
                , ('buyer_id', 'title', 'sku_name',)
                , ('payment', 'total_fee',)
                , ('company_name', 'sid')
                , ('reason', 'desc', 'proof_pic')
            )
        }),
        ('内部信息:', {
             'classes': ('collapse',),
             'fields': (
                ('buyer_nick', 'mobile', 'phone',),
                ('item_id', 'sku_id', 'refund_id', 'charge',),
                ('amount_flow'),
                ('postage_num', 'coupon_num')
            )
        }),
        ('审核信息:', {
         'classes': ('expand',),
         'fields': (('has_good_return', 'has_good_change',)
                    , ('refund_num', 'refund_fee')
                    , ('feedback')
                    , ('good_status', 'status'))
        }),
    )

    # --------定制控件属性----------------
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
        if request.POST.has_key("_refund_confirm"):
            try:
                if obj.status in (SaleRefund.REFUND_WAIT_SELLER_AGREE,
                                  SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                  SaleRefund.REFUND_CONFIRM_GOODS):
                    obj.refund_payment_2_budget()
                    log_action(request.user.id, obj, CHANGE, u'退款审核通过:%s' % obj.refund_id)
                    self.message_user(request, u'退款单审核通过')
                else:
                    self.message_user(request, u'退款单状态不可审核')
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                self.message_user(request, u'系统出错:%s' % exc.message)
            return HttpResponseRedirect("./")

        elif request.POST.has_key("_refund_refuse"):
            try:
                if obj.refund_refuse():
                    log_action(request.user.id, obj, CHANGE, u'驳回重申')
                    self.message_user(request, u'驳回成功')
                else:
                    self.message_user(request, u'退款单状态不可申审核')
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                self.message_user(request, u'系统出错:%s' % exc.message)
            return HttpResponseRedirect("./")

        # elif request.POST.has_key("_refund_invoke"):
        #     try:
        #         strade = SaleTrade.objects.get(id=obj.trade_id)
        #         if (obj.status == SaleRefund.REFUND_APPROVE and
        #                     strade.channel != SaleTrade.WALLET and
        #                 obj.refund_id.strip()):
        #
        #             ch = xiaolupay.Charge.retrieve(strade.charge)
        #             rf = ch.refunds.retrieve(obj.refund_id)
        #             if rf.status == 'failed':
        #                 rf = ch.refunds.create(description=obj.get_refund_desc(),
        #                                        amount=int(obj.refund_fee * 100))
        #                 obj.refund_id = rf.id
        #                 obj.save()
        #             else:
        #                 notifyTradeRefundTask(rf)
        #             log_action(request.user.id, obj, CHANGE, '重新退款:refund=%s' % rf.id)
        #             self.message_user(request, '退款申请成功，等待返款。')
        #         else:
        #             self.message_user(request, '订单退款状态异常')
        #     except Exception, exc:
        #         logger.error(exc.message, exc_info=True)
        #         self.message_user(request, '系统出错:%s' % exc.message)
        #
        #     return HttpResponseRedirect("./")
        #
        # elif request.POST.has_key("_refund_complete"):
        #     try:
        #         if obj.status == SaleRefund.REFUND_APPROVE:
        #             # obj.status = SaleRefund.REFUND_SUCCESS
        #             # obj.save()
        #             obj.refund_confirm()
        #             log_action(request.user.id, obj, CHANGE, '确认退款完成:%s' % obj.refund_id)
        #             self.message_user(request, '确认退款已完成')
        #         else:
        #             self.message_user(request, '退款尚未完成')
        #     except Exception, exc:
        #         logger.error(exc.message, exc_info=True)
        #         self.message_user(request, '系统出错:%s' % exc.message)
        #     return HttpResponseRedirect("./")

        return super(SaleRefundAdmin, self).response_change(request, obj, *args, **kwargs)

    # 添加导出退款单功能
    def export_Refund_Product_Action(self, request, queryset):
        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        pcsv = []
        pcsv.append((u'退款编号', u'交易编号', u'出售标题', u'退款费用', u'是否退货'))

        for rf in queryset:
            strade = SaleTrade.objects.get(id=rf.trade_id)
            pcsv.append((rf.refund_no, strade.tid, rf.title, str(rf.refund_fee), str(rf.has_good_return)))

        pcsv.append(['', '', '', '', ''])
        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)
        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=sale_refund-info-%s.csv' % str(int(time.time()))
        return response

    export_Refund_Product_Action.short_description = u"导出订单信息"
    actions = ['export_Refund_Product_Action', ]

    PKI_LINK = (
        '<a href="%(pki_url)s" target="_blank">'
        '%(order_id)s</a>')

    def pki_link_to(self, obj):
        return self.PKI_LINK % {
            'pki_url': '/admin/trades/packageskuitem/?sale_order_id=%s' % obj.order_id,
            'order_id': obj.order_id
        }

    pki_link_to.allow_tags = True
    pki_link_to.short_description = u'交易单ID'

    class Media:
        css = {"all": ()}
        js = (
            '/static/jquery/jquery-2.1.1.min.js',
            "/static/layer-v1.9.2/layer/layer.js",
            "/static/layer-v1.9.2/layer/extend/layer.ext.js",
            "/static/salerefund/js/salerefund.js",
        )


admin.site.register(SaleRefund, SaleRefundAdmin)


def get_mama_id(obj):
    unionid = WeixinUnionID.objects.filter(openid=obj.recipient).first()
    if unionid:
        mama = XiaoluMama.objects.filter(openid=unionid.unionid).first()
        return mama.id if mama else ''
    else:
        return ''
get_mama_id.short_description = '小鹿妈妈ID'

def get_customer_id(obj):
    unionid = WeixinUnionID.objects.filter(openid=obj.recipient).first()
    if unionid:
        customer = Customer.objects.filter(unionid=unionid.unionid).first()
        return customer.id if customer else ''
    else:
        return ''
get_customer_id.short_description = '用户ID'


def get_mama_created(obj):
    unionid = WeixinUnionID.objects.filter(openid=obj.recipient).first()
    if unionid:
        mama = XiaoluMama.objects.filter(openid=unionid.unionid).first()
        return mama.created if mama else ''
    else:
        return ''
get_mama_created.short_description = '小鹿妈妈创建时间'


class EnvelopAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'receiver', get_mama_id, get_customer_id, 'get_amount_display', 'platform', 'subject',
        'send_time', 'created', 'send_status', 'status',
        get_mama_created
    )

    list_filter = (
        'status', 'send_status', 'platform', 'subject', 'livemode',
        ('created', DateFieldListFilter),
        MamaCreatedFilter,
    )
    search_fields = ['=receiver', '=envelop_id', '=recipient']
    list_per_page = 50
    form = EnvelopForm

    def send_envelop_action(self, request, queryset):
        """ 发送红包动作 """

        wait_envelop_qs = queryset
        envelop_ids = ','.join([str(e.id) for e in wait_envelop_qs])
        envelop_count = wait_envelop_qs.count()
        total_amount = wait_envelop_qs.aggregate(total_amount=Sum('amount')).get('total_amount') or 0

        origin_url = request.get_full_path()

        return render(
            request,
            'pay/confirm_envelop.html',
              {'origin_url': origin_url,
               'envelop_ids': envelop_ids,
               'total_amount': total_amount / 100.0,
               'envelop_count': envelop_count},
              content_type="text/html"
        )

    send_envelop_action.short_description = u"发送微信红包"

    def cancel_envelop_action(self, request, queryset):
        """ 取消红包动作 """

        wait_envelop_qs = queryset.filter(status__in=(Envelop.WAIT_SEND, Envelop.CONFIRM_SEND, Envelop.FAIL))
        envelop_ids = [e.id for e in wait_envelop_qs]

        for envelop in wait_envelop_qs:
            if envelop.cancel_envelop():
                log_action(request.user.id, envelop, CHANGE, u'取消红包')

        envelop_qs = Envelop.objects.filter(id__in=envelop_ids, status=Envelop.CANCEL)

        self.message_user(request, u'已取消%s个红包!' % envelop_qs.count())

        origin_url = request.get_full_path()

        return redirect(origin_url)

    cancel_envelop_action.short_description = u"取消发送红包"

    actions = [
        'send_envelop_action',
        'cancel_envelop_action',
    ]


admin.site.register(Envelop, EnvelopAdmin)

from flashsale.pay.models import ModelProduct, BrandEntry, BrandProduct


class BrandProductInline(admin.TabularInline):
    model = BrandProduct
    fields = ('product_name', 'product_img', 'model_id', 'start_time', 'end_time',)


class ModelProductAdmin(ApproxAdmin):
    list_display = ('id', 'name', 'sale_time', 'salecategory', 'product_type', 'is_onsale', 'is_recommend', 'is_topic',
                    'is_flatten', 'is_teambuy', 'is_boutique', 'product_type', 'status', 'shelf_status', 'onshelf_time', 'offshelf_time',
                    'lowest_agent_price', 'lowest_std_sale_price', 'order_weight', 'created')

    list_filter = ('status',
                   'product_type',
                   'shelf_status',
                   'is_boutique',
                   'is_onsale',
                   'is_recommend',
                   'is_topic',
                   'is_flatten',
                   ('onshelf_time', DateFieldListFilter),
                   ('created', DateFieldListFilter))
    # -------------- 页面布局 --------------
    fieldsets = (('基本信息:',
                  {'classes': ('expand',),
                   'fields': (
                       ('name', 'salecategory', 'saleproduct'),
                       ('lowest_agent_price', 'lowest_std_sale_price'),
                       ('is_onsale', 'is_recommend', 'is_topic', 'is_flatten', 'is_teambuy', 'is_boutique', 'product_type'),
                       ('shelf_status', 'onshelf_time', 'offshelf_time'),
                       ('order_weight', 'rebeta_scheme_id', 'status'),
                       ('head_imgs', 'content_imgs'),
                       ('teambuy_price', 'teambuy_person_num'),
                       ('extras',),
                   )
                   }),
                 )
    readonly_fields = ('saleproduct', )
    search_fields = ['name', '=id']
    list_per_page = 50

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            self.readonly_fields += ('onshelf_time', 'offshelf_time')
        return self.readonly_fields


admin.site.register(ModelProduct, ModelProductAdmin)

from flashsale.pay.models import GoodShelf


class GoodShelfAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_active', 'active_time', 'created', 'preview_link')

    list_filter = ('is_active', ('active_time', DateFieldListFilter), ('created', DateFieldListFilter))
    search_fields = ['title']
    list_per_page = 25

    def preview_link(self, obj):
        if obj.active_time:
            pre_days = (obj.active_time.date() - datetime.date.today()).days
            return u'<a href="http://m.xiaolumeimei.com/preview.html?days=%s">预览一下</a>' % pre_days
        return u''

    preview_link.allow_tags = True
    preview_link.short_description = u"预览"


admin.site.register(GoodShelf, GoodShelfAdmin)


class BrandEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand_name', 'start_time', 'end_time', 'created', 'is_active')

    list_filter = ('is_active', ('start_time', DateFieldListFilter), ('created', DateFieldListFilter))
    search_fields = ['brand_name']
    list_per_page = 25

    inlines = [BrandProductInline]

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': 128})},
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 128})},
    }


# admin.site.register(BrandEntry, BrandEntryAdmin)


class BrandProductAdmin(ApproxAdmin):
    list_display = ('id', 'brand_name', 'product_name', 'product_img', 'model_id', 'start_time', 'end_time')

    list_filter = (('start_time', DateFieldListFilter), ('end_time', DateFieldListFilter))
    search_fields = ['brand_name']
    list_per_page = 25

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': 128})},
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 128})},
    }


# admin.site.register(BrandProduct, BrandProductAdmin)


class IntegralAdmin(admin.ModelAdmin):
    list_display = ('id', 'integral_user', 'integral_value', 'created', 'modified')
    list_filter = ('created',)
    search_fields = ['=integral_user', ]
    list_per_page = 50


admin.site.register(Integral, IntegralAdmin)


class IntegralLogAdmin(admin.ModelAdmin):
    list_display = (
        'integral_user', 'order_id', 'mobile', 'log_value', 'log_status', 'log_type', 'in_out', 'created', 'modified')
    list_filter = ('created', 'log_status', 'log_type', 'in_out',)
    search_fields = ['=integral_user', '=mobile']
    list_per_page = 50


admin.site.register(IntegralLog, IntegralLogAdmin)

######################################################################

from flashsale.pay.models import ShoppingCart


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer_id', 'buyer_nick', 'item_id',
                    'title', 'price', 'sku_id', 'num',
                    'total_fee', 'sku_name',
                    'created', 'remain_time', 'status')
    list_filter = ('created', 'status')
    search_fields = ['=item_id', '=buyer_id', ]


admin.site.register(ShoppingCart, ShoppingCartAdmin)

########################################################################

from .models import CustomShare


class CustomShareAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'share_type', 'share_img', 'status', 'active_at', 'created')
    list_display_links = ('id', 'title',)

    list_filter = ('status', 'share_type')
    search_fields = ['=id', 'title']
    form = CustomShareForm


admin.site.register(CustomShare, CustomShareAdmin)

from .filters import CushopProCategoryFiler
import constants


class CuShopProsAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'customer', 'pro_category_dec', 'product',
                    'model', 'pro_status', 'position', 'created')
    list_display_links = ('shop',)
    list_filter = ('created', 'pro_status', CushopProCategoryFiler)
    search_fields = ['=id', '=model', '=shop', '=product', '=customer']

    def pro_category_dec(self, obj):
        """
        优惠券统计数字
        发放数量, 使用数量
        """
        if obj.pro_category in constants.CHILD_CID_LIST:
            return u'<span>童装</span>'
        elif obj.pro_category in constants.FEMALE_CID_LIST:
            return u'<span>女装</span>'
        else:
            return u''

    def upload_products(self, request, queryset):
        queryset.update(pro_status=CuShopPros.UP_SHELF)
        count = queryset.count()
        return self.message_user(request, '成功上架%s个产品!' % count)

    upload_products.short_description = u'上架选中商品'

    actions = ['upload_products', ]

    pro_category_dec.allow_tags = True
    pro_category_dec.short_description = u"分类"


admin.site.register(CuShopPros, CuShopProsAdmin)


class CustomShopadmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created')
    list_display_links = ('name',)
    list_filter = ('created',)
    search_fields = ['=id', 'name']


admin.site.register(CustomerShops, CustomShopadmin)


class UserBudgetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'mama_id', 'amount', 'pending_cash', 'total_income', 'total_expense', 'created')
    list_display_links = ('id',)

    #     list_filter = ('status',)
    search_fields = ['=id', '=user__mobile', '=user__id']

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ('user',)


admin.site.register(UserBudget, UserBudgetAdmin)


class BudgetLogAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer_id', 'mama_id', 'flow_amount', 'budget_type', 'budget_log_type', 'referal_id', 'uni_key', 'modified', 'created', 'status')
    list_display_links = ('id',)

    list_filter = ('budget_type', 'budget_log_type', 'status', 'modified')
    search_fields = ['=id', '=customer_id']

    # def get_readonly_fields(self, request, obj=None):
    # return self.readonly_fields + ('user',)


admin.site.register(BudgetLog, BudgetLogAdmin)


class FaqMainCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name')
    list_display_links = ('id', 'category_name')

    list_filter = ('created',)
    search_fields = ['=id', ]


admin.site.register(FaqMainCategory, FaqMainCategoryAdmin)


class FaqsDetailCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name')
    list_display_links = ('id', 'category_name')

    list_filter = ('created',)
    search_fields = ['=id', ]


admin.site.register(FaqsDetailCategory, FaqsDetailCategoryAdmin)


class SaleFaqAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'main_category')
    list_display_links = ('id', 'question', 'main_category')

    list_filter = ('created',)
    search_fields = ['=id', ]


admin.site.register(SaleFaq, SaleFaqAdmin)


class SaleOrderSyncLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'time_from', 'time_to', 'target_num', 'actual_num', 'type', 'status', 'modified', 'created')

    list_filter = ('type', 'status')


admin.site.register(SaleOrderSyncLog, SaleOrderSyncLogAdmin)


class TeamBuyAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku_id', 'status', 'limit_time', 'creator')

    list_filter = ('status',)


admin.site.register(TeamBuy, TeamBuyAdmin)


class ADManagerAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'image', 'url', 'status')

admin.site.register(ADManager, ADManagerAdmin)
