# coding:utf-8
__author__ = 'yann'
from django.views.generic import View
from django.shortcuts import HttpResponse
from flashsale.dinghuo.tasks import task_stats_daily_order_by_group,task_stats_daily_product



class DailyStatsView(View):
    @staticmethod
    def get(request, prev_day):
        try:
            prev_day = int(prev_day)
            task_stats_daily_order_by_group.delay(prev_day)
            task_stats_daily_product.delay(prev_day)
        except:
            return HttpResponse("False")
        return HttpResponse(prev_day)