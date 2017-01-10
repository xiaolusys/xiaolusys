# coding: utf8
from __future__ import absolute_import, unicode_literals

from shopmanager import celery_app as app

from collections import defaultdict
from django.db.models import Sum, Min, Count, F

from flashsale.coupon.models import CouponTransferRecord
from ..models import EliteMamaStatus, ReferalRelationship, XiaoluMama


import logging
logger = logging.getLogger('celery.handler')

@app.task()
def task_fresh_elitemama_active_status():

    elite_aggrates = CouponTransferRecord.objects.filter(status=CouponTransferRecord.EFFECT)\
        .values('coupon_from_mama_id', 'transfer_type')\
        .annotate(
            record_amount=Sum(F('coupon_value') * F('coupon_num'))
        )

    elite_mamas = defaultdict(dict)
    for agg in elite_aggrates:
        agg_dict = {}
        if agg['transfer_type'] == CouponTransferRecord.IN_BUY_COUPON:
            agg_dict['purchase_amount'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_TRANSFER:
            agg_dict['transfer_amount'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.IN_RETURN_COUPON:
            agg_dict['return_amount'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_CONSUMED:
            agg_dict['sale_amount'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_CASHOUT:
            agg_dict['refund_amount'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_EXCHG_SALEORDER:
            agg_dict['exchg_amount'] = agg['record_amount']
        elite_mamas[agg['coupon_from_mama_id']].update(agg_dict)

    print 'elite mama total:', len(elite_mamas), elite_mamas

    min_join_records = CouponTransferRecord.objects\
        .values('coupon_from_mama_id').annotate(joined_date=Min('date_field'))\
        .values_list('coupon_from_mama_id','joined_date')
    mama_joined_date_maps = dict(min_join_records)

    referal_maps = dict(ReferalRelationship.objects.filter(
        referal_from_mama_id__in=mama_joined_date_maps.keys(),
        referal_type=XiaoluMama.ELITE)\
        .values('referal_from_mama_id').annotate(sub_mamacount=Count('referal_to_mama_id'))\
        .values_list('referal_from_mama_id', 'sub_mamacount'))

    cnt = 0
    for mama_id, data in elite_mamas.iteritems():
        elite_active, state = EliteMamaStatus.objects.get_or_create(mama_id=mama_id)
        for key, value in data.iteritems():
            setattr(elite_active, key, value)
        print elite_active, mama_id, data
        if state or not elite_active.joined_date:
            elite_active.joined_date = mama_joined_date_maps.get(mama_id)

        elite_active.sub_mamacount = referal_maps.get(mama_id) or 0
        elite_active.save()

        cnt += 1
        if cnt % 100 == 0:
            print 'update count:', cnt

    print 'finish count:', cnt