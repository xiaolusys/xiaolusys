# coding:utf-8
__author__ = 'yann'
from django.views.generic import View
from django.shortcuts import HttpResponse, render_to_response
from flashsale.dinghuo.tasks import task_stats_daily_order_by_group, task_stats_daily_product
from django.template import RequestContext
from flashsale.dinghuo.models_stats import SupplyChainStatsOrder
import time
from shopback.items.models import Product


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


def format_time_from_dict(data_dict):
    print data_dict
    for pro_id, data in data_dict.items():
        trade_general_time = data["trade_general_time"]
        order_deal_time = data["order_deal_time"]
        goods_arrival_time = data["goods_arrival_time"]
        goods_out_time = data["goods_out_time"]
        if trade_general_time > 0:
            data["trade_general_time"] = time.strftime('%Y-%m-%d %H点', time.localtime(trade_general_time))
        if order_deal_time > 0:
            data["order_deal_time"] = time.strftime('%Y-%m-%d %H点', time.localtime(order_deal_time))
        if goods_arrival_time > 0:
            data["goods_arrival_time"] = time.strftime('%Y-%m-%d %H点', time.localtime(goods_arrival_time))
        if goods_out_time > 0:
            data["goods_out_time"] = time.strftime('%Y-%m-%d %H点', time.localtime(goods_out_time))

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
        all_data = SupplyChainStatsOrder.objects.all()
        all_data_dict = {}
        for data in all_data:
            pro_bean = Product.objects.filter(outer_id=data.product_id)
            if pro_bean.count() > 0 and pro_bean[0].sale_time:
                if data.product_id in all_data_dict:
                    if data.ding_huo_num > 0:
                        ding_huo_num = all_data_dict[data.product_id]['ding_huo_num']
                        ding_huo_time = all_data_dict[data.product_id]['order_deal_time']
                        ding_huo_time = (data.ding_huo_num * data.order_deal_time + ding_huo_num * ding_huo_time) / (
                            ding_huo_num + data.ding_huo_num)
                        all_data_dict[data.product_id]['order_deal_time'] = ding_huo_time
                        all_data_dict[data.product_id]['ding_huo_num'] += data.ding_huo_num
                    if data.sale_num > 0:
                        sale_num = all_data_dict[data.product_id]['sale_num']
                        trade_general_time = all_data_dict[data.product_id]['trade_general_time']
                        trade_general_time = (
                                                 data.sale_num * data.trade_general_time + trade_general_time * sale_num) / (
                                                 sale_num + data.sale_num)
                        all_data_dict[data.product_id]['trade_general_time'] = trade_general_time
                        all_data_dict[data.product_id]['sale_num'] += data.sale_num
                    if data.arrival_num > 0:
                        arrival_num = all_data_dict[data.product_id]['arrival_num']
                        goods_arrival_time = all_data_dict[data.product_id]['goods_arrival_time']
                        goods_arrival_time = \
                            (data.arrival_num * data.goods_arrival_time + goods_arrival_time * arrival_num) / (
                                arrival_num + data.arrival_num)
                        all_data_dict[data.product_id]['goods_arrival_time'] = goods_arrival_time
                        all_data_dict[data.product_id]['arrival_num'] += data.arrival_num
                    if data.goods_out_num > 0:
                        goods_out_num = all_data_dict[data.product_id]['goods_out_num']
                        goods_out_time = all_data_dict[data.product_id]['goods_out_time']
                        goods_out_time = (data.goods_out_num * data.goods_out_time + goods_out_time * goods_out_num) / (
                            goods_out_num + data.goods_out_num)
                        all_data_dict[data.product_id]['goods_out_time'] = goods_out_time
                        all_data_dict[data.product_id]['goods_out_num'] += data.goods_out_num
                else:
                    all_data_dict[data.product_id] = {"shelve_time": pro_bean[0].sale_time,
                                                      "sale_num": data.sale_num,
                                                      "trade_general_time": data.trade_general_time,
                                                      "ding_huo_num": data.ding_huo_num,
                                                      "order_deal_time": data.order_deal_time,
                                                      "arrival_num": data.arrival_num,
                                                      "goods_arrival_time": data.goods_arrival_time,
                                                      "goods_out_num": data.goods_out_num,
                                                      "goods_out_time": data.goods_out_time}
        print all_data_dict
        format_time_from_dict(all_data_dict)
        return render_to_response("dinghuo/data_of_product.html", {"all_data": all_data_dict},
                                  context_instance=RequestContext(request))