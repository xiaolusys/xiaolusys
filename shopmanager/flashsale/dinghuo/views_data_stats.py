# coding:utf-8
__author__ = 'yann'
from django.views.generic import View
from django.shortcuts import HttpResponse, render_to_response
from flashsale.dinghuo.tasks import task_stats_product
from django.template import RequestContext
from flashsale.dinghuo.models_stats import DailySupplyChainStatsOrder
import time
from shopback.items.models import Product


class DailyStatsView(View):
    @staticmethod
    def get(request, prev_day):
        try:
            task_stats_product.delay()
        except:
            return HttpResponse("False")
        return HttpResponse(prev_day)


def format_time_from_dict(data_dict):
    for data in data_dict:
        trade_general_time = data["trade_general_time"]
        order_deal_time = data["order_deal_time"]
        goods_arrival_time = data["goods_arrival_time"]
        goods_out_time = data["goods_out_time"]
        if trade_general_time > 0:
            data["trade_general_time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(trade_general_time))
            data["order_deal_time"] = format_time(order_deal_time, trade_general_time)
            data["goods_arrival_time"] = format_time(goods_arrival_time, trade_general_time)
            data["goods_out_time"] = format_time(goods_out_time, trade_general_time)
        else:
            data["order_deal_time"] = ""

            data["goods_arrival_time"] = ""

            data["goods_out_time"] = ""
    return data_dict


def format_time(date1, date2):
    time_of_long = date1 - date2 - 28800
    if time_of_long > 0:
        a = time.localtime(time_of_long)
        result_time = "{0}天 {1} 小时".format(a.tm_mday - 1, a.tm_mday)
        return result_time
    else:
        return ""


class StatsProductView(View):
    @staticmethod
    def get(request):
        all_data = DailySupplyChainStatsOrder.objects.values("product_id", "sale_time", "trade_general_time",
                                                             "order_deal_time", "goods_arrival_time",
                                                             "goods_out_time").all()
        all_data_dict = format_time_from_dict(all_data)
        return render_to_response("dinghuo/data_of_product.html", {"all_data": all_data_dict},
                                  context_instance=RequestContext(request))