# coding:utf-8
__author__ = 'yann'
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import View
from flashsale.dinghuo.models_stats import RecordGroupPoint
import datetime
from django.db.models import Sum


def get_ding_huo_point(group_id, week_begin, week_to):
    ding_huo_point = RecordGroupPoint.objects.filter(group_id=group_id, point_type=1,
                                                     record_time__range=(week_begin, week_to)).aggregate(
        total_point=Sum('get_point')).get('total_point') or 0
    return ding_huo_point


def get_sale_point(group_id, week_begin, week_to):
    ding_huo_point = RecordGroupPoint.objects.filter(group_id=group_id, point_type=2,
                                                     record_time__range=(week_begin, week_to)).aggregate(
        total_sale_point=Sum('get_point')).get('total_sale_point') or 0
    return ding_huo_point


class RecordPointView(View):
    @staticmethod
    def get(request):
        content = request.REQUEST
        today = datetime.date.today()
        shelve_fromstr = content.get("df", None)
        target_date = today
        if shelve_fromstr:
            year, month, day = shelve_fromstr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
        week_begin = target_date - datetime.timedelta(days=target_date.weekday())
        week_to = week_begin + datetime.timedelta(days=6)
        a_ding_huo_point = get_ding_huo_point(1, week_begin, week_to)
        b_ding_huo_point = get_ding_huo_point(2, week_begin, week_to)
        c_ding_huo_point = get_ding_huo_point(3, week_begin, week_to)
        a_sale_point = get_sale_point(1, week_begin, week_to)
        b_sale_point = get_sale_point(2, week_begin, week_to)
        c_sale_point = get_sale_point(3, week_begin, week_to)
        return render_to_response("dinghuo/data_of_point.html",
                                  {"target_date": target_date, "a_ding_huo_point": a_ding_huo_point,
                                   "b_ding_huo_point": b_ding_huo_point, "c_ding_huo_point": c_ding_huo_point,
                                   "a_sale_point": a_sale_point, "b_sale_point": b_sale_point,
                                   "c_sale_point": c_sale_point},
                                  context_instance=RequestContext(request))