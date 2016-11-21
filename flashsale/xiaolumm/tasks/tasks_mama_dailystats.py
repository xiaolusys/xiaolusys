# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import sys
import datetime
from django.db import IntegrityError
from django.db.models import F, Sum

from flashsale.xiaolumm import util_unikey
from flashsale.xiaolumm.models.models_fortune import DailyStats, UniqueVisitor, OrderCarry, CarryRecord

import logging
logger = logging.getLogger('celery.handler')



def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


def create_dailystats_with_integrity(mama_id, date_field, uni_key, **kwargs):
    stats = DailyStats(mama_id=mama_id, date_field=date_field, uni_key=uni_key, **kwargs)
    stats.save()

    # try:
    #    stats = DailyStats(mama_id=mama_id, date_field=date_field, uni_key=uni_key, **kwargs)
    #    stats.save()
    # except IntegrityError as e:
    #    logger.warn("IntegrityError - DailyStats | mama_id: %s, uni_key: %s, params: %s" % (mama_id, uni_key, kwargs))
    # The following will very likely cause deadlock, since another
    # thread is creating this record. we decide to just fail it.
    # DailyStats.objects.filter(mama_id=mama_id, date_field=date_field, uni_key=uni_key).update(**kwargs)


@app.task()
def task_confirm_previous_dailystats(mama_id, today_date_field, num_days):
    # print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    end_date_field = today_date_field - datetime.timedelta(days=num_days)
    records = DailyStats.objects.filter(mama_id=mama_id, date_field__lte=end_date_field, status=1).order_by(
        '-date_field')[:7]
    if records.count() <= 0:
        return

    for stats in records:
        date_field = stats.date_field
        today_visitor_num = UniqueVisitor.objects.filter(mama_id=mama_id, date_field=date_field).count()
        stats.today_visitor_num = today_visitor_num

        today_order_num = OrderCarry.objects.filter(mama_id=mama_id, date_field=date_field).count()
        stats.today_order_num = today_order_num

        carrys = CarryRecord.objects.filter(mama_id=mama_id, date_field=date_field).exclude(status=3).values(
            'date_field').annotate(carry=Sum('carry_num'))
        today_carry_num = 0
        if len(carrys) > 0:
            if carrys[0]["date_field"] == date_field:
                today_carry_num = carrys[0]["carry"]

        stats.today_carry_num = today_carry_num
        stats.status = 2  # confirm
        stats.save()


@app.task(max_retries=3, default_retry_delay=6)
def task_visitor_increment_dailystats(mama_id, date_field):
    # print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    uni_key = util_unikey.gen_dailystats_unikey(mama_id, date_field)
    #if len(uni_key) > 16:
    #    logger.error("%s: create dailystats error: uni_key wrong %s" % (get_cur_info(), uni_key))

    records = DailyStats.objects.filter(uni_key=uni_key)

    if records.count() <= 0:
        try:
            create_dailystats_with_integrity(mama_id, date_field, uni_key, today_visitor_num=1)
        except IntegrityError as exc:
            #logger.error(
            #    "IntegrityError - DailyStats | %s, mama_id: %s, uni_key: %s, today_visitor_num=1" % (get_cur_info(), mama_id, uni_key))
            raise task_visitor_increment_dailystats.retry(exc=exc)
    else:
        records.update(today_visitor_num=F('today_visitor_num') + 1)


@app.task(max_retries=3, default_retry_delay=6)
def task_carryrecord_update_dailystats(mama_id, date_field):
    # print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    uni_key = util_unikey.gen_dailystats_unikey(mama_id, date_field)
    #if len(uni_key) > 16:
    #    logger.error("%s: create dailystats error: uni_key wrong %s" % (get_cur_info(), uni_key))

    records = DailyStats.objects.filter(uni_key=uni_key)
    carrys = CarryRecord.objects.filter(mama_id=mama_id, date_field=date_field).exclude(status=3).values(
        'date_field').annotate(carry=Sum('carry_num'))

    today_carry_num = 0
    if len(carrys) > 0:
        if carrys[0]["date_field"] == date_field:
            today_carry_num = carrys[0]["carry"]

    if records.count() <= 0:
        try:
            create_dailystats_with_integrity(mama_id, date_field, uni_key, today_carry_num=today_carry_num)
        except IntegrityError as exc:
            #logger.error("IntegrityError - DailyStats | %s, mama_id: %s, uni_key: %s, today_carry_num=%s" % (get_cur_info(), mama_id, uni_key, today_carry_num))
            raise task_carryrecord_update_dailystats.retry(exc=exc)
    else:
        records.update(today_carry_num=today_carry_num)


@app.task(max_retries=3, default_retry_delay=6)
def task_ordercarry_increment_dailystats(mama_id, date_field):
    # print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    uni_key = util_unikey.gen_dailystats_unikey(mama_id, date_field)
    #if len(uni_key) > 16:
    #    logger.error("%s: create dailystats error: uni_key wrong %s" % (get_cur_info(), uni_key))

    records = DailyStats.objects.filter(uni_key=uni_key)

    if records.count() <= 0:
        try:
            create_dailystats_with_integrity(mama_id, date_field, uni_key, today_order_num=1)
        except IntegrityError as exc:
            #logger.error(
            #    "IntegrityError - DailyStats | %s, mama_id: %s, uni_key: %s, today_order_num=1" % (get_cur_info(), mama_id, uni_key))
            raise task_ordercarry_increment_dailystats.retry(exc=exc)
    else:
        records.update(today_order_num=F('today_order_num') + 1)


@app.task()
def task_xlmm_score():
    from flashsale.xiaolumm.models.score import XlmmEffectScore, XlmmTeamEffScore
    XlmmEffectScore.batch_generate()
    XlmmTeamEffScore.batch_generate()


@app.task()
def task_calc_all_xlmm_elite_score():
    from flashsale.xiaolumm.models.models import XiaoluMama
    elite_mamas = XiaoluMama.objects.filter(status=XiaoluMama.EFFECT, charge_status=XiaoluMama.CHARGED)
    for mama in elite_mamas:
        is_elite = (mama.referal_from == XiaoluMama.DIRECT) or (mama.referal_from == XiaoluMama.INDIRECT)
        if is_elite:
            task_calc_xlmm_elite_score.delay(mama.id)


@app.task()
def task_calc_xlmm_elite_score(mama_id):
    from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
    res = CouponTransferRecord.objects.filter(coupon_from_mama_id=mama_id, transfer_status=CouponTransferRecord.DELIVERED, transfer_type=CouponTransferRecord.OUT_CASHOUT).aggregate(
        n=Sum('elite_score'))
    out_score = res['n'] or 0

    res = CouponTransferRecord.objects.filter(coupon_to_mama_id=mama_id, transfer_status=CouponTransferRecord.DELIVERED, transfer_type=CouponTransferRecord.IN_BUY_COUPON).aggregate(
        n=Sum('elite_score'))
    in_buy_score = res['n'] or 0

    res = CouponTransferRecord.objects.filter(coupon_to_mama_id=mama_id, transfer_status=CouponTransferRecord.DELIVERED,
                                              transfer_type=CouponTransferRecord.OUT_TRANSFER).aggregate(
        n=Sum('elite_score'))
    in_trans_score = res['n'] or 0

    score = in_buy_score + in_trans_score - out_score
    from flashsale.xiaolumm.models.models import XiaoluMama
    XiaoluMama.objects.filter(id=mama_id).update(elite_score=score)
