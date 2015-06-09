# coding=utf-8
__author__ = 'linjie'

import datetime
from .models import XiaoluMama
from flashsale.clickcount.models import ClickCount, WeekCount
from flashsale.clickrebeta.models import StatisticsShoppingByDay


def xlmm_Click_Top_By_Day(request):
    data = []
    today = datetime.date.today()
    prev_day = today - datetime.timedelta(days=1)
    content = request.REQUEST
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

    xlmms = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED)
    click_counts = ClickCount.objects.filter(write_time__gt=time_from, write_time__lt=time_to).order_by('-valid_num')[:50]
    for click_count in click_counts:
        for xlmm in xlmms:
            if click_count.linkid == xlmm.id:
                data_entry = {'xlmm': xlmm.id, 'click_count': click_count.valid_num}
                data.append(data_entry)
    date_dic = {"prev_day": prev_day, "target_day": target_date, "next_day": next_day}
    return data, date_dic


def xlmm_Order_Top_By_Day(request):
    data = []
    today = datetime.date.today()
    prev_day = today - datetime.timedelta(days=1)
    content = request.REQUEST
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
    xlmms = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED)
    # 找出某天的订单前50
    order_counts = StatisticsShoppingByDay.objects.filter(tongjidate=time_from).order_by(
        '-ordernumcount')[:50]
    for order_count in order_counts:
        for xlmm in xlmms:
            if xlmm.pk == order_count.linkid:
                data_entry = {'xlmm': xlmm.id, 'ordernumcount': order_count.ordernumcount}
                data.append(data_entry)
    date_dic = {"prev_day": prev_day, "target_day": target_date, "next_day": next_day}
    return data, date_dic


def xlmm_Conversion_Top_By_Week(request):
    data = []
    today = datetime.date.today()
    prev_day = today - datetime.timedelta(days=1)
    content = request.REQUEST
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

    xlmms = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED)
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
    content = request.REQUEST
    daystr = content.get("week", None)
    data = []
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_week_from_date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_week_from_date(target_date)

    prev_week = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_week = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)

    xlmms = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED)

    for xlmm in xlmms:
        click_counts = ClickCount.objects.filter(write_time__gt=date_from, write_time__lt=date_to, linkid=xlmm.id)
        # 一个妈妈的一周总点击
        xlmm_total_valid_num = click_counts.aggregate(xlmm_total_valid_num=Sum('valid_num')).get('xlmm_total_valid_num') or 0
        data_entry = {'xlmm': xlmm.id, 'click_count': xlmm_total_valid_num}
        data.append(data_entry)
        sorted_data = sorted(data, key=operator.itemgetter('click_count'))  # 排序
        data = sorted_data[:len(sorted_data) - 51:-1]  # 列表切片 并逆序

    date_dic = {"prev_week": prev_week, "next_week": next_week}
    return data, date_dic


def get_week_from_date(date_time):
    days = date_time.isoweekday()
    day_from = date_time - datetime.timedelta(days=days - 1)
    day_to = day_from + datetime.timedelta(days=6)
    date_from = datetime.datetime(day_from.year, day_from.month, day_from.day, 0, 0, 0)  # 上一周的开始时间
    date_to = datetime.datetime(day_to.year, day_to.month, day_to.day, 23, 59, 59)  # 上一周的结束时间
    return date_from, date_to


def xlmm_Order_Top_By_Week(request):
    content = request.REQUEST
    daystr = content.get("week", None)
    data = []
    if daystr:
        year, month, day = daystr.split('-')
        target_date = datetime.datetime(int(year), int(month), int(day))
        date_from, date_to = get_week_from_date(target_date)
    else:
        target_date = datetime.datetime.now()
        date_from, date_to = get_week_from_date(target_date)
    prev_week = datetime.date(date_from.year, date_from.month, date_from.day) - datetime.timedelta(days=1)
    next_week = datetime.date(date_to.year, date_to.month, date_to.day) + datetime.timedelta(days=1)

    xlmms = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED)

    for xlmm in xlmms:
        order_counts = StatisticsShoppingByDay.objects.filter(tongjidate__gt=date_from, tongjidate__lt=date_to, linkid=xlmm.id)
        # 一个妈妈的一周订单
        xlmm_total_order_counts = order_counts.aggregate(xlmm_total_order_counts=Sum('ordernumcount')).get(
            'xlmm_total_order_counts') or 0
        data_entry = {'xlmm': xlmm.id, 'order_count': xlmm_total_order_counts}
        data.append(data_entry)
        sorted_data = sorted(data, key=operator.itemgetter('order_count'))  # 排序
        data = sorted_data[:len(sorted_data) - 51:-1]  # 列表切片 并逆序

    date_dic = {"prev_week": prev_week, "next_week": next_week}
    return data, date_dic


def xlmm_Click_Top_By_Month(request):
    content = request.REQUEST
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

    xlmms = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED)

    for xlmm in xlmms:
        click_counts = ClickCount.objects.filter(write_time__gt=date_from, write_time__lt=date_to, linkid=xlmm.id)
        # 一个妈妈的一周点击
        xlmm_total_valid_num = click_counts.aggregate(xlmm_total_valid_num=Sum('valid_num')).get(
            'xlmm_total_valid_num') or 0
        data_entry = {'xlmm': xlmm.id, 'click_count': xlmm_total_valid_num}
        data.append(data_entry)
        sorted_data = sorted(data, key=operator.itemgetter('click_count'))  # 排序
        data = sorted_data[:len(sorted_data) - 51:-1]  # 列表切片 并逆序

    date_dic = {"prev_month": prev_month, "next_month": next_month}
    return data, date_dic


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
    content = request.REQUEST
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
    xlmms = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED)

    for xlmm in xlmms:
        order_counts = StatisticsShoppingByDay.objects.filter(tongjidate__gt=date_from, tongjidate__lt=date_to, linkid=xlmm.id)
        xlmm_total_ordernumcount = order_counts.aggregate(xlmm_total_ordernumcount=Sum('ordernumcount')).get(
            'xlmm_total_ordernumcount') or 0
        data_entry = {'xlmm': xlmm.id, 'order_count': xlmm_total_ordernumcount}
        data.append(data_entry)
        sorted_data = sorted(data, key=operator.itemgetter('order_count'))  # 排序
        data = sorted_data[:len(sorted_data) - 51:-1]  # 列表切片 并逆序

    date_dic = {"prev_month": prev_month, "next_month": next_month}
    return data, date_dic


def xlmm_Convers_Top_By_Month(request):
    # 转化率  购买人数/点击人数
    content = request.REQUEST
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
    xlmms = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED)
    for xlmm in xlmms:
        buyercounts = StatisticsShoppingByDay.objects.filter(tongjidate__gt=date_from, tongjidate__lt=date_to, linkid=xlmm.id)
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