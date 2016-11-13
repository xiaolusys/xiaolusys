from __future__ import division

# coding:utf-8
__author__ = 'yann'

from django.shortcuts import render, HttpResponse
from django.template import RequestContext
from django.views.generic import View
from flashsale.dinghuo.models import RecordGroupPoint
import datetime
from django.db.models import Sum
from django.core import serializers
from flashsale.dinghuo.models_user import MyUser


def get_ding_huo_point(group_id, week_begin, week_to):
    ding_huo_point = RecordGroupPoint.objects.filter(group_id=group_id, point_type=1,
                                                     record_time__range=(week_begin, week_to)).aggregate(
        total_point=Sum('get_point')).get('total_point') or 0
    all_point = RecordGroupPoint.objects.filter(group_id=group_id, point_type=1,
                                                record_time__range=(week_begin, week_to))
    return ding_huo_point, all_point.count()


def get_sale_point(group_id, week_begin, week_to):
    ding_huo_point = RecordGroupPoint.objects.filter(group_id=group_id, point_type=2,
                                                     record_time__range=(week_begin, week_to)).aggregate(
        total_sale_point=Sum('get_point')).get('total_sale_point') or 0
    return ding_huo_point


class RecordPointView(View):
    @staticmethod
    def get(request):
        user = request.user
        my_user = MyUser.objects.filter(user=user)
        if my_user.count() > 0:
            group_id = my_user[0].group_id
        else:
            group_id = 1
        content = request.GET
        today = datetime.date.today()
        shelve_fromstr = content.get("df", None)
        target_date = today
        if shelve_fromstr:
            year, month, day = shelve_fromstr.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
        week_begin = target_date - datetime.timedelta(days=target_date.weekday())
        week_to = week_begin + datetime.timedelta(days=6)
        a_ding_huo_point, a_all_point = get_ding_huo_point(1, week_begin, week_to)
        b_ding_huo_point, b_all_point = get_ding_huo_point(2, week_begin, week_to)
        c_ding_huo_point, c_all_point = get_ding_huo_point(3, week_begin, week_to)
        a_percentage = (a_ding_huo_point * 100 // a_all_point) if a_all_point else 0
        b_percentage = (b_ding_huo_point * 100 // b_all_point) if b_all_point else 0
        c_percentage = (c_ding_huo_point * 100 // c_all_point) if c_all_point else 0
        a_sale_point = get_sale_point(1, week_begin, week_to)
        b_sale_point = get_sale_point(2, week_begin, week_to)
        c_sale_point = get_sale_point(3, week_begin, week_to)
        all_point = RecordGroupPoint.objects.exclude(get_point=0).filter(
            record_time__range=(week_begin, week_to)).filter(group_id=group_id)
        return render(
            request,
            "dinghuo/data_of_point.html",
              {"target_date": target_date, "a_ding_huo_point": a_ding_huo_point,
               "b_ding_huo_point": b_ding_huo_point, "c_ding_huo_point": c_ding_huo_point,
               "a_sale_point": a_sale_point, "a_all_point": a_all_point,
               "a_percentage": a_percentage,
               "b_sale_point": b_sale_point, "b_all_point": b_all_point,
               "b_percentage": b_percentage,
               "c_sale_point": c_sale_point, "c_all_point": c_all_point,
               "c_percentage": c_percentage,
               "all_point": all_point,
               "week_begin": week_begin, "week_to": week_to}
        )

    @staticmethod
    def post(request):
        content = request.POST
        group_id = content.get("group_id", "0")
        point_type = content.get("point_type", "0")
        week_begin = content["week_begin"]
        week_to = content["week_to"]
        if point_type == "0":
            all_point = RecordGroupPoint.objects.exclude(get_point="0").filter(
                record_time__range=(week_begin, week_to)).filter(group_id=group_id)
        else:
            all_point = RecordGroupPoint.objects.exclude(get_point=0).filter(
                record_time__range=(week_begin, week_to)).filter(group_id=group_id, point_type=point_type)
        data = serializers.serialize("json", all_point)
        return HttpResponse(data)
