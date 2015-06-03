# coding:utf-8
__author__ = 'yann'
from django.views.generic import View
from django.shortcuts import HttpResponse
import functions
import datetime


class DailyStatsView(View):
    @staticmethod
    def get(request):
        target_day = datetime.date.today()
        target_day = target_day - datetime.timedelta(days=9)
        start_dt = datetime.datetime(target_day.year, target_day.month, target_day.day)
        end_dt = datetime.datetime(target_day.year, target_day.month, target_day.day, 23, 59, 59)
        order_qs = functions.get_source_orders(start_dt, end_dt)
        product_qs = functions.get_product_by_date(target_day)
        order_qs = [{'outer_id': u'8050142204', 'num': 1L, 'outer_sku_id': u'1'},
                    {'outer_id': u'8050142204', 'num': 2L, 'outer_sku_id': u'2'},
                    {'outer_id': u'90301030211', 'num': 3L, 'outer_sku_id': u'2'},
                    {'outer_id': u'8050142204', 'num': 4L, 'outer_sku_id': u'1'}]
        print order_qs
        print "          "
        result_str = {}
        for order in order_qs:
            if order["outer_id"] in result_str:
                if order["outer_sku_id"] in result_str[order["outer_id"]]:
                    result_str[order["outer_id"]][order["outer_sku_id"]]["num"] += order["num"]
                else:
                    result_str[order["outer_id"]][order["outer_sku_id"]] = {"num": order["num"]}
            else:
                result_str[order["outer_id"]] = {order["outer_sku_id"]: {"num": order["num"]}}



        print result_str

        return HttpResponse("OK")