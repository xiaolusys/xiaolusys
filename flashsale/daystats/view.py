# coding: utf-8
# __author__ = 'linjie'
import datetime
import re
import random

from django.db.models import Sum, Q
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.template import RequestContext
from django.core.cache import cache

from rest_framework import permissions, viewsets
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

from flashsale.xiaolumm.models import CarryLog
from shopback.trades.models import PackageSkuItem
from .models import DailyStat, PopularizeCost
from flashsale.coupon.models import CouponTransferRecord


# 推广成本分类统计，包含（订单返利，代理补贴，点击补贴，…）
# 可以集成到 [flashsale.daystat] app里面


def get_month_from_date(date_time):
    day_from = datetime.date(date_time.year, date_time.month, 1)  # 这个月的开始时间
    if date_time.month == 12:
        day_to = datetime.date(date_time.year, date_time.month, 31)
    else:
        day_to = datetime.date(date_time.year, date_time.month + 1,
                               1) - datetime.timedelta(1)  # 这个月的第一天减去1天
    date_from = datetime.datetime(day_from.year, day_from.month, day_from.day,
                                  0, 0, 0)  # 上一周的开始时间
    date_to = datetime.datetime(day_to.year, day_to.month, day_to.day, 23, 59,
                                59)  # 上一周的结束时间
    return date_from, date_to


def popularize_Cost(request):
    content = request.GET or request.POST
    daystr = content.get("month", None)
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_month_from_date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_month_from_date(target_date)
    prev_month = datetime.date(date_from.year, date_from.month,
                               date_from.day) - datetime.timedelta(days=1)
    next_month = datetime.date(date_to.year, date_to.month,
                               date_to.day) + datetime.timedelta(days=1)

    date_from = datetime.date(date_from.year, date_from.month, date_from.day)
    date_to = datetime.date(date_to.year, date_to.month, date_to.day)
    popularizes = PopularizeCost.objects.filter(date__gte=date_from,
                                                date__lte=date_to)

    date_dic = {"prev_month": prev_month, "next_month": next_month}
    return render(request, "popularize/popularize_cost.html",
                              {"date_dic": date_dic,
                               'popularizes': popularizes})


class DailyStatsViewSet(viewsets.GenericViewSet):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = 'xiaolumm/daily_stats.html'

    def list(self, request, *args, **kwargs):
        from flashsale.dinghuo.models import OrderList
        from flashsale.pay.models import SaleOrder, SaleTrade
        from flashsale.pay.models import SaleRefund
        from flashsale.pay.models.product import ModelProduct

        if not re.search(r'application/json', request.META['HTTP_ACCEPT']):
            return Response()
        type_ = int(request.GET.get('type') or 0)
        if not type_:
            return Response({'error': '类型错误'})

        data = None
        now = datetime.datetime.now()
        threshold = now - datetime.timedelta(days=3)
        threshold2 = now - datetime.timedelta(days=5)
        threshold3 = now - datetime.timedelta(days=15)
        if type_ == 1:
            q = PackageSkuItem.objects.filter(
                assign_status__in=[PackageSkuItem.NOT_ASSIGNED, PackageSkuItem.ASSIGNED, PackageSkuItem.VIRTUAL_ASSIGNED], type=0
            )
            n_total = q.only('id').count()
            n_delay = q.filter(pay_time__lte=threshold).only('id').count()
            n_s_delay = q.filter(pay_time__lte=threshold2).only('id').count()
            n_ss_delay = q.filter(pay_time__lte=threshold3).only('id').count()
            data = {'n_total': n_total, 'n_delay': n_delay, 'n_s_delay': n_s_delay, 'n_ss_delay': n_ss_delay}
        elif type_ == 2:
            q = SaleRefund.objects.filter(
                status__in=[SaleRefund.REFUND_WAIT_SELLER_AGREE, SaleRefund.REFUND_WAIT_RETURN_GOODS,
                            SaleRefund.REFUND_CONFIRM_GOODS, SaleRefund.REFUND_APPROVE])
            n_total = q.only('id').count()
            n_delay = q.filter(created__lte=threshold).only('id').count()
            n_s_delay = q.filter(created__lte=threshold2).only('id').count()
            n_ss_delay = q.filter(created__lte=threshold3).only('id').count()
            data = {'n_total': n_total, 'n_delay': n_delay, 'n_s_delay': n_s_delay, 'n_ss_delay': n_ss_delay}
        elif type_ == 3:
            q = SaleRefund.objects.filter(status=SaleRefund.REFUND_APPROVE)
            n_total = q.only('id').count()
            n_delay = q.filter(created__lte=threshold).only('id').count()
            n_s_delay = q.filter(created__lte=threshold2).only('id').count()
            n_ss_delay = q.filter(created__lte=threshold3).only('id').count()
            data = {'n_total': n_total, 'n_delay': n_delay, 'n_s_delay': n_s_delay, 'n_ss_delay': n_ss_delay}
        elif type_ == 4:
            q = OrderList.objects.exclude(stage__in=[OrderList.STAGE_COMPLETED, OrderList.STAGE_STATE, OrderList.STAGE_DELETED])
            n_total = q.only('id').count()
            n_delay = q.filter(created__lte=threshold.date()).only('id').count()
            n_s_delay = q.filter(created__lte=threshold2.date()).only('id').count()
            n_ss_delay = q.filter(created__lte=threshold3.date()).only('id').count()
            data = {'n_total': n_total, 'n_delay': n_delay, 'n_s_delay': n_s_delay, 'n_ss_delay': n_ss_delay}
        elif type_ == 5:
            q = SaleTrade.objects.filter(status__in=[SaleTrade.WAIT_SELLER_SEND_GOODS])
            n_total = q.only('id').count()
            n_delay = q.filter(pay_time__lte=threshold).only('id').count()
            n_s_delay = q.filter(pay_time__lte=threshold2).only('id').count()
            n_ss_delay = q.filter(pay_time__lte=threshold3).only('id').count()
            data = {'n_total': n_total, 'n_delay': n_delay, 'n_s_delay': n_s_delay, 'n_ss_delay': n_ss_delay}
        elif type_ == 6:
            cache_key = 'tongji_product_sellout'
            cache_value = cache.get(cache_key)
            if not cache_value:
                modelproducts = ModelProduct.objects.filter(shelf_status=ModelProduct.ON_SHELF)
                model_ids = []
                for item in modelproducts:
                    if item.is_sale_out:
                        model_ids.append(item.id)

                data = {
                    'n_total': '', 'n_delay': '',
                    'n_s_delay': ','.join(map(str, model_ids[:5])), 'n_ss_delay': len(model_ids)
                }
                cache.set(cache_key, data, 3600)
            else:
                data = cache_value
        elif type_ == 7:
            q = PackageSkuItem.objects.filter(assign_status=0, purchase_order_unikey='', type=0)
            q.filter(pay_time__lt=now - datetime.timedelta(days=1))
            n_total = q.count()
            n_delay = q.filter(pay_time__lt=now - datetime.timedelta(days=1)).only('id').count()
            n_s_delay = q.filter(pay_time__lt=now - datetime.timedelta(days=2)).only('id').count()
            n_ss_delay = q.filter(pay_time__lt=now - datetime.timedelta(days=3)).only('id').count()
            data = {'n_total': n_total, 'n_delay': n_delay, 'n_s_delay': n_s_delay, 'n_ss_delay': n_ss_delay}
        elif type_ == 8:
            q = SaleOrder.objects.filter(
                sale_trade__is_boutique=True,
                sale_trade__order_type=SaleTrade.SALE_ORDER,
                status=SaleOrder.WAIT_SELLER_SEND_GOODS
            )
            n_total = q.count()
            n_delay = q.filter(pay_time__lt=now - datetime.timedelta(days=1)).only('id').count()
            n_s_delay = q.filter(pay_time__lt=now - datetime.timedelta(days=2)).only('id').count()
            n_ss_delay = q.filter(pay_time__lt=now - datetime.timedelta(days=3)).only('id').count()
            data = {'n_total': n_total, 'n_delay': n_delay, 'n_s_delay': n_s_delay, 'n_ss_delay': n_ss_delay}
        if data:
            return Response(data)
        return Response({'error': '参数错误'})
