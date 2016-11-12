# coding=utf-8
__author__ = 'linjie'

import datetime
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.clickcount.models import ClickCount, WeekCount
from flashsale.clickrebeta.models import StatisticsShoppingByDay
from django.db import connection, transaction
from django.contrib.auth.models import User


def xlmm_Click_Top_By_Day(request):
    today = datetime.date.today()
    prev_day = today - datetime.timedelta(days=1)
    content = request.GET
    daystr = content.get("day", None)
    target_date = today
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.date(int(year), int(month), int(day))
        if target_date > today:
            target_date = today
    prev_day = target_date - datetime.timedelta(days=1)
    next_day = None
    if target_date < today:  # 如果目标日期比今天小
        next_day = target_date + datetime.timedelta(days=1)  # 下一天 则是目标日期加上一天

    time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
    time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

    # manager        username

    sql = "SELECT C.xlmm_total_valid_num,C.linkid,C.weikefu,C.xlmm_total_buyercount,C.xlmm_total_ordernumcount,C.baifenbi,D.username FROM (SELECT AA.xlmm_total_valid_num,AA.linkid,AA.weikefu,BB.xlmm_total_buyercount,BB.xlmm_total_ordernumcount," \
          "(IF(AA.xlmm_total_valid_num=0,0,100*(BB.xlmm_total_buyercount/AA.xlmm_total_valid_num))) AS baifenbi, AA.manager FROM" \
          "(SELECT A.linkid, A.xlmm_total_valid_num, B.weikefu,B.manager FROM " \
          "(SELECT linkid,SUM(valid_num) AS xlmm_total_valid_num  FROM flashsale_clickcount WHERE linkid IN " \
          "(SELECT id FROM xiaolumm_xiaolumama WHERE agencylevel IN (2,3)) AND  write_time  BETWEEN '{0}' AND '{1}' GROUP BY linkid ORDER BY xlmm_total_valid_num DESC LIMIT 50) AS A " \
          "LEFT JOIN xiaolumm_xiaolumama AS B ON A.linkid = B.id) AS AA " \
          "LEFT JOIN (SELECT linkid,sum(ordernumcount) AS xlmm_total_ordernumcount,sum(buyercount) AS xlmm_total_buyercount" \
          " FROM flashsale_tongji_shopping_day WHERE  tongjidate  BETWEEN '{0}' AND '{1}'   GROUP BY linkid ) AS BB ON AA.linkid = BB.linkid ) AS C LEFT JOIN (SELECT id,username FROM auth_user) AS D ON C.manager=D.id".format(
        time_from, time_to)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    cursor.close()
    date_dic = {"prev_day": prev_day, "target_day": target_date, "next_day": next_day}
    return raw, date_dic


def xlmm_Order_Top_By_Day(request):
    today = datetime.date.today()
    prev_day = today - datetime.timedelta(days=1)
    content = request.GET
    daystr = content.get("day", None)
    target_date = today
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.date(int(year), int(month), int(day))
        if target_date > today:
            target_date = today
    prev_day = target_date - datetime.timedelta(days=1)
    next_day = None
    if target_date < today:  # 如果目标日期比今天小
        next_day = target_date + datetime.timedelta(days=1)  # 下一天 则是目标日期加上一天

    time_from = datetime.date(target_date.year, target_date.month, target_date.day)

    sql = "SELECT C.linkid,C.xlmm_total_ordernumcount,C.weikefu,C.xlmm_total_valid_num,C.xlmm_total_buyercount,C.baifenbi,D.username FROM (SELECT AA.linkid,AA.xlmm_total_ordernumcount,AA.weikefu,BB.xlmm_total_valid_num,AA.xlmm_total_buyercount ,(IF(BB.xlmm_total_valid_num=0,0,100*(AA.xlmm_total_buyercount/BB.xlmm_total_valid_num))) AS baifenbi ,AA.manager FROM " \
          "(SELECT A.linkid ,A.xlmm_total_ordernumcount,A.xlmm_total_buyercount,B.weikefu,B.manager " \
          "FROM " + "(SELECT linkid, SUM(buyercount) AS xlmm_total_buyercount,SUM(ordernumcount) AS xlmm_total_ordernumcount " \
                    "FROM flashsale_tongji_shopping_day WHERE tongjidate ='{0}' AND" \
                    " linkid IN (SELECT id FROM xiaolumm_xiaolumama WHERE agencylevel IN (2,3))" \
                    "GROUP BY linkid ORDER BY xlmm_total_ordernumcount" \
                    " DESC LIMIT 50) AS A LEFT JOIN xiaolumm_xiaolumama AS B ON A.linkid = B.id) AS AA LEFT JOIN " \
                    "(SELECT sum(valid_num) AS xlmm_total_valid_num,linkid FROM flashsale_clickcount WHERE date = '{0}' GROUP BY linkid) as BB ON AA.linkid=BB.linkid ) AS C LEFT JOIN (SELECT id,username FROM auth_user) AS D ON C.manager=D.id".format(
        time_from)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    date_dic = {"prev_day": prev_day, "target_day": target_date, "next_day": next_day}
    return raw, date_dic


def xlmm_Conversion_Top_By_Week(request):
    content = request.GET
    data = []
    today = datetime.date.today()
    prev_day = today - datetime.timedelta(days=1)
    daystr = content.get("week", None)
    week_code = str(today.year) + prev_day.strftime('%U')
    target_week = str(today.year) + today.strftime("%U")  # 目标周编码
    if daystr:
        target_week = daystr
        if int(target_week) > int(str(today.year) + today.strftime("%U")):
            target_week = str(today.year) + today.strftime("%U")
    prev_week = str(int(target_week) - 1)
    next_week = None
    if int(target_week) < int(str(today.year) + today.strftime("%U")):  # 如果目标周比本周
        next_week = str(int(target_week) + 1)  # 下一天 则是目标日期加上一天

    xlmms = XiaoluMama.objects.filter(agencylevel__gte=XiaoluMama.VIP_LEVEL, charge_status=XiaoluMama.CHARGED)
    # 找出某天的转化前50
    week_counts = WeekCount.objects.filter(week_code=target_week).order_by('-conversion_rate')[:50]
    for week_count in week_counts:
        for xlmm in xlmms:
            if xlmm.pk == week_count.linkid:
                data_entry = {'xlmm': xlmm.id, 'conversion_rate': week_count.conversion_rate}
                data.append(data_entry)
    date_dic = {"prev_week": prev_week, "target_week": target_week, "next_week": next_week}
    return data, date_dic


from django.db.models import Sum

import operator  # 导入排序模块


def xlmm_Click_Top_By_Week(request):
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

    sql = "SELECT C.xlmm_total_valid_num,C.linkid,C.weikefu,C.xlmm_total_buyercount,C.xlmm_total_ordernumcount,C.baifenbi,D.username FROM (SELECT AA.xlmm_total_valid_num,AA.linkid,AA.weikefu,BB.xlmm_total_buyercount,BB.xlmm_total_ordernumcount," \
          "(IF(AA.xlmm_total_valid_num=0,0,100*(BB.xlmm_total_buyercount/AA.xlmm_total_valid_num))) AS baifenbi, AA.manager FROM" \
          "(SELECT A.linkid, A.xlmm_total_valid_num, B.weikefu,B.manager FROM " \
          "(SELECT linkid,SUM(valid_num) AS xlmm_total_valid_num  FROM flashsale_clickcount WHERE linkid IN " \
          "(SELECT id FROM xiaolumm_xiaolumama WHERE agencylevel IN (2,3)) AND  write_time  BETWEEN '{0}' AND '{1}' GROUP BY linkid ORDER BY xlmm_total_valid_num DESC LIMIT 50) AS A " \
          "LEFT JOIN xiaolumm_xiaolumama AS B ON A.linkid = B.id) AS AA " \
          "LEFT JOIN (SELECT linkid,sum(ordernumcount) AS xlmm_total_ordernumcount,sum(buyercount) AS xlmm_total_buyercount" \
          " FROM flashsale_tongji_shopping_day WHERE  tongjidate  BETWEEN '{0}' AND '{1}'   GROUP BY linkid ) AS BB ON AA.linkid = BB.linkid ) AS C LEFT JOIN (SELECT id,username FROM auth_user) AS D ON C.manager=D.id".format(
        date_from, date_to)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()

    date_dic = {"prev_week": prev_week, "next_week": next_week}
    return raw, date_dic


def get_week_from_date(date_time):
    days = date_time.isoweekday()
    day_from = date_time - datetime.timedelta(days=days - 1)
    day_to = day_from + datetime.timedelta(days=6)
    date_from = datetime.datetime(day_from.year, day_from.month, day_from.day, 0, 0, 0)  # 上一周的开始时间
    date_to = datetime.datetime(day_to.year, day_to.month, day_to.day, 23, 59, 59)  # 上一周的结束时间
    return date_from, date_to


def xlmm_Order_Top_By_Week(request):
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

    sql = "SELECT C.linkid,C.xlmm_total_ordernumcount,C.weikefu,C.xlmm_total_valid_num,C.xlmm_total_buyercount,C.baifenbi,D.username FROM (SELECT AA.linkid,AA.xlmm_total_ordernumcount,AA.weikefu,BB.xlmm_total_valid_num,AA.xlmm_total_buyercount ,(IF(BB.xlmm_total_valid_num=0,0,100*(AA.xlmm_total_buyercount/BB.xlmm_total_valid_num))) AS baifenbi ,AA.manager FROM " \
          "(SELECT A.linkid ,A.xlmm_total_ordernumcount,A.xlmm_total_buyercount,B.weikefu,B.manager " \
          "FROM " + "(SELECT linkid, SUM(buyercount) AS xlmm_total_buyercount,SUM(ordernumcount) AS xlmm_total_ordernumcount " \
                    "FROM flashsale_tongji_shopping_day WHERE tongjidate BETWEEN '{0}' AND '{1}' AND" \
                    " linkid IN (SELECT id FROM xiaolumm_xiaolumama WHERE agencylevel IN (2,3))" \
                    "GROUP BY linkid ORDER BY xlmm_total_ordernumcount" \
                    " DESC LIMIT 50) AS A LEFT JOIN xiaolumm_xiaolumama AS B ON A.linkid = B.id) AS AA LEFT JOIN " \
                    "(SELECT sum(valid_num) AS xlmm_total_valid_num,linkid FROM flashsale_clickcount WHERE  write_time BETWEEN '{0}' AND '{1}' GROUP BY linkid) as BB ON AA.linkid=BB.linkid ) AS C LEFT JOIN (SELECT id,username FROM auth_user) AS D ON C.manager=D.id".format(
        date_from, date_to)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()

    date_dic = {"prev_week": prev_week, "next_week": next_week}
    return raw, date_dic


def xlmm_Click_Top_By_Month(request):
    content = request.GET
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

    sql = "SELECT C.xlmm_total_valid_num,C.linkid,C.weikefu,C.xlmm_total_buyercount,C.xlmm_total_ordernumcount,C.baifenbi,D.username FROM (SELECT AA.xlmm_total_valid_num,AA.linkid,AA.weikefu,BB.xlmm_total_buyercount,BB.xlmm_total_ordernumcount," \
          "(IF(AA.xlmm_total_valid_num=0,0,100*(BB.xlmm_total_buyercount/AA.xlmm_total_valid_num))) AS baifenbi, AA.manager FROM" \
          "(SELECT A.linkid, A.xlmm_total_valid_num, B.weikefu,B.manager FROM " \
          "(SELECT linkid,SUM(valid_num) AS xlmm_total_valid_num  FROM flashsale_clickcount WHERE linkid IN " \
          "(SELECT id FROM xiaolumm_xiaolumama WHERE agencylevel IN (2,3)) AND  write_time  BETWEEN '{0}' AND '{1}' GROUP BY linkid ORDER BY xlmm_total_valid_num DESC LIMIT 50) AS A " \
          "LEFT JOIN xiaolumm_xiaolumama AS B ON A.linkid = B.id) AS AA " \
          "LEFT JOIN (SELECT linkid,sum(ordernumcount) AS xlmm_total_ordernumcount,sum(buyercount) AS xlmm_total_buyercount" \
          " FROM flashsale_tongji_shopping_day WHERE  tongjidate  BETWEEN '{0}' AND '{1}'   GROUP BY linkid ) AS BB ON AA.linkid = BB.linkid ) AS C LEFT JOIN (SELECT id,username FROM auth_user) AS D ON C.manager=D.id".format(
        date_from, date_to)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()

    date_dic = {"prev_month": prev_month, "next_month": next_month}
    return raw, date_dic


def get_month_from_date(date_time):
    day_from = datetime.date(date_time.year, date_time.month, 1)  # 这个月的开始时间
    if date_time.month == 12:
        day_to = datetime.date(date_time.year, date_time.month, 31)
    else:
        day_to = datetime.date(date_time.year, date_time.month + 1, 1) - datetime.timedelta(1)  # 这个月的第一天减去1天
    date_from = datetime.datetime(day_from.year, day_from.month, day_from.day, 0, 0, 0)  # 上一周的开始时间
    date_to = datetime.datetime(day_to.year, day_to.month, day_to.day, 23, 59, 59)  # 上一周的结束时间
    return date_from, date_to


def xlmm_Order_Top_By_Month(request):
    content = request.GET
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

    date_from = datetime.date(date_from.year, date_from.month, date_from.day)
    date_to = datetime.date(date_to.year, date_to.month, date_to.day)

    sql = "SELECT C.linkid,C.xlmm_total_ordernumcount,C.weikefu,C.xlmm_total_valid_num,C.xlmm_total_buyercount,C.baifenbi,D.username FROM (SELECT AA.linkid,AA.xlmm_total_ordernumcount,AA.weikefu,BB.xlmm_total_valid_num,AA.xlmm_total_buyercount ,(IF(BB.xlmm_total_valid_num=0,0,100*(AA.xlmm_total_buyercount/BB.xlmm_total_valid_num))) AS baifenbi ,AA.manager FROM " \
          "(SELECT A.linkid ,A.xlmm_total_ordernumcount,A.xlmm_total_buyercount,B.weikefu,B.manager " \
          "FROM " + "(SELECT linkid, SUM(buyercount) AS xlmm_total_buyercount,SUM(ordernumcount) AS xlmm_total_ordernumcount " \
                    "FROM flashsale_tongji_shopping_day WHERE tongjidate BETWEEN '{0}' AND '{1}' AND" \
                    " linkid IN (SELECT id FROM xiaolumm_xiaolumama WHERE agencylevel IN (2,3))" \
                    "GROUP BY linkid ORDER BY xlmm_total_ordernumcount" \
                    " DESC LIMIT 50) AS A LEFT JOIN xiaolumm_xiaolumama AS B ON A.linkid = B.id) AS AA LEFT JOIN " \
                    "(SELECT sum(valid_num) AS xlmm_total_valid_num,linkid FROM flashsale_clickcount WHERE  write_time BETWEEN '{0}' AND '{1}' GROUP BY linkid) as BB ON AA.linkid=BB.linkid ) AS C LEFT JOIN (SELECT id,username FROM auth_user) AS D ON C.manager=D.id".format(
        date_from, date_to)

    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    date_dic = {"prev_month": prev_month, "next_month": next_month}
    return raw, date_dic


def xlmm_Convers_Top_By_Month(request):
    # 转化率  购买人数/点击人数
    content = request.GET
    daystr = content.get("month", None)
    data = []
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_month_from_date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_month_from_date(target_date)
    prev_month = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_month = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)
    xlmms = XiaoluMama.objects.filter(agencylevel__gte=XiaoluMama.VIP_LEVEL, charge_status=XiaoluMama.CHARGED)
    for xlmm in xlmms:
        buyercounts = StatisticsShoppingByDay.objects.filter(tongjidate__gt=date_from, tongjidate__lt=date_to,
                                                             linkid=xlmm.id)
        xlmm_total_buyercount = buyercounts.aggregate(xlmm_total_buyercount=Sum('buyercount')).get(
            'xlmm_total_buyercount') or 0
        click_counts = ClickCount.objects.filter(write_time__gt=date_from, write_time__lt=date_to, linkid=xlmm.id)
        # 一个妈妈的一月点击
        xlmm_total_valid_num = click_counts.aggregate(xlmm_total_valid_num=Sum('valid_num')).get(
            'xlmm_total_valid_num') or 0
        if xlmm_total_valid_num == 0:
            conversion = 0.0
        else:
            conversion = float(xlmm_total_buyercount) / xlmm_total_valid_num
        data_entry = {'conversion': conversion, 'xlmm': xlmm.id}
        data.append(data_entry)
        sorted_data = sorted(data)  # 排序
        data = sorted_data[:len(sorted_data) - 51:-1]  # 列表切片 并逆序

    date_dic = {"prev_month": prev_month, "next_month": next_month}
    return data, date_dic


def xlmm_TOP50_Manager_Month(request):
    content = request.GET
    daystr = content.get("month", None)
    manager = request.user.id
    if manager is None:
        manager = 0
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_month_from_date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_month_from_date(target_date)
    prev_month = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_month = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)

    date_from = datetime.date(date_from.year, date_from.month, date_from.day)
    date_to = datetime.date(date_to.year, date_to.month, date_to.day)
    sql = "SELECT " \
          " linkid, " \
          " linkname, " \
          " SUM(buyercount) AS xlmm_total_buyercount, " \
          " SUM(ordernumcount) AS xlmm_total_ordernumcount " \
          " FROM " \
          " flashsale_tongji_shopping_day " \
          " WHERE " \
          " tongjidate BETWEEN '{0}' AND '{1}' " \
          " AND linkid IN (SELECT " \
          "  id " \
          "  FROM " \
          "    xiaolumm_xiaolumama " \
          " WHERE " \
          "     agencylevel IN (2,3) AND manager = {2}) " \
          " GROUP BY linkid  " \
          " ORDER BY xlmm_total_ordernumcount DESC " \
          " LIMIT 50".format(date_from, date_to, manager)
    cursor = connection.cursor()
    cursor.execute(sql)
    raw = cursor.fetchall()
    cursor.close()
    date_dic = {"prev_month": prev_month, "month": date_from.strftime("%Y-%m"), "next_month": next_month}
    return raw, date_dic
