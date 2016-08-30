# encoding=utf8
from datetime import datetime, timedelta
from django.shortcuts import render
from django.db import connections

from flashsale.daystats.lib.db import execute_sql, get_cursor
from flashsale.daystats.lib.chart import (
    generate_chart,
    generate_date,
    generate_chart_data,
)
from flashsale.daystats.lib.util import (
    process_data,
    groupby,
    process,
    format_datetime,
)
from shopback.items.models import Product
from flashsale.pay.models.product import ModelProduct
from supplychain.supplier.models.category import SaleCategory


def index(req):
    now = datetime.now()
    last = now - timedelta(days=7)
    p_start_date = req.GET.get('start_date', '%s-%s-%s' % (last.year, last.month, last.day))
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


category_cache = {}


def get_root_category(cid):
    if category_cache.get(cid):
        category = category_cache.get(cid)
    else:
        category = SaleCategory.objects.using('product').filter(cid=cid).first()
        if category:
            category_cache[cid] = category
        else:
            category_cache[cid] = 'UNKNOWN'
            return 'UNKNOWN'
    if category.is_parent:
        return category
    else:
        return get_root_category(category.parent_cid)


def salecategory(req):
    now = datetime.now()
    last = now - timedelta(days=7)
    p_start_date = req.GET.get('start_date', '%s-%s-%s' % (last.year, last.month, last.day))
    p_end_date = req.GET.get('end_date', '%s-%s-%s' % (now.year, now.month, now.day+1))

    start_date = datetime.strptime(p_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(p_end_date, '%Y-%m-%d')

    cursor = get_cursor()

    sql = """
        SELECT
            flashsale_order.item_id,
            flashsale_order.total_fee,
            flashsale_order.title,
            flashsale_order.pay_time,
            supplychain_sale_category.cid,
            supplychain_sale_category.name
        FROM xiaoludb.flashsale_order
        join xiaoludb.shop_items_product on shop_items_product.id=flashsale_order.item_id
        join xiaoludb.flashsale_modelproduct on shop_items_product.model_id=flashsale_modelproduct.id
        join xiaoludb.supplychain_sale_category on flashsale_modelproduct.salecategory_id=supplychain_sale_category.id
        where flashsale_order.pay_time >= %s and flashsale_order.pay_time < %s
    """
    products = execute_sql(cursor, sql, [format_datetime(start_date), format_datetime(end_date)])

    def byfunc(item):
        # return item['name']
        category = get_root_category(item['cid'])
        return category.name

    def pfunc(items):
        return int(sum([x['total_fee'] for x in items]))

    pie_products = groupby(products, byfunc)
    pie_products = process(pie_products, pfunc)
    piechart = dict(pie_products)

    x_axis, chart_items = generate_chart_data(
        products, xaris='pay_time', key=byfunc, yaris=pfunc, start_date=start_date, end_date=end_date)
    charts = [generate_chart('商品类目销售额', x_axis, chart_items, width='1000px')]

    return render(req, 'yunying/product/category.html', locals())


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
