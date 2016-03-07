#-*- encoding:utf-8 -*-
import time
import datetime
from django.db.models import F,Sum,Q
from django.conf import settings
from celery.task import task


import logging
logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_fortune import MamaFortune



#STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'),(3, u'取消'), )
action_dict = {
    "12": {'carry_param':  0, 'cash_param':  1},
    "13": {'carry_param': -1, 'cash_param':  0},
    "21": {'carry_param':  0, 'cash_param': -1},
    "23": {'carry_param': -1, 'cash_param': -1},
    "31": {'carry_param':  1, 'cash_param':  0},
    "32": {'carry_param':  1, 'cash_param':  1}
    }

def get_action_value(action_key):
    if action_key in action_dict:
        return action_dict[action_key]
    return {'carry_param':  0, 'cash_param':  0}
    

@task()
def increment_mamafortune_cash_and_carry(mama_id, amount, action_key):
    """
    动态更新小鹿妈妈的cash和carry，amount可以为负。
    """
    if amount == 0: 
        return
    
    action_value = get_action_value(action_key)
    carry_param, cash_param = action_value['carry_param'],action_value['cash_param']
    carry_amount = amount * carry_param
    cash_amount = amount * cash_param
    
    mama_fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if mama_fortunes.count() > 0:
        mama_fortunes.update(carry_num=F('cash_num')+carry_amount, cash_num=F('carry_num')+cash_amount)
    else:
        mama_fortune = MamaFortune(mama_id=mama_id, carry_num=carry_amount, cash_num=cash_amount)
        mama_fortune.save()




@task()
def update_second_level_ordercarry(parent_mama_id, order_carry):
    uni_key = gen_ordercarry_unikey(parent_mama_id, order_carry.order_id)
    records = OrderCarry.objects.filter(uni_key=uni_key)
    
    if records.count() > 0:
        record = records[0]
        if record.status != order_carry.status:
            record.status = order_carry.status
            record.save()
        return
    
    mama_id     = parent_mama_id
    order_id    = order_carry.order_id
    order_value = order_carry.order_vale
    carry_num   = order_carry.carry_num * 0.1 # 10 percent carry
    carry_type  = 3 # second level
    sku_name    = order_carry.sku_name
    sku_img     = order_carry.sku_img

    contributor_nick = order_carry.contributor_nick
    contributor_img  = order_carry.contributor_img
    contributor_id   = order_carry.contributor_id

    date_field  = order_carry.date_field
    status      = order_carry.status
    
    record = OrderCarry(mama_id=mama_id, order_id=order_id, order_value=order_value,
                             carry_num=carry_num,carry_type=carry_type,sku_name=sku_name,
                             sku_img=sku_img,contributor_nick=contributor_nick,
                             contributor_img=contributor_img,contributor_id=contributor_id,
                             date_field=date_field,uni_key=uni_key,status=status)
    record.save()
    
    
@task()
def update_carryrecord(carry_data, carry_type):
    carry_records = CarryRecord.objects.filter(uni_key=carry_data.uni_key)
    if carry_records.count() > 0:
        record = carry_records[0]
        if record.status != carry_data.status:
            action_key = "%d%d" % (record.status, carry_data.status)
            
            # 1. update carryrecord
            record.status = carry_data.status
            record.save()
            
            # 2. update mamafortune
            increment_mamafortune_cash_and_carry.s(carry_data.mama_id, carry_data.carry_num, action_key)()
            
        return
    try:
        # create new record 
        carry_record = CarryRecord(mama_id=carry_data.mama_id,carry_num=carry_data.carry_num,
                                   carry_type=carry_type,date_field=carry_data.date_field,
                                   uni_key=carry_data.uni_key,status=carry_data.status)
        carry_record.save()
    except:
        #log("severe error!+++++++++")
        pass

@task()
def update_carryrecord_carry_num(carry_data):
    carry_records = CarryRecord.objects.filter(uni_key=carry_data.uni_key)
    if carry_records.count() > 0:
        record = carry_records[0]
        if record.carry_num != carry_data.carry_num:
            record.carry_num = carry_data.carry_num
            record.save()
        return

    carry_type = 1 # click_carry    

    try:
        # create new record 
        carry_record = CarryRecord(mama_id=carry_data.mama_id,carry_num=carry_data.carry_num,
                                   carry_type=carry_type,date_field=carry_data.date_field,
                                   uni_key=carry_data.uni_key,status=carry_data.status)
        carry_record.save()
    except:
        #log("severe error!+++++++++")
        pass
    
    
