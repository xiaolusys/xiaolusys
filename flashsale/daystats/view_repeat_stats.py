# -*- coding:utf-8 -*-
from __future__ import division

from django.views.generic import View
from django.shortcuts import render
import datetime
from calendar import monthrange
from flashsale.daystats.tasks import task_calc_xlmm, task_calc_package
from flashsale.pay.models.user import Customer
from flashsale.pay.models.trade import SaleTrade


def get_new_user(user_data, old_user):
    new_user = []
    for val in user_data:
        if val not in old_user:
            new_user.append(val[0])
    return new_user


def next_month(date):
    year = date.year
    month = date.month + 1

    if month > 12:
        year = year + 1
        month = month % 12
    return datetime.datetime(year, month, 1)


def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


def last_day_of_week(day):
    delta = datetime.timedelta(days=(6-day.weekday()))
    return day + delta


def next_week(day):
    return last_day_of_week(day) + datetime.timedelta(days=1)


def generate_date_range(start, end, category='month'):
    while start < end:
        if category == 'month':
            day = last_day_of_month(start)
        elif category == 'week':
            day = last_day_of_week(start)

        if day > end:
            day = end

        yield (start, day)
        if category == 'month':
            start = next_month(start)
        elif category == 'week':
            start = next_week(start)


def calc_customer_repeat_buy(start_date, end_date, category='month', user_type='all'):
    date_range = list(generate_date_range(start_date, end_date, category=category))

    repeat_num = len(date_range)

    orders = []
    new_customers = []

    for start_date, end_date in date_range:
        if user_type == 'all':
            customers = Customer.objects.filter(first_paytime__gt=start_date, first_paytime__lt=end_date).values('id')
            data = set([x['id'] for x in customers])
        elif user_type == 'xiaolumm':
            sql = """SELECT flashsale_customer.id
                     FROM flashsale_customer
                     join xiaolumm_xiaolumama on flashsale_customer.unionid=xiaolumm_xiaolumama.openid
                     where flashsale_customer.first_paytime >= "%s" and flashsale_customer.first_paytime < "%s"
                     order by flashsale_customer.first_paytime desc""" % (start_date, end_date)
            customers = Customer.objects.raw(sql)
            data = set([x.id for x in customers])
        new_customers.append({
            'date': start_date,
            'data': data,
        })

        trades = SaleTrade.objects.filter(
            pay_time__isnull=False, pay_time__gt=start_date, pay_time__lt=end_date).values('buyer_id')
        orders.append({
            'date': start_date,
            'data': set([x['buyer_id'] for x in trades])
        })

    rowdata = []

    for row in range(0, repeat_num):
        coldata = []
        coldata.append(orders[row]['date'].date())
        for col in range(0, repeat_num):
            if row <= col:
                i1 = new_customers[row]['data']
                i2 = orders[col]['data']
                num = len(i1 & i2)
                data = num
            else:
                i1 = rowdata[col][row+1]
                i2 = rowdata[col][col+1]
                try:
                    percent = round((i1 * 1.0 / i2) * 100, 2)
                except Exception:
                    percent = 0
                data = '%s%%' % percent
            coldata.append(data)
        rowdata.append(coldata)
    return rowdata


class StatsRepeatView(View):
    @staticmethod
    def get(request):
        content = request.GET
        today = datetime.datetime.now()
        start_time_str = content.get("df", None)
        end_time_str = content.get("dt", None)
        category = content.get('category', 'month')
        user_type = content.get('user_type', 'all')

        if start_time_str:
            year, month, day = start_time_str.split('-')
            start_date = datetime.datetime(int(year), int(month), int(day))
            if start_date > today:
                start_date = today
        else:
            start_date = today - datetime.timedelta(days=monthrange(today.year, today.month)[1])
        if end_time_str:
            year, month, day = end_time_str.split('-')
            end_date = datetime.datetime(int(year), int(month), int(day))
        else:
            end_date = today
        """找出选择的开始月份和结束月份"""
        start_month = start_date.month
        end_month = end_date.month
        month_range = range(start_month + 1, end_month + 1)
        # task_id = task_calc_new_user_repeat.delay(start_date, end_date)  # 计算重复购买
        # send_tasks = task_calc_xlmm.delay(start_time_str, end_time_str)  # 计算小鹿妈妈购买
        # task_id_sale = task_calc_package.delay(start_date, end_date)  # 计算包裹数量

        customer_repeat_buy_data = calc_customer_repeat_buy(
            start_date, end_date, category=category, user_type=user_type)
        return render(
            request,
            "xiaolumm/data2repeatshop.html",
            {
                # "task_id": task_id,
                'customer_repeat_buy_data': customer_repeat_buy_data,
                # "task_id_2": send_tasks,
                # "task_id_sale": task_id_sale,
                "start_date": start_date.date(),
                "end_date": end_date.date(),
                "month_range": range(1, len(customer_repeat_buy_data)+1),
                'category': category,
                'user_type': user_type,
            }
        )


from flashsale.daystats.models import DailyStat
from shopback.trades.models import MergeTrade


class StatsSaleView(View):
    @staticmethod
    def get(request):
        content = request.GET
        today = datetime.date.today()
        start_time_str = content.get("df", None)
        end_time_str = content.get("dt", None)
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
        """找出选择的开始月份和结束月份"""
        start_month = start_date.month
        end_month = end_date.month
        month_range = range(start_month, end_month + 1)
        task_id = task_calc_package.delay(start_date, end_date, False)
        return render(
            request,
            "xiaolumm/data2sale.html",
            {
                "month_range": month_range,
                "task_id_sale": task_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )


class StatsSalePeopleView(View):
    @staticmethod
    def get(request):
        content = request.GET
        start_time_str = content.get("df", None)
        end_time_str = content.get("dt", None)
        send_tasks = task_calc_xlmm.delay(start_time_str, end_time_str)
        return render(
            request,
            "xiaolumm/data2salepeople.html",
            {"task_id": send_tasks}
        )
