# -*- coding:utf8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User as DjangoUser
from shopback.refunds.models import Refund, RefundProduct
from shopback.trades.models import MergeTrade,PackageOrder,PackageSkuItem
from flashsale.pay.models import SaleTrade
from shopback.items.models import Product, ProductSku
import datetime, time

__author__ = 'meixqhi'
import cStringIO as StringIO
from django.http import HttpResponse, HttpResponseRedirect
from common.utils import gen_cvs_tuple, CSVUnicodeWriter


class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_id', 'tid', 'oid', 'num_iid', 'buyer_nick', 'total_fee', 'refund_fee', 'payment'
                    , 'company_name', 'sid', 'has_good_return', 'is_reissue', 'created', 'good_status', 'order_status',
                    'status')
    list_display_links = ('refund_id', 'tid', 'buyer_nick')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']

    # --------设置页面布局----------------
    fieldsets = (('重要信息', {
        'classes': ('expand',),
        'fields': (('tid', 'user', 'buyer_nick'),
                   ('has_good_return', 'good_status', 'status'),
                   'desc')
    }),
                 ('参考信息:', {
                     'classes': ('collapse',),
                     'fields': (('oid', 'title', 'seller_id', 'seller_nick'),
                                ('num_iid', 'total_fee', 'refund_fee', 'payment')
                                , ('company_name', 'sid', 'is_reissue')
                                , ('cs_status', 'order_status', 'reason'))
                 }))

    # --------定制控件属性----------------
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '16'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 35})},
    }

    list_filter = ('user', 'has_good_return', 'good_status', 'is_reissue', 'order_status', 'status',)
    search_fields = ['refund_id', 'tid', 'oid', 'sid', 'buyer_nick']

    # 标记为已处理
    def tag_as_finished(self, request, queryset):
        http_referer = request.META.get('HTTP_REFERER')
        for refund in queryset:
            refund.is_reissue = True
            refund.save()

        return HttpResponseRedirect(http_referer)

    tag_as_finished.short_description = u"标记为已处理"

    # 更新退货款订单
    def pull_all_refund_orders(self, request, queryset):
        http_referer = request.META.get('HTTP_REFERER')

        from shopback.refunds.tasks import updateAllUserRefundOrderTask
        updateAllUserRefundOrderTask(days=7)

        return HttpResponseRedirect(http_referer)

    pull_all_refund_orders.short_description = u"更新退货款订单"

    actions = ['tag_as_finished', 'pull_all_refund_orders']


admin.site.register(Refund, RefundAdmin)

from .filters import RefundMonthFilter, BoyGirlWomen


class RefundProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'outer_id', 'title', 'outer_sku_id', 'show_Product_Price', 'buyer_nick', 'buyer_mobile',
                    'buyer_phone', 'trade_id_display'
                    , 'out_sid', 'company', 'can_reuse', 'is_finish', 'created', 'modified', 'memo', 'select_Reason')
    list_display_links = ('id', 'outer_id')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    date_hierarchy = 'created'
    # ordering = ['created_at']
    list_per_page = 20

    list_filter = ('can_reuse', 'is_finish', RefundMonthFilter, BoyGirlWomen)
    search_fields = ['buyer_nick', 'buyer_mobile', 'buyer_phone', 'trade_id', 'out_sid']

    # 标记为已处理
    def tag_as_finished(self, request, queryset):

        http_referer = request.META.get('HTTP_REFERER')
        for prod in queryset:
            prod.is_finish = True
            prod.save()

        return HttpResponseRedirect(http_referer)

    tag_as_finished.short_description = u"标记为已处理"

    def show_Product_Price(self, obj):
        outer_id = obj.outer_id
        outer_sku_id = obj.outer_sku_id
        skus = ProductSku.objects.filter(product__outer_id=outer_id, outer_id=outer_sku_id)
        if skus.exists():
            return skus[0].agent_price
        else:
            return None

    show_Product_Price.allow_tags = True
    show_Product_Price.short_description = u"出售价格"

    def trade_id_display(self, obj):

        # mt = MergeTrade.objects.filter(tid=obj.trade_id).first()
        po = PackageSkuItem.objects.filter(sale_trade_id=obj.trade_id).first()
        if po:
            st = SaleTrade.objects.filter(tid=obj.trade_id).first()
            color = 'red'
            salerefund = obj.get_sale_refund()
            if salerefund and salerefund.status == 7:
                color = 'green'
            trade = u'{0}<br><br>' \
                    u'<a href="/admin/trades/packageorder/?pid={1}" target="_blank">订单</a>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp' \
                    u'<a href="/admin/pay/salerefund/?trade_id={2}&sku_id={3}" ' \
                    u'target="_blank" style="color: {4}">退款单</a>'.format(obj.trade_id, po.package_order_pid,
                                                                         st.id, st.sku_id, color)
            return trade

    trade_id_display.allow_tags = True
    trade_id_display.short_description = u"订单"

    def select_Reason(self, obj):
        reason_id = obj.reason
        reason = obj.get_reason_display()  # 显示当前的退货原因
        select = u'<select class="select_reason" cid="{0}" id="reason_select_{0} " style="width:100px" >' \
                 u"<option value='{2}'>{1}</option>" \
                 u"<option value='0'>其他</option>" \
                 u"<option value='1'>错拍</option>" \
                 u"<option value='2'>缺货</option>" \
                 u"<option value='3'>开线/脱色/脱毛/有色差/有虫洞</option>" \
                 u"<option value='4'>发错货/漏发</option>" \
                 u"<option value='5'>没有发货</option>" \
                 u"<option value='6'>未收到货</option>" \
                 u"<option value='7'>与描述不符</option>" \
                 u"<option value='8'>退运费</option>" \
                 u"<option value='9'>发票问题</option>" \
                 u"<option value='10'>七天无理由退换货</option>" \
                 u'</select>'.format(obj.id, reason, reason_id)

        return select

    def export_Refund_Product_Action(self, request, queryset):
        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        pcsv = []

        pcsv.append((u'ID', u'买家昵称', u'手机', u"原单id", u'出售价格',
                     u'物流单号', u'物流名称', u'商品编码', u'规格编码',
                     u'数量', u'商品名称', u'二次销售', u'处理完成',
                     u'退货原因', u'创建时间'))
        for prod in queryset:
            outer_id = prod.outer_id
            outer_sku_id = prod.outer_sku_id
            skus = ProductSku.objects.filter(product__outer_id=outer_id, outer_id=outer_sku_id)
            price = 0
            if skus.exists():
                price = skus[0].agent_price
            pcsv.append((str(prod.id), prod.buyer_nick, prod.buyer_mobile, prod.trade_id, str(price),
                         prod.out_sid, prod.company, prod.outer_id, prod.outer_sku_id,
                         str(prod.num), prod.title, str(prod.can_reuse), str(prod.is_finish),
                         str(prod.get_reason_display()), str(prod.created)
                         ))

        pcsv.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment; filename=refund-pro-info-%s.csv' % str(int(time.time()))

        return response

    export_Refund_Product_Action.short_description = u"导出退货选中商品信息"

    class Media:
        js = ("js/select_refubd_pro_reason.js",)

    select_Reason.allow_tags = True
    select_Reason.short_description = u"退货原因"

    actions = ['tag_as_finished', 'export_Refund_Product_Action']


admin.site.register(RefundProduct, RefundProductAdmin)

from models_refund_rate import PayRefundRate, PayRefNumRcord, ProRefunRcord


class PayRefundRateAdmin(admin.ModelAdmin):
    list_display = ('id', 'date_cal', 'ref_num', 'pay_num', 'ref_rate', 'created')
    list_display_links = ('id', 'date_cal')
    list_filter = ('date_cal', 'created')
    search_fields = ['=id', '=date_cal']


admin.site.register(PayRefundRate, PayRefundRateAdmin)


class PayRefundRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'date_cal', 'ref_num_out', 'ref_num_in', 'ref_sed_num', 'created')
    list_display_links = ('id', 'date_cal')
    list_filter = ('date_cal', 'created')
    search_fields = ['=id', '=date_cal']


admin.site.register(PayRefNumRcord, PayRefundRecordAdmin)


class ProRefunRcorddAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'ref_num_out', 'ref_num_in', 'ref_sed_num', 'contactor', 'pro_model', 'sale_date',
                    'created')
    list_display_links = ('id', 'product')
    list_filter = ('contactor', 'created')
    search_fields = ['=id', '=product', '=pro_model']


admin.site.register(ProRefunRcord, ProRefunRcorddAdmin)
