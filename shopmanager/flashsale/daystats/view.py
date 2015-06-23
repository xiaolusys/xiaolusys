# coding=utf-8
# __author__ = 'linjie'

from .models import DailyStat, PopularizeCost
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.db.models import Sum
from flashsale.xiaolumm.models import CarryLog
import datetime


# 推广成本分类统计，包含（订单返利，代理补贴，点击补贴，…）
# 可以集成到 [flashsale.daystat] app里面

def get_month_from_date(date_time):
    day_from = datetime.date(date_time.year, date_time.month, 1)  # 这个月的开始时间
    if date_time.month == 12:
        day_to = datetime.date(date_time.year, date_time.month, 31)
    else:
        day_to = datetime.date(date_time.year, date_time.month + 1, 1) - datetime.timedelta(1)  # 这个月的第一天减去1天
    date_from = datetime.datetime(day_from.year, day_from.month, day_from.day, 0, 0, 0)  # 上一周的开始时间
    date_to = datetime.datetime(day_to.year, day_to.month, day_to.day, 23, 59, 59)  # 上一周的结束时间
    return date_from, date_to


def popularize_Cost(request):
    content = request.REQUEST
    daystr = content.get("month", None)
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_month_from_date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_month_from_date(target_date)
    prev_month = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_month = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)

    date_from = datetime.date(date_from.year, date_from.month, date_from.day)
    date_to = datetime.date(date_to.year, date_to.month, date_to.day)
    popularizes = PopularizeCost.objects.filter(date__gte=date_from, date__lte=date_to)

    date_dic = {"prev_month": prev_month, "next_month": next_month}
    return render_to_response("popularize/popularize_cost.html", {"date_dic": date_dic, 'popularizes': popularizes},
                              context_instance=RequestContext(request))