# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task as task

import sys
import datetime
from flashsale.xiaolumm.models.models_fortune import CarryRecord

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


@task(serializer='pickle')
def task_awardcarry_update_carryrecord(carry):
    #print "%s, mama_id: %s" % (get_cur_info(), carry.mama_id)
    if carry.mama_id <= 0:
        return
    
    record = CarryRecord.objects.filter(uni_key=carry.uni_key).first()
    if record:
        update_fields = []
        if record.status != carry.status:
            record.status = carry.status
            update_fields.append('status')
            if carry.status == 2:
                record.date_field = datetime.date.today()
                update_fields.append('date_field')
        if record.carry_num != carry.carry_num:
            record.carry_num = carry.carry_num
            update_fields.append('carry_num')
        if record.mama_id != carry.mama_id:
            record.mama_id = carry.mama_id
            update_fields.append('mama_id')
        if record.carry_description != carry.carry_description:
            record.carry_description = carry.carry_description
            update_fields.append('carry_description')
        if update_fields:
            update_fields.append('modified')
            record.save(update_fields=update_fields)
    else:
        carry_type = 3  # awardcarry
        carry_record = CarryRecord(mama_id=carry.mama_id, carry_num=carry.carry_num,
                                   carry_type=carry_type, date_field=carry.date_field,
                                   carry_description=carry.carry_description,
                                   uni_key=carry.uni_key, status=carry.status)
        carry_record.save()


@task(serializer='pickle')
def task_ordercarry_update_carryrecord(carry):
    if carry.mama_id <= 0:
        return

    record = CarryRecord.objects.filter(uni_key=carry.uni_key).first()
    if record:
        if record.status != carry.status:
            record.status = carry.status
            record.save()
        return
    # We create CarryRecord upon two status: 1) paid(pending); 2) confirmed
    if not (carry.is_pending() or carry.is_confirmed()):
        return

    # create new record 
    carry_type = 2  # ordercarry
    carry_record = CarryRecord(mama_id=carry.mama_id, carry_num=carry.carry_num,
                               carry_type=carry_type, date_field=carry.date_field,
                               carry_description=carry.carry_description,
                               uni_key=carry.uni_key, status=carry.status)
    carry_record.save()


@task(serializer='pickle')
def task_clickcarry_update_carryrecord(carry):
    if carry.mama_id <= 0:
        return
    
    records = CarryRecord.objects.filter(uni_key=carry.uni_key)
    if records.count() > 0:
        record = records[0]
        if record.carry_num != carry.total_value or record.status != carry.status:
            record.carry_num = carry.total_value
            record.status = carry.status
            record.save()
        return
    else:
        carry_type = 1  # clickcarry
        carry_record = CarryRecord(mama_id=carry.mama_id, carry_num=carry.total_value,
                                   carry_type=carry_type, date_field=carry.date_field,
                                   carry_description=carry.carry_description,
                                   uni_key=carry.uni_key, status=carry.status)
        carry_record.save()
