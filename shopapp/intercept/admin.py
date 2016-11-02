# -*- coding:utf-8 -*-
import time
import cStringIO as StringIO
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import admin
from django.db import models
from django.conf import settings
from django.contrib import messages
from django.forms import TextInput, Textarea
from django.core.urlresolvers import reverse

from core.options import log_action, User, ADDITION, CHANGE
from core.filters import DateFieldListFilter
from shopback import paramconfig as pcfg
from .models import InterceptTrade
from common.utils import gen_cvs_tuple, CSVUnicodeWriter, update_model_fields


class InterceptTradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer_nick', 'buyer_mobile', 'serial_no', 'trade_id', 'created', 'modified', 'status')
    search_fields = ['buyer_nick', 'buyer_mobile', 'serial_no']

    list_filter = ('status', ('created', DateFieldListFilter))

    class Media:
        css = {"all": ("admin/css/forms.css", "css/admin/dialog.css", "jquery/jquery-ui-1.10.1.css")}
        js = ("script/admin/adminpopup.js", "jquery/jquery-ui-1.8.13.min.js",
              "jquery/addons/jquery.upload.js", "intercept/js/trade.csvfile.upload.js")

    def intercept_trade_action(self, request, queryset):

        queryset = queryset.filter(status=InterceptTrade.UNCOMPLETE)

        for itrade in queryset:
            trades = InterceptTrade.objects.getTradeByInterceptInfo(itrade.buyer_nick,
                                                                    itrade.buyer_mobile,
                                                                    itrade.serial_no)

            if not trades or trades.count() == 0:
                messages.warning(request, u'订单[ %s, %s, %s ]拦截失败' % (itrade.buyer_nick,
                                                                     itrade.buyer_mobile,
                                                                     itrade.serial_no))
                continue

            for merge_trade in trades:
                merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
                merge_trade.sys_memo += u"【订单被拦截】"

                update_model_fields(merge_trade, update_fields=['sys_status',
                                                                'sys_memo'])

                log_action(request.user.id, merge_trade, CHANGE, u'订单被拦截')

            itrade.trade_id = merge_trade.id
            itrade.status = InterceptTrade.COMPLETE
            itrade.save()

        return HttpResponseRedirect(reverse('admin:intercept_intercepttrade_changelist'))

    intercept_trade_action.short_description = u"拦截选中订单"

    def export_tradeinfo_action(self, request, queryset):
        """ 导出拦截订单信息 """

        queryset = queryset.filter(status=InterceptTrade.COMPLETE)
        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        pcsv = []
        pcsv.append((u'订单ID', '原单ID', u'用户ID', u'收货手机', u'下单金额', u'付款时间',
                     u'发货时间', u'系统状态', u'省', u'市', u'详细地址'))

        from shopback.trades.models import MergeTrade

        for itrade in queryset:
            mtrade = MergeTrade.objects.get(id=itrade.trade_id)
            pcsv.append(('%s' % m for m in [mtrade.id, mtrade.tid, mtrade.buyer_nick,
                                            mtrade.receiver_mobile, mtrade.payment, mtrade.pay_time,
                                            mtrade.consign_time, mtrade.get_sys_status_display(),
                                            mtrade.receiver_state, mtrade.receiver_city,
                                            mtrade.receiver_district + mtrade.receiver_address]))

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment;filename=intercept-tradeinfo-%s.csv' % str(int(time.time()))

        return response

    export_tradeinfo_action.short_description = u"导出拦截订单信息"

    def export_orderdetail_action(self, request, queryset):
        """ 导出订单明细信息 """

        queryset = queryset.filter(status=InterceptTrade.COMPLETE)
        is_windows = request.META['HTTP_USER_AGENT'].lower().find('windows') > -1
        pcsv = []
        pcsv.append((u'商品编码', '商品名称', u'规格编码', u'规格名称', u'拍下数量'))

        from shopback.trades.models import MergeTrade
        from shopback.trades.tasks import get_trade_pickle_list_data
        trade_ids = []
        for itrade in queryset:
            trade_ids.append(itrade.id)

        mtrades = MergeTrade.objects.filter(id__in=trade_ids)
        pickle_list = get_trade_pickle_list_data(mtrades)

        for pickle in pickle_list:

            pskus = pickle[1]['skus']
            for sku in pskus:
                pcsv.append(
                    ('%s' % p for p in [pickle[0], pickle[1]['title'], sku[0], sku[1]['sku_name'], sku[1]['num']]))

        tmpfile = StringIO.StringIO()
        writer = CSVUnicodeWriter(tmpfile, encoding=is_windows and "gbk" or 'utf8')
        writer.writerows(pcsv)

        response = HttpResponse(tmpfile.getvalue(), content_type='application/octet-stream')
        tmpfile.close()
        response['Content-Disposition'] = 'attachment;filename=intercept-tradedetail-%s.csv' % str(int(time.time()))

        return response

    export_orderdetail_action.short_description = u"导出订单明细信息"

    actions = ['intercept_trade_action', 'export_tradeinfo_action', 'export_orderdetail_action']


admin.site.register(InterceptTrade, InterceptTradeAdmin)
