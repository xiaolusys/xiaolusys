# encoding=utf8
from datetime import datetime, timedelta
from django.shortcuts import render
from django.db import connections

from flashsale.daystats.lib.db import execute_sql, get_cursor
from flashsale.daystats.lib.chart import (
    generate_chart,
    generate_date,
)
from shopback.items.models import Product


def format_datetime(datetime):
    return datetime.strftime('%Y-%m-%d %H:%M:%S')


def index(req):
    now = datetime.now()
    p_start_date = req.GET.get('start_date', '2016-08-01')
    p_end_date = req.GET.get('end_date', '%s-%s-%s' % (now.year, now.month, now.day+1))

    start_date = datetime.strptime(p_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(p_end_date, '%Y-%m-%d')

    cursor = get_cursor()

    sql = """
        select item_id, title, count(*) as count
        from xiaoludb.flashsale_order
        where pay_time >= %s and pay_time < %s
        group by item_id
        order by count desc
        limit 1000
    """
    products = execute_sql(cursor, sql, [format_datetime(start_date), format_datetime(end_date)])

    return render(req, 'yunying/product/index.html', locals())


def show(req, id):
    now = datetime.now()
    p_start_date = req.GET.get('start_date', '2015-01-01')
    p_end_date = req.GET.get('end_date', '%s-%s-%s' % (now.year, now.month, now.day+1))

    start_date = datetime.strptime(p_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(p_end_date, '%Y-%m-%d')

    product = Product.objects.using('product').get(id=id)

    cursor = get_cursor()
    sql = """
        SELECT pay_time, count(DATE(pay_time)) as count
        FROM xiaoludb.flashsale_order
        where item_id=%s
            and pay_time > %s
            and pay_time < %s
        group by DATE(pay_time)
    """
    items = execute_sql(get_cursor(), sql, [id, format_datetime(start_date), format_datetime(end_date)])

    sql = """
        SELECT flashsale_order.title,
            shop_items_productsku.properties_name,
            flashsale_order.total_fee,
            count(*) as count
        FROM xiaoludb.flashsale_order
        join xiaoludb.shop_items_productsku on shop_items_productsku.id=flashsale_order.sku_id
        where flashsale_order.item_id=%s
            and flashsale_order.pay_time > %s
            and flashsale_order.pay_time < %s
        group by flashsale_order.sku_id
        order by flashsale_order.created desc
    """

    order_items = execute_sql(get_cursor(), sql, [id, format_datetime(start_date), format_datetime(end_date)])
    order_items = [x.values()+[x['total_fee']*x['count']] for x in order_items]

    weixin_items = {
        '销量': [int(x['count']) for x in items],
    }
    x_axis = [x['pay_time'].strftime('%Y-%m-%d') for x in items if x['pay_time'] is not None]

    charts = []
    charts.append(generate_chart(product.name, x_axis, weixin_items, width='1000px'))

    return render(req, 'yunying/product/show.html', locals())
