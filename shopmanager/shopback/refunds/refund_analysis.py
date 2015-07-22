# coding=utf-8
from .models import Refund, RefundProduct
from django.http import HttpResponse
from django.db.models import Sum, Q, Count
from django.views.decorators.csrf import csrf_exempt
import json
import datetime
from django.shortcuts import redirect, render_to_response
from django.views.generic import View
from django.template import RequestContext
import operator
from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg
"""
    # (0, u'其他'),
    # (1, u'错拍'),
    # (2, u'缺货'),
    # (3, u'开线/脱色/脱毛/有色差/有虫洞'),
    # (4, u'发错货/漏发'),
    # (5, u'没有发货'),
    # (6, u'未收到货'),
    # (7, u'与描述不符'),
    # (8, u'退运费'),
    # (9, u'发票问题'),
    # (10, u'七天无理由退换货')
    # 退货商品数量
ALTER TABLE shop_refunds_product ADD reason INT(11) DEFAULT 0;

1，能根据产品信息（编码，名称）查看该产品的退款明细，退款原因分类统计；
2，可以根据退款原因，查看有多少退款单；
3，退款，退货的退款原因，需客服手动选择；

"""


@csrf_exempt
def refund_Analysis(request):
    content = request.REQUEST
    sear_pro = content.get('sear_pro') or ''
    date_from = content.get('date_from')
    date_to = content.get('date_to')
    reason = content.get('reason') or ''

    today = datetime.date.today()
    sev_day = today - datetime.timedelta(days=7)  # 前七天
    date_time_from = datetime.datetime(sev_day.year, sev_day.month, sev_day.day, 0, 0, 0)
    date_time_to = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
    if date_from != '' and date_from is not None:
        year, month, day = date_from.split('-')
        date_time_from = datetime.datetime(int(year), int(month), int(day), 0, 0, 0)
    if date_to != '' and date_to is not None:
        year, month, day = date_to.split('-')
        date_time_to = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)

    refunds = Refund.objects.filter(created__gte=date_time_from, created__lte=date_time_to)
    refunds_success = refunds.filter(status=Refund.REFUND_SUCCESS)
    ref_co = refunds.count()  # 退款单数
    ref_am = refunds.aggregate(total_amount=Sum('refund_fee')).get('total_amount') or 0

    ref_su_co = refunds_success.count()  # 退款成功的单数
    ref_su_am = refunds_success.aggregate(total_su_am=Sum('refund_fee')).get('total_su_am') or 0

    refund_pros = RefundProduct.objects.filter(created__gte=date_time_from, created__lte=date_time_to)
    # 发货总数量
    merge_counts = MergeTrade.objects.all().exclude(status=pcfg.INVALID_STATUS).count()  # 排除作废订单
    # 计算退货率 退货单数量／发货总数量
    refund_rate_func = lambda ref_co, merge_counts: 0 if merge_counts == 0 else round(float(ref_co) / merge_counts, 3)
    refund_rate = refund_rate_func(ref_co, merge_counts)
    top_re = refund_pros.values('outer_id', 'title').annotate(t_num=Sum('num'))
    if len(top_re) > 50:
        top_re = sorted(top_re, key=operator.itemgetter('t_num'))   # 排序
        top_re = top_re[len(top_re) - 50:]

    # 有时间的情况 输出总的 对应时间的退货产品统计内容
    reason_count_total = refund_pros.values('reason').annotate(t_count=Count('num'))
    if reason != '':
        reason = int(reason)
        refund_pros = refund_pros.filter(reason=reason)  # refund_pros 过滤退货原因
    elif sear_pro != '':
        refund_pros = refund_pros.filter(Q(outer_id=sear_pro) | Q(title__contains=sear_pro))
    reason_count = refund_pros.values('reason').annotate(t_count=Count('num'))  # 条件过滤后的输出原因及对应条数的列表

    pros_co = refund_pros.count()

    # for top in top_re:
    # title = refund_pros.filter(outer_id=top['outer_id'])[0].title
    # top['title'] = title   # 如果同一个编码和名称有多个的情况

    return render_to_response("refunds/refund_analysis.html",
                              {"refund_pros": refund_pros, "ref_co": ref_co, "ref_am": ref_am,
                               "ref_su_co": ref_su_co, 'ref_su_am': ref_su_am,

                               "merge_counts": merge_counts, "refund_rate": refund_rate,

                               "reason_count_total": reason_count_total,
                               "reason_count": reason_count,
                               "sev_day": date_time_from.strftime("%Y-%m-%d"),
                               "today": date_time_to.strftime("%Y-%m-%d"), "sear_pro": sear_pro, "top_re": top_re,

                               'pros_co': pros_co, 'reason': reason},
                              context_instance=RequestContext(request))


@csrf_exempt
def refund_Reason(request):
    content = request.REQUEST
    try:
        reason = content.get('reason')
        pro_id = content.get('pro_id')
        pro = RefundProduct.objects.get(id=pro_id)
        pro.reason = reason
        pro.save()
        return HttpResponse('ok')
    except:
        return HttpResponse('change error')
