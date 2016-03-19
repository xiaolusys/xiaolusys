# -*- encoding:utf-8 -*-

from django.db.models import F
from celery.task import task
from flashsale.xiaolumm import util_description

import logging

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_fortune import CarryRecord, OrderCarry, AwardCarry, ClickCarry
from flashsale.pay.models import SaleOrder

import sys


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    #return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@task()
def task_awardcarry_update_carryrecord(carry):
    print "%s, mama_id: %s" % (get_cur_info(), carry.mama_id)
    
    records = CarryRecord.objects.filter(uni_key=carry.uni_key)
    if records.count() > 0:
        record = records[0]
        if record.status != carry.status:
            record.status = carry.status
            record.save()
    else:
        carry_type = 3 # awardcarry
        carry_record = CarryRecord(mama_id=carry.mama_id, carry_num=carry.carry_num,
                                   carry_type=carry_type, date_field=carry.date_field,
                                   carry_description=carry.carry_description,
                                   uni_key=carry.uni_key, status=carry.status)
        carry_record.save()

        

@task()        
def task_ordercarry_update_carryrecord(carry):    
    records = CarryRecord.objects.filter(uni_key=carry.uni_key)
    if records.count() > 0:
        record = records[0]
        if record.status != carry.status:
            record.status = carry.status
            record.save()
        return
    # We create CarryRecord upon two status: 1) paid(pending); 2) confirmed
    if not (carry.is_pending() or carry.is_confirmed()):
        return
    
    # create new record 
    carry_type = 2 # ordercarry
    carry_record = CarryRecord(mama_id=carry.mama_id, carry_num=carry.carry_num,
                               carry_type=carry_type, date_field=carry.date_field,
                               carry_description=carry.carry_description,
                               uni_key=carry.uni_key, status=carry.status)
    carry_record.save()
    

@task()
def task_clickcarry_update_carryrecord(carry):    
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



    
    
