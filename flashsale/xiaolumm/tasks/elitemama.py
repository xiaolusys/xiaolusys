# coding: utf8
from __future__ import absolute_import, unicode_literals

from shopmanager import celery_app as app

import datetime
from collections import defaultdict
from django.db.models import Sum, Min, Max, Count, F, Q, FloatField

from flashsale.coupon.models import CouponTransferRecord
from ..models import EliteMamaStatus, ReferalRelationship, XiaoluMama


import logging
logger = logging.getLogger(__name__)

@app.task()
def task_fresh_elitemama_active_status():

    base_qs = CouponTransferRecord.objects.filter(
        # Q(coupon_from_mama_id=2219502)|Q(coupon_to_mama_id=2219502),
        transfer_status=CouponTransferRecord.DELIVERED,
        status=CouponTransferRecord.EFFECT,
    )
    # 进货金额
    out_data_set = base_qs.values('coupon_from_mama_id','transfer_type').annotate(
        record_amount=Sum(F('coupon_value') * F('coupon_num'), output_field=FloatField())
    )

    in_data_set = base_qs.values('coupon_to_mama_id', 'transfer_type').annotate(
        record_amount=Sum(F('coupon_value') * F('coupon_num'), output_field=FloatField())
    )

    elite_mamas = defaultdict(dict)
    for agg in in_data_set:
        agg_dict = {}
        if agg['transfer_type'] == CouponTransferRecord.IN_BUY_COUPON:
            agg_dict['purchase_amount_in'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_TRANSFER:
            agg_dict['transfer_amount_in'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.IN_RETURN_COUPON:
            agg_dict['return_amount_in'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.IN_RETURN_GOODS:
            agg_dict['refund_coupon_in'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_CONSUMED:
            agg_dict['sale_amount_in'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_CASHOUT:
            agg_dict['refund_amount_in'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_EXCHG_SALEORDER:
            agg_dict['exchg_amount_in'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.IN_GIFT_COUPON:
            agg_dict['gift_amount_in'] = agg['record_amount']
        elite_mamas[agg['coupon_to_mama_id']].update(agg_dict)

    for agg in out_data_set:
        agg_dict = {}
        if agg['transfer_type'] == CouponTransferRecord.IN_BUY_COUPON:
            agg_dict['purchase_amount_out'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_TRANSFER:
            agg_dict['transfer_amount_out'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.IN_RETURN_COUPON:
            agg_dict['return_amount_out'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.IN_RETURN_GOODS:
            agg_dict['refund_coupon_in'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_CONSUMED:
            agg_dict['sale_amount_out'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_CASHOUT:
            agg_dict['refund_amount_out'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.OUT_EXCHG_SALEORDER:
            agg_dict['exchg_amount_out'] = agg['record_amount']
        if agg['transfer_type'] == CouponTransferRecord.IN_GIFT_COUPON:
            agg_dict['gift_amount_out'] = agg['record_amount']
        elite_mamas[agg['coupon_from_mama_id']].update(agg_dict)

    print 'elite mama total:', len(elite_mamas)

    min_join_records = CouponTransferRecord.objects.filter(date_field__isnull=False)\
        .values('coupon_from_mama_id').annotate(joined_date=Min('date_field'))\
        .values_list('coupon_from_mama_id','joined_date')
    mama_joined_date_maps = dict(min_join_records)

    max_active_records = CouponTransferRecord.objects.filter(date_field__isnull=False) \
        .values('coupon_from_mama_id').annotate(last_active_time=Max('date_field')) \
        .values_list('coupon_from_mama_id', 'last_active_time')
    mama_active_date_maps = dict(max_active_records)

    referal_maps = dict(ReferalRelationship.objects.filter(
        referal_from_mama_id__in=mama_joined_date_maps.keys(),
        referal_type__gte=XiaoluMama.ELITE)\
        .values('referal_from_mama_id').annotate(sub_mamacount=Count('referal_to_mama_id'))\
        .values_list('referal_from_mama_id', 'sub_mamacount'))

    cnt = 0
    for mama_id, data in elite_mamas.iteritems():
        elite_active, state = EliteMamaStatus.objects.get_or_create(mama_id=mama_id)
        for key, value in data.iteritems():
            setattr(elite_active, key, value)
        
        if state or not elite_active.joined_date:
            elite_active.joined_date = mama_joined_date_maps.get(mama_id) or datetime.date.today()

        if mama_id in mama_active_date_maps:
            elite_active.last_active_time = mama_active_date_maps.get(mama_id)

        elite_active.sub_mamacount = referal_maps.get(mama_id) or 0
        elite_active.save()

        cnt += 1
        if cnt % 100 == 0:
            print 'update count:', cnt

    print 'finish count:', cnt


def double_mama_score():
    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
    from_time = datetime.datetime(2017, 2, 8, 23, 0, 0, 0)
    to_time = datetime.datetime(2017, 2, 8, 23, 30, 0, 0)
    has_add = CouponTransferRecord.objects.filter(
        transfer_status=CouponTransferRecord.DELIVERED,
        transfer_type__in=[CouponTransferRecord.IN_GIFT_COUPON],
        created__range=(from_time, to_time)
    )

    has_add_mms = [p['coupon_to_mama_id'] for p in has_add.values('coupon_to_mama_id')]

    from flashsale.xiaolumm.models import XiaoluMama
    mamas = XiaoluMama.objects.filter(referal_from__in=[XiaoluMama.DIRECT, XiaoluMama.INDIRECT], status=XiaoluMama.EFFECT,
                                      charge_status=XiaoluMama.CHARGED, elite_score__gt=0)
    for mama in mamas:
        origin_score = mama.elite_score
        score = mama.elite_score
        if mama.id in has_add_mms:
            gift_ct = CouponTransferRecord.objects.filter(
                coupon_to_mama_id=mama.id,
                transfer_status=CouponTransferRecord.DELIVERED,
                transfer_type__in=[CouponTransferRecord.IN_GIFT_COUPON],
                created__range=(from_time, to_time)
            ).first()
            if mama.elite_score >= 600 and mama.elite_score < 2000:
                score = 600 - gift_ct.elite_score + 300
            elif mama.elite_score >= 2000 and mama.elite_score < 6000:
                score = 2000 - gift_ct.elite_score + 1000
            elif mama.elite_score >= 6000 and mama.elite_score < 20000:
                score = 6000 - gift_ct.elite_score + 3000
            elif mama.elite_score >= 20000:
                score = 20000 - gift_ct.elite_score + 10000
        else:
            if score >= 600 and score < 1000:
                score += 300
            elif score >= 2000 and score < 3000:
                score += 1000
            elif score >= 6000 and score < 10000:
                score += 3000

        if mama.elite_score != score:
            mama.elite_score = score
            mama.save()
            from core.options import log_action, CHANGE, ADDITION, get_systemoa_user
            sys_oa = get_systemoa_user()
            log_action(sys_oa, mama, CHANGE, u'0208升级分数翻倍修改用户积分从%s到%s' % (origin_score, score))

        try:
            from flashsale.coupon.apis.v1.transfer import create_present_elite_score
            from flashsale.coupon.apis.v1.coupontemplate import get_coupon_template_by_id
            from flashsale.pay.apis.v1.customer import get_customer_by_id

            if score > origin_score:
                template = get_coupon_template_by_id(id=156)
                customer = get_customer_by_id(mama.customer_id)
                transfer_in = create_present_elite_score(customer, int(score - origin_score), template, 1)
                log_action(sys_oa, transfer_in, ADDITION, '0208升级分数翻倍赠送积分: 赠送')
                # log_action(sys_oa, transfer_out, ADDITION, '0208升级分数翻倍赠送积分: 消耗')
        except Exception as e:
            pass
