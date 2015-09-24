# coding:utf-8
__author__ = 'yann'
from django.views.generic import View
from django.shortcuts import HttpResponse, render_to_response, HttpResponseRedirect
from flashsale.dinghuo.tasks import task_stats_product, task_stats_daily_product, task_stats_daily_order_by_group, \
    task_send_daily_message, task_write_supply_name
from django.template import RequestContext
from flashsale.dinghuo.models_stats import DailySupplyChainStatsOrder
import time
from shopback.items.models import Product
from django.db import connection
import datetime
from calendar import monthrange
from flashsale.daystats.tasks import task_calc_hot_sale, task_calc_stock_top, task_calc_sale_bad


class EntranceView(View):
    @staticmethod
    def get(request):
        content = request.REQUEST
        today = datetime.date.today()
        start_time_str = content.get("df", None)
        end_time_str = content.get("dt", None)
        category = content.get("category", None)

        if start_time_str:
            year, month, day = start_time_str.split('-')
            start_date = datetime.date(int(year), int(month), int(day))
            if start_date > today:
                start_date = today
        else:
            start_date = today - datetime.timedelta(days=monthrange(today.year, today.month)[1])
        if end_time_str:
            year, month, day = end_time_str.split('-')
            end_date = datetime.date(int(year), int(month), int(day))
        else:
            end_date = today
        # return render_to_response("dinghuo/sale_status_entrance.html",
        #                           {"start_date": start_date, "end_date": end_date, "category": category},
        #                           context_instance=RequestContext(request))
        return HttpResponseRedirect("/sale/dinghuo/sale_hot")


class SaleHotView(View):
    @staticmethod
    def get(request):
        content = request.REQUEST
        start_time_str = content.get("df", datetime.date.today().strftime('%Y-%m-%d'))
        end_time_str = content.get("dt",  datetime.date.today().strftime('%Y-%m-%d'))
        category = content.get("category", None)
        send_tasks = task_calc_hot_sale.delay(start_time_str, end_time_str, category)
        return render_to_response("dinghuo/data2hotsale.html",
                                  {"task_id": send_tasks, "start_date": start_time_str,
                                   "end_date": end_time_str, "category": category},
                                  context_instance=RequestContext(request))

class SaleBadView(View):
    @staticmethod
    def get(request):
        content = request.REQUEST
        start_time_str = content.get("df", datetime.date.today().strftime('%Y-%m-%d'))
        end_time_str = content.get("dt",  datetime.date.today().strftime('%Y-%m-%d'))
        category = content.get("category", None)
        send_tasks = task_calc_sale_bad.delay(start_time_str, end_time_str, category)
        return render_to_response("dinghuo/data2salebad.html",
                                  {"task_id": send_tasks, "start_date": start_time_str,
                                   "end_date": end_time_str, "category": category},
                                  context_instance=RequestContext(request))

from django.db.models import Q
from shopback.categorys.models import ProductCategory

class TopStockView(View):
    @staticmethod
    def get(request):
        content = request.REQUEST
        start_time_str = content.get("df", None)
        end_time_str = content.get("dt", None)
        today = datetime.date.today()
        if start_time_str:
            year, month, day = start_time_str.split('-')
            start_date = datetime.date(int(year), int(month), int(day))

        else:
            start_date = today - datetime.timedelta(days=monthrange(today.year, today.month)[1])
        if end_time_str:
            year, month, day = end_time_str.split('-')
            end_date = datetime.date(int(year), int(month), int(day))
        else:
            end_date = today
        """找出选择的开始月份和结束月份"""

        outer_idset = set([])
        sale_top = {}
        product_qs = Product.objects.filter(status=Product.NORMAL, collect_num__gt=0).extra(
            where=["CHAR_LENGTH(outer_id)>=9"]) \
            .filter(Q(outer_id__startswith="9") | Q(outer_id__startswith="1") | Q(outer_id__startswith="8")).filter(
            sale_time__range=(start_date, end_date))

        for product in product_qs:
            outer_id = product.outer_id
            router_id = outer_id[0:-1]
            if outer_id in outer_idset:
                continue
            outer_idset.add(outer_id)
            if router_id not in sale_top:
                if product.category:
                    if product.category.is_parent == 1:
                        category_name = product.category.name
                    else:
                        cate = ProductCategory.objects.filter(cid=product.category.parent_cid)
                        if cate.count() > 0:
                            category_name = cate[0].name
                        else:
                            category_name = ""
                else:
                    category_name = ""
                sale_top[router_id] = {'name': product.name, 'collect_num': product.collect_num,
                                       'sale_time': str(product.sale_time) if product.sale_time else "",
                                       "category": category_name}
            else:
                sale_top[router_id]['collect_num'] += product.collect_num

        sale_list = sorted(sale_top.items(), key=lambda d: d[1]['collect_num'], reverse=True)
        print sale_list, "eeee"
        # send_tasks = task_calc_stock_top.delay(start_time_str, end_time_str)
        return render_to_response("dinghuo/data2stock.html",
                                  {"sale_list": sale_list[0:200], "start_date": start_date, "end_date": end_date},
                                  context_instance=RequestContext(request))



