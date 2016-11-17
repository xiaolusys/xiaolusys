# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import datetime
import sys

from django.db.models import F
from flashsale.xiaolumm import util_description, util_unikey
from flashsale.xiaolumm.models.models_fortune import ActiveValue, OrderCarry, UniqueVisitor


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@app.task()
def task_fans_update_activevalue(mama_id, fans_customer_id, date_field):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    value_type = 4  # fans
    status = 2  # confirmed
    contributor_id = fans_customer_id
    order_id = ""
    value_num = ActiveValue.VALUE_MAP[str(value_type)]
    uni_key = util_unikey.gen_activevalue_unikey(value_type, mama_id, date_field, order_id, contributor_id)

    description = util_description.gen_activevalue_description(value_type)
    active_value = ActiveValue(mama_id=mama_id, value_num=value_num, value_type=value_type,
                               value_description=description,
                               uni_key=uni_key, date_field=date_field, status=status)
    active_value.save()


@app.task()
def task_ordercarry_update_activevalue(order_carry_unikey):
    value_type = 2
    order_carrys = OrderCarry.objects.filter(uni_key=order_carry_unikey)
    if order_carrys.count() <= 0:
        return

    order_carry = order_carrys[0]
    mama_id = order_carry.mama_id
    print "%s, mama_id: %s" % (get_cur_info(), order_carry.mama_id)

    date_field = order_carry.date_field
    order_id = order_carry.order_id
    contributor_id = order_carry.contributor_id

    uni_key = util_unikey.gen_activevalue_unikey(value_type, mama_id, date_field, order_id, contributor_id)
    value_num = ActiveValue.VALUE_MAP[str(value_type)]

    active_values = ActiveValue.objects.filter(uni_key=uni_key)
    if active_values.count() > 0:
        active_value = active_values[0]
        if active_value.status != order_carry.status:
            active_value.status = order_carry.status
            active_value.value_num = value_num
            if order_carry.status == 0:
                active_value.status = 3  # canceled

            active_value.save()
        return

    if order_carry.status == 0:
        # dont create ActiveValue record if order status is "unpaid"
        return

    status = order_carry.status
    description = util_description.gen_activevalue_description(value_type)
    active_value = ActiveValue(mama_id=mama_id, value_num=value_num, value_type=value_type,
                               value_description=description,
                               uni_key=uni_key, date_field=date_field, status=status)
    active_value.save()


@app.task()
def task_referal_update_activevalue(mama_id, date_field, contributor_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    value_type = 3  # referal
    status = 2  # confirmed
    value_num = ActiveValue.VALUE_MAP[str(value_type)]
    description = util_description.gen_activevalue_description(value_type)
    order_id = ""
    uni_key = util_unikey.gen_activevalue_unikey(value_type, mama_id, date_field, order_id, contributor_id)
    if ActiveValue.objects.filter(uni_key=uni_key).exists():
        return
    active_value = ActiveValue(mama_id=mama_id, value_num=value_num, value_type=value_type,
                               value_description=description,
                               uni_key=uni_key, date_field=date_field, status=status)
    active_value.save()


@app.task()
def task_confirm_previous_activevalue(mama_id, today_date_field, num_days):
    """
    This is how a click-type activevalue gets confirmed:
    everytime a new activevalue gets created, we confirm
    any activevalue of this type generated in previous 7 days.
    """

    end_date_field = today_date_field - datetime.timedelta(days=num_days)

    value_type = 1  # click-type
    active_values = ActiveValue.objects.filter(mama_id=mama_id, value_type=value_type, date_field__lte=end_date_field,
                                               status=1).order_by('-date_field')[:7]
    if active_values.count() <= 0:
        return

    for active_value in active_values:
        date_field = active_value.date_field
        value_num = UniqueVisitor.objects.filter(mama_id=mama_id, date_field=date_field).count()
        active_value.value_num = value_num
        active_value.status = 2  # confirm
        active_value.save()


@app.task()
def task_visitor_increment_activevalue(mama_id, date_field):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    value_type = 1  # click

    uni_key = util_unikey.gen_activevalue_unikey(value_type, mama_id, date_field, None, None)
    active_values = ActiveValue.objects.filter(uni_key=uni_key)

    if active_values.count() <= 0:
        status = 1  # pending
        description = util_description.gen_activevalue_description(value_type)
        active_value = ActiveValue(mama_id=mama_id, value_num=1, value_type=value_type,
                                   uni_key=uni_key, value_description=description,
                                   date_field=date_field, status=status)
        active_value.save()
        # task_confirm_previous_activevalue.s(mama_id, value_type, date_field, 2)()

    else:
        active_values.update(value_num=F('value_num') + 1)
