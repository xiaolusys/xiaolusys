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
    get_date_from_req,
)
from shopback.items.models import Product
from flashsale.pay.models.product import ModelProduct
from supplychain.supplier.models.category import SaleCategory


def get_children_cids(cid=None):
    cids = []
    categories = SaleCategory.objects.filter(parent_cid=cid)
    for item in categories:
        scids = get_children_cids(cid=item.cid)
        if scids:
            cids += scids
        cids.append(item.cid)
    return cids


def index(req):
    p_start_date, p_end_date, start_date, end_date = get_date_from_req(req)
    cid = req.GET.get('category') or None

    sql = """
        select item_id, title, count(*) as count
        from xiaoludb.flashsale_order
        where pay_time >= %s and pay_time < %s
        group by item_id
        order by count desc
        limit 1000
    """
    sql = """
        SELECT
            flashsale_order.item_id as item_id,
            flashsale_order.total_fee,
            flashsale_order.title as title,
            flashsale_order.pay_time,
            supplychain_sale_category.cid as cid,
            supplychain_sale_category.name as category_name,
            count(*) as count
        FROM xiaoludb.flashsale_order
        join xiaoludb.shop_items_product on shop_items_product.id=flashsale_order.item_id
        join xiaoludb.flashsale_modelproduct on shop_items_product.model_id=flashsale_modelproduct.id
        join xiaoludb.supplychain_sale_category on flashsale_modelproduct.salecategory_id=supplychain_sale_category.id
        where flashsale_order.pay_time >= %s
            and flashsale_order.pay_time < %s
    """
    if cid:
        cid = get_children_cids(cid=cid)
        cid = ', '.join(map(lambda x: '"%s"' % x, cid))
        print cid
        sql += 'and supplychain_sale_category.cid in (%s)' % cid

    sql += """
        group by flashsale_order.item_id
        order by count desc
        limit 1000
    """
    products = execute_sql(get_cursor(), sql, [format_datetime(start_date), format_datetime(end_date)])

    # def byfunc(item):
    #     category = get_root_category(item['cid'])
    #     item['category_name'] = category.name
    #     return category.name

    # products = map(byfunc, products)
    categories = SaleCategory.objects.filter(is_parent=True)

    return render(req, 'yunying/product/index.html', locals())


category_cache = {}


def get_root_category(cid):
    if category_cache.get(cid):
        category = category_cache.get(cid)
    else:
        category = SaleCategory.objects.filter(cid=cid).first()
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
    p_start_date, p_end_date, start_date, end_date = get_date_from_req(req)

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
    p_start_date, p_end_date, start_date, end_date = get_date_from_req(req)

    product = Product.objects.get(id=id)
    modelproduct = product.get_product_model()
    if modelproduct:
        saleproduct = modelproduct.saleproduct

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
