# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import collections
from itertools import chain
from django.db.models import Sum, F

from shopmanager import celery_app as app

from core.utils.timeutils import day_range
from ..models import DailySkuDeliveryStat, DailySkuAmountStat
from flashsale.pay.models import SaleOrder, SaleTrade
from flashsale.coupon.models import UserCoupon, CouponTemplate
from shopback.items.models import ProductSku

@app.task
def task_call_all_sku_delivery_stats(stat_date=None):
    """ 统计所有订单规格sku发货天数 """
    if not stat_date:
        stat_date = datetime.date.today() - datetime.timedelta(days=1)

    post_values = SaleOrder.objects.filter(consign_time__range=day_range(stat_date))\
        .extra(select={'days': 'TIMESTAMPDIFF(DAY, pay_time, consign_time)'})\
        .values('sku_id', 'days').annotate(Sum('num'))

    wait_values = SaleOrder.objects.filter(
        status=SaleOrder.WAIT_SELLER_SEND_GOODS,
    ).extra(select={'days': 'TIMESTAMPDIFF(DAY, pay_time, NOW())'}) \
        .values('sku_id', 'days').annotate(Sum('num'))

    sku_ids  = chain([l['sku_id'] for l in post_values], [l['sku_id'] for l in wait_values])
    sku_maps = dict(ProductSku.objects.filter(id__in=list(sku_ids)).values_list('id', 'product__model_id'))

    for value in post_values:
        stat, state = DailySkuDeliveryStat.objects.get_or_create(
            sku_id=value['sku_id'], stat_date=stat_date, days=value['days'])
        stat.post_num = value['num__sum']
        stat.model_id = sku_maps.get(int(value['sku_id']))
        stat.save()

    for value in wait_values:
        stat, state = DailySkuDeliveryStat.objects.get_or_create(
            sku_id=value['sku_id'], stat_date=stat_date, days=value['days'])
        stat.wait_num = value['num__sum']
        stat.model_id = sku_maps.get(int(value['sku_id']))
        stat.save()


def task_calc_all_sku_amount_stat_by_date(stat_date=None):
    """ 统计sku销售金额 """

    if not stat_date:
        stat_date = datetime.date.today() - datetime.timedelta(days=1)

    order_qs = SaleOrder.objects.active_orders().filter(
        pay_time__range=day_range(stat_date),
        # oid__in=('xo170210589d11ac3fc93','xo170210589da3cab0e72'), # TODO@REMOVE
    )

    order_stats = order_qs.values('sku_id').annotate(
        total_amount=Sum(F('total_fee') * 100),
        direct_payment=Sum(F('payment') * 100),
        coupon_amount=Sum(F('discount_fee') * 100),
    )

    sku_ids = [l['sku_id'] for l in order_stats]
    sku_model_maps = dict(ProductSku.objects.filter(id__in=list(sku_ids)).values_list('id', 'product__model_id'))

    sku_tid_num_list = order_qs.values_list('sku_id', 'sale_trade__tid', 'num', 'oid')
    tid_list = []
    tid_num_maps = collections.defaultdict(dict)
    sku_tid_maps = {}
    for st in sku_tid_num_list:
        sku_id = int(st[0])
        tid = st[1]
        model_id = sku_model_maps.get(sku_id)
        tid_list.append(tid)
        tid_num_maps[tid][model_id] = (tid_num_maps[tid].get(model_id) or 0) + st[2]
        sku_tid_maps[sku_id] = tid

    tmp_pro_maps = CouponTemplate.objects.get_template_to_modelproduct_maps()
    boutique_coupon_qs = UserCoupon.objects.get_origin_payment_boutique_coupons()
    usercoupon_values = boutique_coupon_qs.filter(trade_tid__in=tid_list)\
        .values_list('template_id', 'trade_tid', 'extras')
    # TODO@TIPS 统计妈妈购买优惠券实际支付金额
    tid_origin_price_maps = {}
    tid_template_model_masp = {}
    for template_id, tid, extras in usercoupon_values:
        tid_origin_price_maps[tid] = tid_origin_price_maps.get(tid, 0) + (extras.get('origin_price') or 0)
        tid_template_model_masp[tid] = tmp_pro_maps.get(template_id)

    sku_origin_price_maps = {}
    for st in sku_tid_num_list:
        sku_id, tid, sku_num = int(st[0]), st[1], st[2]
        model_id = sku_model_maps.get(sku_id)
        sku_sum  = tid_num_maps[tid].get(model_id, 0)
        if sku_sum == 0:
            continue
        sku_origin_price_maps[sku_id] = sku_origin_price_maps.get(sku_id, 0) \
            + (sku_num * 1.0 / sku_sum) * tid_origin_price_maps.get(tid, 0)

    # TODO@TIPS 统计妈妈兑换优惠券兑出差额 = 兑出金额 - 购券金额, (兑换金额必须根据订单实际支付金额计算)
    order_exchg_maps = {}
    order_value_list = order_qs.values('oid', 'num', 'payment')
    order_num_payment_maps = dict([(ol['oid'], ol) for ol in order_value_list])
    exchg_coupon_values = boutique_coupon_qs.filter(trade_tid__in=order_num_payment_maps.keys())\
        .values_list('trade_tid', 'value', 'extras')
    for oid, value, extras in exchg_coupon_values:
        order_value = order_num_payment_maps.get(oid)
        order_per_payment = order_value.get('num') > 0  and order_value.get('payment') * 100 / order_value.get('num') or 0
        order_exchg_maps[oid] = order_exchg_maps.get(oid, 0) + (order_per_payment - extras.get('origin_price', 0))

    sku_exchg_maps = {}
    for st in sku_tid_num_list:
        sku_id, oid = int(st[0]), st[3]
        sku_exchg_maps[sku_id] = sku_exchg_maps.get(sku_id, 0) + order_exchg_maps.get(oid, 0)

    for value in order_stats:
        sku_id = int(value['sku_id'])
        stat, state = DailySkuAmountStat.objects.get_or_create(
            sku_id=sku_id, stat_date=stat_date
        )
        value['model_id'] = sku_model_maps.get(sku_id)
        value['coupon_payment'] = sku_origin_price_maps.get(sku_id, 0)
        value['exchg_amount']   = sku_exchg_maps.get(sku_id, 0)

        for k, v in value.items():
            setattr(stat, k, v)

        stat.save()

@app.task
def task_calc_all_sku_amount_stat_by_schedule():
    """ 统计sku销售金额 """
    # calc the last day sku_amount
    task_calc_all_sku_amount_stat_by_date(datetime.date.today() - datetime.timedelta(days=1))

    # calc the fifth days ago sku_amount
    task_calc_all_sku_amount_stat_by_date(datetime.date.today() - datetime.timedelta(days=15))




