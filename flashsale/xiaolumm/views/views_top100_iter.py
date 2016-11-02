# coding=utf-8
# __author__ = 'linjie'
import datetime
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.clickcount.models import ClickCount, WeekCount
from flashsale.clickrebeta.models import StatisticsShoppingByDay
from django.db import connection, transaction
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import F, Sum
import calendar


def get_month_from_date(date_time):
    day_from = datetime.date(date_time.year, date_time.month, 1)  # 这个月的开始时间
    if date_time.month == 12:
        day_to = datetime.date(date_time.year, date_time.month, 31)
    else:
        day_to = datetime.date(date_time.year, date_time.month + 1, 1) - datetime.timedelta(1)  # 这个月的第一天减去1天
    date_from = datetime.datetime(day_from.year, day_from.month, day_from.day, 0, 0, 0)  # 上一周的开始时间
    date_to = datetime.datetime(day_to.year, day_to.month, day_to.day, 23, 59, 59)  # 上一周的结束时间
    return date_from, date_to


def get_next_month(date):
    a = calendar.monthrange(date.year, date.month)
    next_month_has_days = a[1]
    next_date_from = datetime.date(date.year, date.month, 1)
    next_date_to = datetime.date(date.year, date.month, next_month_has_days)

    next_next_date_from = next_date_to + datetime.timedelta(days=1)
    b = calendar.monthrange(next_next_date_from.year, next_next_date_from.month)
    next_next_month_has_days = b[1]
    next_next_date_to = datetime.date(next_next_date_from.year, next_next_date_from.month, next_next_month_has_days)
    return next_date_from, next_date_to, next_next_date_from, next_next_date_to


# 计算 每个月的TOP100 在随后的2个月 的 贡献情况  （分别是 点击100  订单100 ）
def Top100_Click(request):
    # 计算每个月的点击TOP100
    # 根据妈妈的ID   计算下个月 的点击  订单
    # 根据妈妈的ID   计算下下个月 的点击  订单
    content = request.REQUEST
    daystr = content.get("month", None)
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_month_from_date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_month_from_date(target_date)
    prev_month = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_month = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)
    date_dic = {"prev_month": prev_month, "next_month": next_month}

    sql = "SELECT " \
          " click.linkid,click.clicknum,click.weikefu,shop.ordernum " \
          "FROM " \
          "   (SELECT  " \
          "    linkid, SUM(valid_num) AS clicknum, weikefu " \
          "   FROM " \
          "     flashsale_clickcount " \
          " WHERE " \
          "      date BETWEEN '{0}' AND '{1}' " \
          "  GROUP BY linkid " \
          " ORDER BY clicknum DESC " \
          "    LIMIT 100) AS click " \
          "   LEFT JOIN " \
          "  (SELECT  " \
          "      linkid, SUM(ordernumcount) AS ordernum " \
          "   FROM " \
          "       flashsale_tongji_shopping_day " \
          "  WHERE " \
          "      tongjidate BETWEEN '{0}' AND '{1}' " \
          "   GROUP BY linkid) AS shop ON click.linkid = shop.linkid".format(date_from, date_to)  # 注意时间段  要加上

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    cursor.close()
    id = []
    for i in raw:
        id.append(i[0])

    sum_click_list_next = []
    # 计算下个月的点击数量
    next_date = date_to + datetime.timedelta(days=1)
    next_month_from, next_month_to, next_next_month_from, next_next_month_to = get_next_month(next_date)

    for j in id:  # 对每一个id 求 下个月的点击
        clicks = ClickCount.objects.filter(linkid=j, date__gt=next_month_from, date__lt=next_month_to)
        sum_click = clicks.aggregate(total_click=Sum('valid_num')).get('total_click') or 0
        sum_click_list_next.append(sum_click)
    sum_click_list_next_next = []
    for j in id:  # 对每一个id 求 下 下 个月的点击
        clicks = ClickCount.objects.filter(linkid=j, date__gt=next_next_month_from, date__lt=next_next_month_to)
        sum_click = clicks.aggregate(total_click=Sum('valid_num')).get('total_click') or 0
        sum_click_list_next_next.append(sum_click)

    data = []
    count_index = 0
    for x in raw:
        data_entry = {"id": x[0], "click": x[1], "nick": x[2], "order": x[3],
                      "next_month": sum_click_list_next[count_index],
                      "next_next_month": sum_click_list_next_next[count_index]}
        data.append(data_entry)
        count_index += 1
    return render_to_response('analysis/click_iter_top100.html',
                              {'data': data, 'date_dic': date_dic},
                              context_instance=RequestContext(request))


def Top100_Order(request):
    # 计算每个月的订单TOP100
    # 根据妈妈的ID   计算下个月 的点击  订单
    # 根据妈妈的ID   计算下下个月 的点击  订单
    content = request.REQUEST
    daystr = content.get("month", None)
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_month_from_date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_month_from_date(target_date)
    prev_month = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_month = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)
    date_dic = {"prev_month": prev_month, "next_month": next_month}

    sql = "SELECT " \
          "xlmmshop.linkid, " \
          "xlmmshop.ordernum, " \
          "xlmmshop.linkname, " \
          "clicks_tab.clicks " \
          "FROM " \
          "(SELECT  " \
          "    linkid, SUM(ordernumcount) AS ordernum, linkname " \
          "  FROM " \
          "     flashsale_tongji_shopping_day " \
          " WHERE " \
          "      tongjidate BETWEEN '{0}' AND '{1}' " \
          "  GROUP BY linkid " \
          " ORDER BY ordernum DESC " \
          "  LIMIT 100) AS xlmmshop " \
          "      LEFT JOIN " \
          " (SELECT  " \
          "     linkid, SUM(valid_num) AS clicks " \
          " FROM " \
          "     flashsale_clickcount " \
          " WHERE " \
          "    date BETWEEN '{0}' AND '{1}' " \
          " GROUP BY linkid) AS clicks_tab ON xlmmshop.linkid = clicks_tab.linkid".format(date_from,
                                                                                          date_to)  # 注意时间段  要加上

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    cursor.close()
    id = []
    for i in raw:
        id.append(i[0])

    sum_order_list_next = []
    # 计算下个月的点击数量
    next_date = date_to + datetime.timedelta(days=1)
    next_month_from, next_month_to, next_next_month_from, next_next_month_to = get_next_month(next_date)

    for j in id:  # 对每一个id 求 下个月的点击
        shops = StatisticsShoppingByDay.objects.filter(linkid=j, tongjidate__gt=next_month_from,
                                                       tongjidate__lt=next_month_to)
        sum_order = shops.aggregate(total_ordernumcount=Sum('ordernumcount')).get('total_ordernumcount') or 0
        sum_order_list_next.append(sum_order)
    sum_order_list_next_next = []
    for j in id:  # 对每一个id 求 下 下 个月的点击
        shops = StatisticsShoppingByDay.objects.filter(linkid=j, tongjidate__gt=next_next_month_from,
                                                       tongjidate__lt=next_next_month_to)
        sum_order = shops.aggregate(total_ordernumcount=Sum('ordernumcount')).get('total_ordernumcount') or 0
        sum_order_list_next_next.append(sum_order)

    data = []
    count_index = 0
    for x in raw:
        data_entry = {"id": x[0], "order": x[1], "nick": x[2], "click": x[3],
                      "next_month": sum_order_list_next[count_index],
                      "next_next_month": sum_order_list_next_next[count_index]}
        data.append(data_entry)
        count_index += 1
    return render_to_response('analysis/order_iter_top100.html',
                              {'data': data, 'date_dic': date_dic},
                              context_instance=RequestContext(request))
