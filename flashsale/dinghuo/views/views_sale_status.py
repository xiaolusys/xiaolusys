# coding:utf-8
__author__ = 'yann'
from django.views.generic import View
from django.shortcuts import HttpResponse, render, HttpResponseRedirect
from flashsale.dinghuo.tasks import task_stats_product, task_stats_daily_product, task_stats_daily_order_by_group, \
    task_send_daily_message, task_write_supply_name
from django.template import RequestContext
import time
from shopback.items.models import Product
from django.db import connection
import datetime
from calendar import monthrange
from flashsale.daystats.tasks import task_calc_hot_sale, task_calc_stock_top, task_calc_sale_bad


class EntranceView(View):
    @staticmethod
    def get(request):
        content = request.GET
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
    """热销产品统计"""

    @staticmethod
    def get(request):
        content = request.GET
        start_time_str = content.get("df", datetime.date.today().strftime('%Y-%m-%d'))
        end_time_str = content.get("dt", datetime.date.today().strftime('%Y-%m-%d'))
        category = content.get("category", None)
        send_tasks = task_calc_hot_sale.delay(start_time_str, end_time_str, category)
        return render(
            request,
            "dinghuo/data2hotsale.html",
              {"task_id": send_tasks, "start_date": start_time_str,
               "end_date": end_time_str, "category": category},
        )


class SaleBadView(View):
    """滞销产品统计"""

    @staticmethod
    def get(request):
        content = request.GET
        start_time_str = content.get("df", datetime.date.today().strftime('%Y-%m-%d'))
        end_time_str = content.get("dt", datetime.date.today().strftime('%Y-%m-%d'))
        category = content.get("category", None)
        send_tasks = task_calc_sale_bad.delay(start_time_str, end_time_str, category)
        return render(
            request,
            "dinghuo/data2salebad.html",
              {"task_id": send_tasks, "start_date": start_time_str,
               "end_date": end_time_str, "category": category},
        )


from django.db.models import Q


class TopStockView(View):
    """库存多的商品"""

    @staticmethod
    def get(request):
        content = request.GET
        start_time_str = content.get("df", None)
        end_time_str = content.get("dt", None)
        limit_num = content.get("limit_num", 200)
        try:
            limit_num = int(limit_num)
        except:
            limit_num = 200
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
        send_tasks = task_calc_stock_top.delay(start_time_str, end_time_str, int(limit_num))
        return render(
            request,
            "dinghuo/data2stock.html",
              {"task_id": send_tasks, "start_date": start_date,
               "end_date": end_date, "limit_num": limit_num},
        )


from rest_framework import generics
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from core.options import log_action, CHANGE
from shopback.items.models import Product
from flashsale.dinghuo.models import ProductSkuDetail
from django.db import transaction


class ChangeKunView(generics.ListCreateAPIView):
    """
        修改上架前库存
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "dinghuo/product/change_kucun.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        product_outer_id = request.GET.get("search_input", "")
        if not product_outer_id:
            return Response({"product_outer_id": product_outer_id})
        try:
            product = Product.objects.get(outer_id=product_outer_id, status=Product.NORMAL)
            all_skus = product.normal_skus
            normal_skus = []
            for one_sku in all_skus:
                before_shelf = ProductSkuDetail.objects.filter(product_sku=one_sku.id)
                exist_stock_num = 0
                if before_shelf.count() > 0:
                    exist_stock_num = before_shelf[0].exist_stock_num
                normal_skus.append(
                    {"sku_id": one_sku.id, "exist_stock_num": exist_stock_num, "sku_name": one_sku.properties_alias})
            return Response({"product_outer_id": product_outer_id, "product": product, "normal_skus": normal_skus})
        except:
            return Response({"product_outer_id": product_outer_id})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        post = request.POST
        sku_list_str = post.get("sku_list", "")
        sku_list_str = sku_list_str[0: len(sku_list_str) - 1]
        sku_list = sku_list_str.split(",")
        try:
            for one_sku in sku_list:
                detail, status = ProductSkuDetail.objects.get_or_create(product_sku=one_sku)
                detail.exist_stock_num = post.get(one_sku, 0)
                detail.save()
                log_action(request.user.id, detail, CHANGE, u'修改上架前库存')
            return Response({"result": "OK"})
        except:
            return Response({"result": "error"})


class SaleStatusView(generics.ListCreateAPIView):
    """
        销售情况预览（预留和待发）
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "dinghuo/product/sale_warning.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        target_date_str = content.get("target_date", None)
        warn_num = content.get("warn_num", 3)
        try:
            warn_num = int(warn_num)
        except:
            warn_num = 3
        today = datetime.date.today()
        if target_date_str:
            year, month, day = target_date_str.split('-')
            target_date = datetime.date(int(year), int(month), int(day))
        else:
            target_date = today
        all_product = Product.objects.filter(status=Product.NORMAL).filter(
            Q(sale_time=target_date) | Q(sale_time=target_date - - datetime.timedelta(days=1)))
        result_data = []
        for one_product in all_product:
            all_skus = one_product.normal_skus
            warning = False
            for one_sku in all_skus:
                if one_sku.remain_num - one_sku.lock_num < warn_num:
                    warning = True
            result_data.append({"outer_id": one_product.outer_id, "warning": warning,
                                "name": one_product.name, "pic_path": one_product.PIC_PATH})
        return Response({"warn_num": warn_num, "target_date": target_date, "result_data": result_data})
