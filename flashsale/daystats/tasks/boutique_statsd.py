# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
from django_statsd.clients import statsd
from django.db.models import Sum, F, Count

from shopmanager import celery_app as app

from flashsale.coupon.models import CouponTransferRecord, TransferCouponDetail
from flashsale.xiaolumm.models import OrderCarry


@app.task
def task_transfer_coupon_order_statsd():
    ctr_qs = CouponTransferRecord.objects.filter(status=1)

    values = ctr_qs.filter(transfer_status=3, transfer_type=4
    ).aggregate(
        total_coupon_num=Sum('coupon_num'),
        total_coupon_value=Sum(F('coupon_num') * F('coupon_value'))
    )
    coupon_sale_num = values.get('total_coupon_num')
    coupon_sale_amount = values.get('total_coupon_value')

    values = ctr_qs.filter(transfer_status=3, transfer_type__in=(3, 8)
    ).aggregate(
        total_coupon_used_num=Sum('coupon_num'),
        total_coupon_used_value=Sum(F('coupon_num') * F('coupon_value'))
    )
    coupon_used_num = values.get('total_coupon_used_num')
    coupon_used_amount = values.get('total_coupon_used_value')

    transfer_details = ctr_qs.filter(
        transfer_type=CouponTransferRecord.OUT_TRANSFER
    ).aggregate(
        transfer_count=Count('id'),
        transfer_nums=Sum('coupon_num'),
        transfer_amounts=Sum(F('coupon_num') * F('coupon_value')),
    )

    refund_return_num = ctr_qs.filter(transfer_type=CouponTransferRecord.OUT_CASHOUT).aggregate(
        transfer_amounts=Sum(F('coupon_num') * F('coupon_value'))).get('transfer_amounts') or 0

    exchg_order_num = ctr_qs.filter(transfer_type=CouponTransferRecord.OUT_EXCHG_SALEORDER).aggregate(
        exchg_amounts=Sum(F('coupon_num') * F('coupon_value'))).get('exchg_amounts') or 0

    dt_str = datetime.datetime.now().strftime('%Y.%m.%d')
    statsd.gauge('xiaolumm.boutique.coupon.sale_num.%s'%dt_str, coupon_sale_num)
    statsd.gauge('xiaolumm.boutique.coupon.sale_amount.%s'% dt_str, coupon_sale_amount)
    statsd.gauge('xiaolumm.boutique.coupon.used_num.%s'% dt_str, coupon_used_num)
    statsd.gauge('xiaolumm.boutique.coupon.used_amount.%s'% dt_str, coupon_used_amount)
    statsd.gauge('xiaolumm.boutique.coupon.refund_over_amount.%s'% dt_str, refund_return_num)
    statsd.gauge('xiaolumm.boutique.coupon.exchg_order_amount.%s'% dt_str, exchg_order_num)

    statsd.gauge('xiaolumm.boutique.coupon.transfer_count.%s' % dt_str, transfer_details.get('transfer_count') or 0)
    statsd.gauge('xiaolumm.boutique.coupon.transfer_nums.%s' % dt_str, transfer_details.get('transfer_nums') or 0)
    statsd.gauge('xiaolumm.boutique.coupon.transfer_amounts.%s' % dt_str, transfer_details.get('transfer_amounts') or 0)


@app.task
def task_boutique_mama_statsd():
    ctr_qs = CouponTransferRecord.objects.filter(status=1)

    dt = datetime.datetime.now()
    elite_mama_count = ctr_qs.filter(
        transfer_status=CouponTransferRecord.DELIVERED
    ).values('coupon_to_mama_id').distinct().count()

    active_elite_mama_count = ctr_qs.filter(
        date_field=dt.date(),
        transfer_status=CouponTransferRecord.DELIVERED
    ).values('coupon_to_mama_id').distinct().count()

    order_mama_count = OrderCarry.objects.filter(
        date_field=dt.date(),
        status__in=(1, 2, 3),
        carry_type__in=(1, 2),
        mama_id__gt=0
    ).values_list('mama_id', flat=True).distinct().count()

    dt_str = dt.strftime('%Y.%m.%d')
    statsd.gauge('xiaolumm.boutique.mama.elite_count.%s'% dt_str, elite_mama_count)
    statsd.gauge('xiaolumm.boutique.mama.active_count.%s'% dt_str, active_elite_mama_count)
    statsd.gauge('xiaolumm.boutique.mama.ordered_count.%s'% dt_str, order_mama_count)









