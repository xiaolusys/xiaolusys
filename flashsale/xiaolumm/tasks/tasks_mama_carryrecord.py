# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

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


@app.task(serializer='pickle')
def task_awardcarry_update_carryrecord(carry):
    if carry.mama_id <= 0:
        return
    
    record = CarryRecord.objects.filter(uni_key=carry.uni_key).first()
    if record:
        # 1. 不能同时修改状态和金额
        if record.status != carry.status:
            if carry.status == CarryRecord.CONFIRMED:
                record.confirm()
            if carry.status == CarryRecord.CANCEL:
                record.cancel()
            return

        # 2. 只有预计收益可以修改金额
        if record.carry_num != carry.carry_num:
            if record.status == CarryRecord.PENDING:
                record.changePendingCarryAmount(carry.carry_num)
            return

        return

    CarryRecord.create(carry.mama_id, carry.carry_num, CarryRecord.CR_RECOMMEND, carry.carry_description,
        uni_key=carry.uni_key, status=carry.status)


@app.task(serializer='pickle')
def task_ordercarry_update_carryrecord(carry):
    if carry.mama_id <= 0:
        return

    record = CarryRecord.objects.filter(uni_key=carry.uni_key).first()
    if record:
        if record.status != carry.status:
            if carry.status == CarryRecord.CONFIRMED:
                record.confirm()
            if carry.status == CarryRecord.CANCEL:
                record.cancel()
        return

    CarryRecord.create(carry.mama_id, carry.carry_num, CarryRecord.CR_ORDER, carry.carry_description,
                       uni_key=carry.uni_key,status=carry.status)


@app.task(serializer='pickle')
def task_clickcarry_update_carryrecord(carry):
    if carry.mama_id <= 0:
        return
    
    record = CarryRecord.objects.filter(uni_key=carry.uni_key).first()
    if record:
        # 1. 不能同时修改状态和金额
        if record.status != carry.status:
            if carry.status == CarryRecord.CONFIRMED:
                record.confirm()
            if carry.status == CarryRecord.CANCEL:
                record.cancel()
            return

        # 2. 只有预计收益可以修改金额
        if record.carry_num != carry.total_value:
            if record.status == CarryRecord.PENDING:
                record.changePendingCarryAmount(carry.total_value)
            return

        return

    CarryRecord.create(carry.mama_id, carry.carry_num, CarryRecord.CR_CLICK, carry.carry_description,
                       uni_key=carry.uni_key, status=carry.status)
