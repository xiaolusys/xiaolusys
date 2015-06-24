# coding:utf-8
__author__ = 'yann'
from django.views.generic import View
from django.shortcuts import HttpResponse, render_to_response
from flashsale.dinghuo.tasks import task_stats_product, task_stats_daily_product, task_stats_daily_order_by_group, \
    task_send_daily_message, task_write_supply_name
from django.template import RequestContext
from flashsale.dinghuo.models_stats import DailySupplyChainStatsOrder
import time
from shopback.items.models import Product
from django.db import connection


class DailyStatsView(View):
    @staticmethod
    def get(request, prev_day):
        try:
            prev_day = int(prev_day)
            if prev_day == 1000:
                task_stats_product.delay()
            elif prev_day == 10000:
                task_send_daily_message.delay()
            elif prev_day == 10001:
                task_write_supply_name.delay()
            elif prev_day > 1000:
                task_stats_daily_order_by_group.delay(prev_day - 1000)

            else:
                task_stats_daily_product.delay(prev_day)
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


def format_time_from_tuple(data_tuple):
    data_list = []
    for data in data_tuple:
        data_dict = {"product_id": data[1], "sale_time": data[2], "trade_general_time": data[3],
                     "order_deal_time": data[4], "goods_arrival_time": data[5], "goods_out_time": data[6],
                     "ding_huo_num": data[7], "sale_num": data[8], "cost_of_product": data[9],
                     "sale_cost_of_product": data[10], "return_num": data[11], "inferior_num": data[12],
                     "supplier_shop": data[16]}
        trade_general_time = data[3]
        order_deal_time = data[4]
        goods_arrival_time = data[5]
        goods_out_time = data[6]
        if trade_general_time > 0:
            data_dict["trade_general_time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(trade_general_time))
            data_dict["order_deal_time"] = format_time(order_deal_time, trade_general_time)
            data_dict["goods_arrival_time"] = format_time(goods_arrival_time, trade_general_time)
            data_dict["goods_out_time"] = format_time(goods_out_time, trade_general_time)
        else:
            data_dict["order_deal_time"] = ""

            data_dict["goods_arrival_time"] = ""

            data_dict["goods_out_time"] = ""
        data_list.append(data_dict)
    return data_list


def format_time(date1, date2):
    time_of_long = date1 - date2
    days = 0
    tm_hours = 0
    if time_of_long > 0:
        days = time_of_long / 86400
        tm_hours = time_of_long % 86400 / 3600
    if days > 0 or tm_hours > 0:
        return str(days) + "天" + str(tm_hours) + "小时"
    else:
        return ""


class StatsProductView(View):
    @staticmethod
    def get(request):
        sql = 'select * from (select * from supply_chain_stats_daily) as supplydata left join (select detail.outer_id,list.supplier_shop from (select outer_id,orderlist_id from suplychain_flashsale_orderdetail where orderlist_id not in(select id from suplychain_flashsale_orderlist where status="作废" or status="7")) as detail left join (select id,supplier_shop from suplychain_flashsale_orderlist) as list on detail.orderlist_id=list.id where list.supplier_shop!="" group by outer_id) as supply on supplydata.product_id=supply.outer_id'
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        all_data_list = format_time_from_tuple(raw)
        return render_to_response("dinghuo/data_of_product.html", {"all_data": all_data_list},
                                  context_instance=RequestContext(request))


class StatsSupplierView(View):
    @staticmethod
    def get(request):
        sql = 'select supply.supplier_shop,sum(supplydata.ding_huo_num) as ding_huo_num,' \
              'sum(supplydata.sale_num) as sale_num,sum(supplydata.sale_cost_of_product) as sale_amount,' \
              'sum(inferior_num) as inferior_num,sum(return_num) as return_num ' \
              'from (select * from supply_chain_stats_daily) as supplydata left join ' \
              '(select detail.outer_id,list.supplier_shop from (select outer_id,orderlist_id from suplychain_flashsale_orderdetail where orderlist_id not in(select id from suplychain_flashsale_orderlist where status="作废" or status="7")) as detail left join ' \
              '(select id,supplier_shop from suplychain_flashsale_orderlist) as list ' \
              'on detail.orderlist_id=list.id where list.supplier_shop!="" group by outer_id) as supply ' \
              'on supplydata.product_id=supply.outer_id group by supply.supplier_shop'
        cursor = connection.cursor()
        cursor.execute(sql)
        raw = cursor.fetchall()
        return render_to_response("dinghuo/data_of_supplier.html", {"all_data": raw},
                                  context_instance=RequestContext(request))