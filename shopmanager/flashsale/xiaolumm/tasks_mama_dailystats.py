# -*- encoding:utf-8 -*-

import datetime
import logging

from celery.task import task
from django.db import IntegrityError
from django.db.models import F, Sum

from flashsale.xiaolumm import util_unikey
from flashsale.xiaolumm.models.models_fortune import DailyStats, UniqueVisitor, OrderCarry, CarryRecord

logger = logging.getLogger('celery.handler')

import sys


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


@task()
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


@task(max_retries=3, default_retry_delay=6)
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


@task(max_retries=3, default_retry_delay=6)
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


@task(max_retries=3, default_retry_delay=6)
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
