# encoding=utf8
from itertools import groupby
from datetime import datetime, timedelta
from django.shortcuts import render
from django.template import Template, Context
from django.db import connections
from flashsale.pay.models.user import Customer
from flashsale.pay.models.trade import SaleTrade


def process_data(data):
    def bydate(item):
        return item['created'].date()

    def count(item):
        return item[0], len(list(item[1]))

    data = groupby(data, bydate)
    data = map(count, data)
    return [x[1] for x in data]


def generate_date(start_date, end_date):
    date = start_date

    ranges = []
    while date <= end_date:
        ranges.append(date)
        date = date + timedelta(days=1)
    return ranges


def generate_chart(name, x_axis, items):

    tpl = Template("""[
    {% for k, v in items.items %}
    {
        name: "{{ k }}",
        type: 'line',
        data: {{ v }},
    },
    {% endfor %}
    ]""")
    context = Context({'items': items})
    series = tpl.render(context)

    return {
        'name': name,
        'x_axis': x_axis,
        'series': series
    }


def execute_sql(cursor, sql):
    cursor.execute(sql)
    return cursor.fetchall()


def index(req):
    now = datetime.now()
    p_start_date = req.GET.get('start_date', '2016-07-01')
    p_end_date = req.GET.get('end_date', '%s-%s-%s' % (now.year, now.month, now.day))
    start_date = datetime.strptime(p_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(p_end_date, '%Y-%m-%d')

    # customers = Customer.objects.using('product').filter(
    #     created__gte=start_date, created__lt=end_date).values('created')

    where = ' created > "{0}" and created < "{1}" '.format(p_start_date, p_end_date)

    cursor = connections['product'].cursor()
    sql = 'SELECT DATE(created) as day, count(DATE(created)) FROM xiaoludb.flashsale_customer where {0} group by DATE(created);'.format(where)
    print sql
    customers = execute_sql(cursor, sql)

    sql = 'SELECT DATE(created), count(DATE(created)) FROM xiaoludb.flashsale_trade where {0} group by DATE(created)'.format(where)
    print sql
    trades_all = execute_sql(cursor, sql)

    sql = 'SELECT DATE(created), count(DATE(created)) FROM xiaoludb.flashsale_trade where pay_time is not null and {0} group by DATE(created)'.format(where)
    print sql
    trades_pay = execute_sql(cursor, sql)

    # trades_all = SaleTrade.objects.using('product').filter(
        # created__gte=start_date, created__lt=end_date).values('created')
    # trades_pay = SaleTrade.objects.using('product').filter(
        # created__gte=start_date, created__lt=end_date, pay_time__isnull=False).values('created')

    customer_items = {
        # '增加用户数': process_data(customers),
        '增加用户数': [int(x[1]) for x in customers],
    }
    trade_items = {
        '付款订单数': [int(x[1]) for x in trades_pay],
        'trade_all_data': [int(x[1]) for x in trades_all],
    }

    x_axis = [x.strftime('%Y-%m-%d') for x in generate_date(start_date, end_date)]

    charts = []
    charts.append(generate_chart('customer', x_axis, customer_items))
    charts.append(generate_chart('trade', x_axis, trade_items))

    return render(req, 'customer/index.html', {'charts': charts})
