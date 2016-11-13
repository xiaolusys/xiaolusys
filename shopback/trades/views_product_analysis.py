# coding=utf-8
__author__ = 'linjie'
from django.shortcuts import render
from django.template import RequestContext
from models import MergeTrade, MergeOrder
import datetime
from django.db.models import Sum
from shopback import paramconfig as pcfg
from flashsale.dinghuo.models import OrderDetail
from flashsale.clickrebeta.models import StatisticsShopping
from django.db import connection
from flashsale.xiaolumm.models import XiaoluMama
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from shopback.items.models import Product, ProductSku
from django.http import HttpResponse


def get_Month_By_Date(date_time):
    day_from = datetime.date(date_time.year, date_time.month, 1)  # 这个月的开始时间
    if date_time.month == 12:
        day_to = datetime.date(date_time.year, date_time.month, 31)
    else:
        day_to = datetime.date(date_time.year, date_time.month + 1, 1) - datetime.timedelta(1)  # 下个月的第一天减去1天
    date_from = datetime.datetime(day_from.year, day_from.month, day_from.day, 0, 0, 0)
    date_to = datetime.datetime(day_to.year, day_to.month, day_to.day, 23, 59, 59)
    return date_from, date_to


@csrf_exempt
def xlmm_Product_Analysis(request):
    content = request.GET
    daystr = content.get("month", None)
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_Month_By_Date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_Month_By_Date(target_date)
    prev_month = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_month = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)

    date_from = datetime.date(date_from.year, date_from.month, date_from.day)
    date_to = datetime.date(date_to.year, date_to.month, date_to.day)
    date_dic = {"prev_month": prev_month, "next_month": next_month}

    sql = "SELECT " \
          "shopping.linkid, " \
          "shopping.linkname, " \
          "shopping.refund_num, " \
          "detail.sum_ordernumcount, " \
          "detail.sum_orderamountcount " \
          "FROM " \
          "(SELECT  " \
          "linkid, sum(if(status=2,1,0)) AS refund_num, linkname " \
          "FROM " \
          "flashsale_tongji_shopping WHERE shoptime BETWEEN '{0}'  AND '{1}' " \
          "GROUP BY linkid) AS shopping " \
          "LEFT JOIN " \
          "(SELECT  " \
          "linkid, " \
          "SUM(ordernumcount) AS sum_ordernumcount, " \
          "ROUND ((SUM(orderamountcount)/100),2) AS sum_orderamountcount " \
          "FROM " \
          "flashsale_tongji_shopping_day WHERE tongjidate BETWEEN '{0}'  AND '{1}'" \
          "GROUP BY linkid) AS detail ON shopping.linkid = detail.linkid ".format(date_from, date_to)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    return render(
        request,
        'product_analysis/xlmm_pro_analysis.html',
        {'raw': raw, 'date_dic': date_dic},
    )


@csrf_exempt
def product_Analysis(request):
    content = request.GET
    daystr = content.get("month", None)
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_Month_By_Date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_Month_By_Date(target_date)
    prev_month = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_month = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)

    date_from = datetime.date(date_from.year, date_from.month, date_from.day)
    date_to = datetime.date(date_to.year, date_to.month, date_to.day)
    date_dic = {"prev_month": prev_month, "next_month": next_month}

    # 统计每月销售top50 以及次品数量
    sql = "SELECT " \
          "C.product_id, C.sum_num, C.name, detail.inferior_quantity " \
          "FROM" \
          "(SELECT " \
          "A.product_id, A.sum_num, B.name " \
          "FROM" \
          "(SELECT " \
          "product_id, SUM(sale_num) AS sum_num  " \
          "FROM " \
          "supply_chain_stats_order WHERE created BETWEEN '{0}' AND '{1}' " \
          "GROUP BY product_id " \
          "ORDER BY sum_num DESC " \
          "LIMIT 50) AS A " \
          "LEFT JOIN (SELECT " \
          "outer_id, name " \
          "FROM " \
          "shop_items_product) AS B ON A.product_id = B.outer_id) AS C " \
          "LEFT JOIN" \
          "(SELECT " \
          " outer_id, inferior_quantity " \
          "FROM " \
          "suplychain_flashsale_orderdetail WHERE created BETWEEN '{0}' AND '{1}' " \
          "GROUP BY outer_id) AS detail ON detail.outer_id = C.product_id".format(
        date_from, date_to)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    return render(
        request,
        'product_analysis/product_analysis.html',
        {'data': raw, 'date_dic': date_dic},
    )


# 统计特卖商品销售前100（按周），按编码去掉最后一位来聚合
# 每日商品销售信息统计表：shopback/items/models.py #ProductDaySale
# from  shopback.items.models import ProductDaySale


def get_week_from_date(date_time):
    days = date_time.isoweekday()
    day_from = date_time - datetime.timedelta(days=days - 1)
    day_to = day_from + datetime.timedelta(days=6)
    date_from = datetime.datetime(day_from.year, day_from.month, day_from.day, 0, 0, 0)  # 上一周的开始时间
    date_to = datetime.datetime(day_to.year, day_to.month, day_to.day, 23, 59, 59)  # 上一周的结束时间
    return date_from, date_to


def product_Top100_By_Week(request):
    content = request.GET
    daystr = content.get("week", None)
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_week_from_date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_week_from_date(target_date)
    prev_week = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_week = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)

    sql = "SELECT " \
          " sale.product_id, product.name, " \
          "SUM(sale.confirm_num) AS sale_num, " \
          "SUM(sale.confirm_payment) AS sale_payment, " \
          "LEFT(product.outer_id, 9) AS pid " \
          "FROM " \
          "((SELECT " \
          " product_id, confirm_num, confirm_payment " \
          "FROM " \
          "shop_items_daysale WHERE  day_date BETWEEN '{0}' AND '{1}') AS sale " \
          "LEFT JOIN (SELECT " \
          "id, outer_id, name " \
          "FROM " \
          "shop_items_product) AS product ON sale.product_id = product.id) " \
          "WHERE " \
          "LENGTH(product.outer_id) >= 9 " \
          "GROUP BY pid " \
          "ORDER BY sale_num DESC " \
          " LIMIT 100 ".format(date_from, date_to)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()

    date_dic = {"prev_week": prev_week, "next_week": next_week}
    return render(
        request,
        'product_analysis/product_analysis_top100.html',
        {'data': raw, 'date_dic': date_dic},
    )


# 统计特卖商品剩余库存最多的前100个
# 关联表:shopback/items/models.py #Product,ProductSku

# Product: collect_num, name

def product_Collect_Topp100(request):
    sql = "SELECT  " \
          "product.id, " \
          "product.name, " \
          "product.collect_num, " \
          "sku.properties_alias, " \
          "sku.quantity " \
          "FROM " \
          "(SELECT " \
          "id, name, collect_num " \
          "FROM " \
          "shop_items_product where length(outer_id)>=9  and ( left(outer_id,1)=9 or " \
          " left(outer_id,1)=8 or left(outer_id,1)=1)  and status!='delete' " \
          "ORDER BY collect_num DESC " \
          " LIMIT 100) AS product " \
          "LEFT JOIN " \
          "(SELECT " \
          " product_id, quantity, properties_alias " \
          "FROM " \
          " shop_items_productsku) AS sku ON product.id = sku.product_id"
    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()

    pro = {}
    for i in raw:
        product_id = i[0]
        if product_id not in pro:
            pro[i[0]] = [{"product_name": i[1], 'collect_num': i[2], 'properties_alias': i[3], 'quantity': i[4]}]
        else:
            pro[i[0]].append({"product_name": i[1], 'collect_num': i[2], 'properties_alias': i[3], 'quantity': i[4]})

    return render(
        request,
        'product_analysis/product_analysis_collect_top100.html',
        {'data': pro},
    )


# 打开订单送货时间查询页面
def open_trade_time(request):
    return render(request, 'trades/trade_time.html')


import json
# 订单送货时间查询结果
from rest_framework.response import Response


@csrf_exempt
def list_trade_time(request):
    quest = request.POST
    start = quest['startdate']
    end = quest['enddate']

    year, month, day = start.split('-')
    start_date = datetime.date(int(year), int(month), int(day))

    year, month, day = end.split('-')
    end_date = datetime.date(int(year), int(month), int(day))

    listTrade = MergeTrade.objects.filter(type__in=(pcfg.SALE_TYPE, pcfg.WX_TYPE)) \
        .filter(Q(weight_time__gte=start_date), Q(weight_time__lte=end_date),
                Q(status=pcfg.WAIT_BUYER_CONFIRM_GOODS) | Q(status=pcfg.TRADE_BUYER_SIGNED)
                | Q(status=pcfg.TRADE_FINISHED) | Q(status=pcfg.TRADE_CLOSED)
                ).exclude(sys_status=pcfg.INVALID_STATUS).exclude(sys_status=pcfg.ON_THE_FLY_STATUS)
    # 定义全局变量
    global c3, c5, c7, c9, c10
    c3 = 0
    c5 = 0
    c7 = 0
    c9 = 0
    c10 = 0

    for trade in listTrade:
        if trade.weight_time not in (None, " "):
            tian = int((trade.weight_time - trade.pay_time).days) + 1
            if tian <= 3:  # 三天之内发货的
                c3 += 1
            elif tian > 3 and tian <= 5:  # 三到五天之内发货的的
                c5 += 1
            elif tian > 5 and tian <= 7:  # 五到七天之内发货的的
                c7 += 1
            elif tian > 7 and tian <= 9:  # 七到九天之内发货的的
                c9 += 1
            else:  # 九天之后发货的
                c10 += 1
    csum = c3 + c5 + c7 + c9 + c10
    data = {"c3": c3, "c5": c5, "c7": c7, "c9": c9, "c10": c10, "csum": csum}
    return HttpResponse(json.dumps(data), content_type='application/json')
