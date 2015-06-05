# coding:utf-8
__author__ = 'yann'
from django.views.generic import View
from django.shortcuts import HttpResponse
from flashsale.dinghuo.tasks import task_stats_daily_order_by_group
import function_of_task


class DailyStatsView(View):
    @staticmethod
    def get(request, prev_day):
        try:
            prev_day = int(prev_day)
            task_stats_daily_order_by_group.delay(prev_day)
            function_of_task.get_daily_order_stats(prev_day)
            function_of_task.get_daily_ding_huo_stats(prev_day)
            function_of_task.get_daily_goods_arrival_stats(prev_day)
            function_of_task.get_daily_out_order_stats(prev_day)
        except:
            return HttpResponse("False")
        return HttpResponse(prev_day)