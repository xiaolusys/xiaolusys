# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
from django.db.models import Sum, F

from shopmanager import celery_app as app

from flashsale.pay.models import SaleOrder, SaleRefund, ModelProduct
from flashsale.coupon.models import CouponTemplate, UserCoupon
from shopback.items.models import ProductSku, Product, SkuStock
from ..models import DailyBoutiqueStat

@app.task
def task_boutique_sale_and_refund_stats(stat_date, modelproduct_id):

    stat_datetime_start = datetime.datetime.combine(stat_date, datetime.time.min)
    stat_datetime_end   = datetime.datetime.combine(stat_date, datetime.time.max)

    sku_stats = []
    stat_params = {
        'model_stock_num': 0,
        'model_sale_num': 0,
        'model_refund_num': 0,
        'coupon_sale_num': 0,
        'coupon_use_num': 0,
        'coupon_refund_num': 0,
        'sku_stats': sku_stats
    }


    mp = ModelProduct.objects.get(id=modelproduct_id)
    product_ids = list(Product.objects.filter(model_id=mp.id).values_list('id', flat=True))
    sku_ids = list(ProductSku.objects.filter(product_id__in=product_ids).values_list('id', flat=True))

    order_stats = dict(SaleOrder.objects.filter(
        sku_id__in=sku_ids,
        pay_time__range=(stat_datetime_start, stat_datetime_end)
    ).exclude(status=SaleOrder.TRADE_CLOSED_BY_SYS).values('sku_id').
                       annotate(Sum('num')).values_list('sku_id', 'num__sum'))

    stock_values = SkuStock.objects.filter(
        sku_id__in=sku_ids
    ).values_list('sku_id','history_quantity', 'inbound_quantity', 'adjust_quantity', 'return_quantity', 'post_num', 'rg_quantity')
    stock_stats = dict([(s[0], sum(s[1:-2]) - s[-2] - s[-1]) for s in stock_values])

    refund_stats = dict(SaleRefund.objects.filter(
        sku_id__in=sku_ids,
        success_time__range=(stat_datetime_start, stat_datetime_end)
    ).values('sku_id').annotate(Sum('refund_num')).values_list('sku_id', 'refund_num__sum'))

    for sku_id in sku_ids:
        sku_stat = {
            'sku_id': sku_id,
            'sku_stock_num': max(stock_stats.get(sku_id) or 0, 0),
            'sku_sale_num': max(order_stats.get(sku_id) or 0, 0),
            'sku_refund_num': max(refund_stats.get(sku_id) or 0, 0)
        }
        stat_params['model_stock_num'] += sku_stat['sku_stock_num']
        stat_params['model_sale_num'] += sku_stat['sku_sale_num']
        stat_params['model_refund_num'] += sku_stat['sku_refund_num']
        sku_stats.append(sku_stat)

    coupon_values = CouponTemplate.objects.filter(coupon_type=CouponTemplate.TYPE_TRANSFER)\
        .exclude(status=CouponTemplate.CREATE).values('has_released_count', 'has_used_count', 'extras')

    for v in coupon_values:
        model_id = v['extras']['scopes'].get('modelproduct_ids')
        if model_id and int(model_id) == modelproduct_id:
            stat_params['coupon_sale_num'] = v['has_released_count']
            stat_params['coupon_use_num']  = v['has_used_count']

    boutique_stat, state= DailyBoutiqueStat.objects.get_or_create(
        model_id=modelproduct_id, stat_date=stat_date)
    for k, v in stat_params.iteritems():
        if not state and k == 'model_stock_num':
            continue

        if not state and k == 'sku_stats':
            old_sku_stock_num = boutique_stat.sku_stats['sku_stock_num']
            stat_params['sku_stock_num'] = old_sku_stock_num

        setattr(boutique_stat, k, v)
    boutique_stat.save()


@app.task
def task_all_boutique_stats():
    """ 批量精品汇商品每日数据统计 """
    boutique_products = ModelProduct.objects.filter(
        is_boutique=True,
        status=ModelProduct.NORMAL,
        product_type=ModelProduct.USUAL_TYPE
    )
    yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
    for mp in boutique_products.iterator():
        task_boutique_sale_and_refund_stats.delay(yesterday, mp.id)





