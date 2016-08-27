# encoding=utf8
from itertools import groupby
from datetime import datetime, timedelta
from django.shortcuts import render
from django.db import connections
from flashsale.pay.models.user import Customer
from flashsale.pay.models.trade import SaleTrade
from flashsale.daystats.lib.chart import generate_chart, generate_date


def process_data(data):
    def bydate(item):
        return item['created'].date()

    def count(item):
        return item[0], len(list(item[1]))

    data = groupby(data, bydate)
    data = map(count, data)
    return [x[1] for x in data]


def execute_sql(cursor, sql):
    cursor.execute(sql)
    return cursor.fetchall()


def index(req):
    now = datetime.now()
    p_start_date = req.GET.get('start_date', '2016-07-01')
    p_end_date = req.GET.get('end_date', '%s-%s-%s' % (now.year, now.month, now.day+1))
    start_date = datetime.strptime(p_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(p_end_date, '%Y-%m-%d')

    cursor = connections['product'].cursor()

    where = ' created > "{0}" and created < "{1}" '.format(p_start_date, p_end_date)

    sql = """SELECT DATE(created) as day, count(DATE(created))
             FROM xiaoludb.flashsale_customer where {0} group by DATE(created);""".format(where)
    customers = execute_sql(cursor, sql)

    sql = """SELECT DATE(created), count(DATE(created))
             FROM xiaoludb.xiaolumm_xiaolumama WHERE {0} GROUP by DATE(created) """.format(where)
    xiaolumm = execute_sql(cursor, sql)

    sql = """SELECT DATE(created), count(DATE(created))
             FROM xiaoludb.flashsale_trade where {0} group by DATE(created)""".format(where)
    trades_all = execute_sql(cursor, sql)

    sql = """SELECT DATE(created), count(DATE(created))
             FROM xiaoludb.flashsale_trade where pay_time is not null and {0} group by DATE(created)""".format(where)
    trades_pay = execute_sql(cursor, sql)

    sql = """
        SELECT DATE(flashsale_trade.pay_time), count(DATE(flashsale_trade.pay_time))
        FROM xiaoludb.flashsale_trade
        join xiaoludb.flashsale_customer on flashsale_customer.id=flashsale_trade.buyer_id
        join xiaoludb.xiaolumm_xiaolumama on flashsale_customer.unionid=xiaolumm_xiaolumama.openid
        where flashsale_trade.created > "{0}"
            and flashsale_trade.created < "{1}"
            and flashsale_trade.pay_time is not null
        group by DATE(flashsale_trade.created)
    """.format(p_start_date, p_end_date)
    xiaolumm_trades = execute_sql(cursor, sql)

    sql = """
        SELECT DATE(subscribe_time), count(DATE(subscribe_time))
        FROM xiaoludb.shop_weixin_fans group by DATE(subscribe_time)
    """
    weixin_fans = execute_sql(cursor, sql)

    customer_items = {
        '新增小鹿妈妈': [int(x[1]) for x in xiaolumm],
        '新增用户数': [int(x[1]) for x in customers],
    }
    trade_items = {
        '付款订单数': [int(x[1]) for x in trades_pay],
        '所有订单（含未付款）': [int(x[1]) for x in trades_all],
        '来自小鹿妈妈订单': [int(x[1]) for x in xiaolumm_trades],
    }
    weixin_items = {
        '小鹿美美粉丝': [int(x[1]) for x in weixin_fans],
    }

    x_axis = [x.strftime('%Y-%m-%d') for x in generate_date(start_date, end_date)]
    x1_axis = [x[0].strftime('%Y-%m-%d') for x in weixin_fans if x[0] is not None]

    charts = []
    charts.append(generate_chart('customer', x_axis, customer_items))
    charts.append(generate_chart('trade', x_axis, trade_items))
    charts.append(generate_chart('公众号', x1_axis, weixin_items, width='1200px'))

    return render(req, 'customer/index.html', {'charts': charts})
