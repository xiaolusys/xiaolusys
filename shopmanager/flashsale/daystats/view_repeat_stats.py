# -*- coding:utf-8 -*-
from __future__ import division

from datetime import datetime, timedelta
from django.views.generic import View
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db import connection
import datetime
from calendar import monthrange
from flashsale.clickrebeta.models import StatisticsShopping
from django.db.models import Sum
from flashsale.xiaolumm.models import XiaoluMama
from django.conf import settings
from shopapp.weixin.models import get_Unionid
from flashsale.daystats.tasks import task_calc_xlmm, task_calc_new_user_repeat, task_calc_package
from flashsale.pay.models.user import Customer
from flashsale.pay.models.trade import SaleTrade


def get_new_user(user_data, old_user):
    new_user = []
    for val in user_data:
        if val not in old_user:
            new_user.append(val[0])
    return new_user


def calc_customer_repeat_buy(start_date, end_date, category='month'):
    if category == 'month':
        n = 31
    elif category == 'week':
        n = 7

    delta = timedelta(days=n)
    repeat_num = int((end_date - start_date).days / n) + 1

    orders = []
    new_customers = []

    for i in range(0, repeat_num):
        end_date = start_date + delta

        customers = Customer.objects.filter(first_paytime__gt=start_date, first_paytime__lt=end_date).values('id')
        new_customers.append({
            'date': start_date,
            'data': set([x['id'] for x in customers])
        })

        trades = SaleTrade.objects.filter(pay_time__isnull=False, pay_time__gt=start_date, pay_time__lt=end_date).values('buyer_id')
        orders.append({
            'date': start_date,
            'data': set([x['buyer_id'] for x in trades])
        })
        start_date = end_date

    rowdata = []

    for row in range(0, repeat_num):
        coldata = []
        coldata.append(orders[row]['date'])
        for col in range(0, repeat_num):
            if row <= col:
                i1 = new_customers[row]['data']
                i2 = orders[col]['data']
                num = len(i1 & i2)
                try:
                    percent = int((num * 1.0 / len(i1)) * 100)
                except Exception:
                    percent = 0
            else:
                num = 0
                percent = 0
            coldata.append((num, percent))
        rowdata.append(coldata)
    return rowdata


class StatsRepeatView(View):
    @staticmethod
    def get(request):
        content = request.REQUEST
        today = datetime.date.today()
        start_time_str = content.get("df", None)
        end_time_str = content.get("dt", None)
        category = content.get('category', 'month')
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
        month_range = range(start_month + 1, end_month + 1)
        # task_id = task_calc_new_user_repeat.delay(start_date, end_date)  # 计算重复购买
        # send_tasks = task_calc_xlmm.delay(start_time_str, end_time_str)  # 计算小鹿妈妈购买
        # task_id_sale = task_calc_package.delay(start_date, end_date)  # 计算包裹数量

        customer_repeat_buy_data = calc_customer_repeat_buy(start_date, end_date, category=category)
        return render_to_response(
            "xiaolumm/data2repeatshop.html",
            {
                # "task_id": task_id,
                'customer_repeat_buy_data': customer_repeat_buy_data,
                # "task_id_2": send_tasks,
                # "task_id_sale": task_id_sale,
                "start_date": start_date,
                "end_date": end_date,
                "month_range": range(1, len(customer_repeat_buy_data)+1),
                'category': category,
            },
            context_instance=RequestContext(request)
        )


from flashsale.daystats.models import DailyStat
from shopback.trades.models import MergeTrade


class StatsSaleView(View):
    @staticmethod
    def get(request):
        content = request.REQUEST
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
        return render_to_response(
            "xiaolumm/data2sale.html",
            {
                "month_range": month_range,
                "task_id_sale": task_id,
                "start_date": start_date,
                "end_date": end_date
            },
            context_instance=RequestContext(request)
        )


class StatsSalePeopleView(View):
    @staticmethod
    def get(request):
        content = request.REQUEST
        start_time_str = content.get("df", None)
        end_time_str = content.get("dt", None)
        send_tasks = task_calc_xlmm.delay(start_time_str, end_time_str)
        return render_to_response("xiaolumm/data2salepeople.html",
                                  {"task_id": send_tasks},
                                  context_instance=RequestContext(request))
