#-*- encoding:utf-8 -*-

from django.db.models import F
from celery.task import task


import logging
logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_fortune import MamaFortune,CarryRecord,OrderCarry,AwardCarry,ClickCarry



#STATUS_TYPES = ((0, u'未付款'), (1, u'待确定'), (2, u'已确定'),(3, u'取消'), )
action_dict = {
    "01": {'carry_param':  1, 'cash_param':  0},
    "02": {'carry_param':  1, 'cash_param':  1},
    "03": {'carry_param':  0, 'cash_param':  0},
    "10": {'carry_param': -1, 'cash_param':  0},
    "12": {'carry_param':  0, 'cash_param':  1},
    "13": {'carry_param': -1, 'cash_param':  0},
    "20": {'carry_param': -1, 'cash_param': -1},
    "21": {'carry_param':  0, 'cash_param': -1},
    "23": {'carry_param': -1, 'cash_param': -1},
    "30": {'carry_param':  0, 'cash_param':  0},
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
    
    print 'action_key:', action_key
    action_value = get_action_value(action_key)
    carry_param, cash_param = action_value['carry_param'],action_value['cash_param']
    carry_amount = amount * carry_param
    cash_amount = amount * cash_param
    
    mama_fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if mama_fortunes.count() > 0:
        mama_fortunes.update(carry_num=F('carry_num')+carry_amount, cash_num=F('cash_num')+cash_amount)
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
    
    agency_level     = order_carry.agency_level
    carry_plan_name  = order_carry.carry_plan_name
    
    date_field  = order_carry.date_field
    status      = order_carry.status
    
    record = OrderCarry(mama_id=mama_id, order_id=order_id, order_value=order_value,
                        carry_num=carry_num,carry_type=carry_type,sku_name=sku_name,
                        sku_img=sku_img,contributor_nick=contributor_nick,
                        contributor_img=contributor_img,contributor_id=contributor_id,
                        agency_level=agency_level,carry_plan_name=carry_plan_name,
                        date_field=date_field,uni_key=uni_key,status=status)
    record.save()
    
    
@task()
def update_carryrecord(carry_data, carry_type):
    carry_records = CarryRecord.objects.filter(uni_key=carry_data.uni_key)
    if carry_records.count() > 0:
        print "carry_record exists---"
        record = carry_records[0]
        if record.status != carry_data.status:
            print "status change, gonna update the chain!+++"
            action_key = "%d%d" % (record.status, carry_data.status)
            
            # 1. update carryrecord
            record.status = carry_data.status
            record.save()
            
            # 2. update mamafortune
            increment_mamafortune_cash_and_carry.s(carry_data.mama_id, carry_data.carry_num, action_key)()
        else:
            print "nothing to do, status' the same!+++"
        return

    # We create CarryRecord upon two status: 1) paid(pending); 2) confirmed
    if not (carry_data.is_pending() or carry_data.is_confirmed()):
        return
    
    print "carry_record DOESN'T exists---, gonna create new one +++"
    try:
        # create new record 
        carry_record = CarryRecord(mama_id=carry_data.mama_id,carry_num=carry_data.carry_num,
                                   carry_type=carry_type,date_field=carry_data.date_field,
                                   uni_key=carry_data.uni_key,status=carry_data.status)
        carry_record.save()
    except Exception, e:
        print Exception, ":", e
        print "severe error ++++"
        #log("severe error!+++++++++")
        pass

@task()
def update_carryrecord_carry_num(carry_data):
    carry_records = CarryRecord.objects.filter(uni_key=carry_data.uni_key)
    if carry_records.count() > 0:
        record = carry_records[0]
        if record.carry_num != carry_data.total_value:
            # we dont update status change here, because the status 
            # change will be triggered by orders' status change.
            record.carry_num = carry_data.total_value
            record.save()
        return

    carry_type = 1 # click_carry    

    try:
        # create new record 
        carry_record = CarryRecord(mama_id=carry_data.mama_id,carry_num=carry_data.total_value,
                                   carry_type=carry_type,date_field=carry_data.date_field,
                                   uni_key=carry_data.uni_key,status=carry_data.status)
        carry_record.save()
    except Exception, e:
        print Exception, ":", e
        print "severe error!+++++++++"
        pass
    
@task()
def update_ordercarry(mama_id, order, customer, carry_amount, agency_level, carry_plan_name):
    """
    Whenever a sku order gets saved, trigger this task to update 
    corresponding order_carry record.
    """
    status = 0 #unpaid
    if order.is_pending():
        status = 1
    elif order.is_confirmed():
        status = 2
    elif order.is_canceled():
        status = 3
    
    
    from flashsale.xiaolumm.models_fortune import gen_ordercarry_unikey
    
    order_id = order.oid    
    uni_key = gen_ordercarry_unikey(mama_id,order_id)
    
    order_carrys = OrderCarry.objects.filter(uni_key=uni_key)
    if order_carrys.count() > 0:
        order_carry = order_carrys[0]
        print order_carry.status, status
        if order_carry.status != status:
            # We only update status change. We assume no price/value change.
            # We dont do updates on changes other than status change.
            order_carry.status = status
            order_carry.save()
        return

    try:
        order_value = order.payment * 100
        carry_num   = carry_amount
        carry_type  = 1 # direct order
        sku_name    = order.title
        sku_img     = order.pic_path
        date_field  = order.created.date()
        
        contributor_nick = customer.nick 
        contributor_img  = customer.thumbnail
        contributor_id   = customer.id
        
        order_carry = OrderCarry(mama_id=mama_id,order_id=order_id,order_value=order_value,
                                 carry_num=carry_num,carry_type=carry_type,sku_name=sku_name,
                                 sku_img=sku_img,contributor_nick=contributor_nick,
                                 contributor_img=contributor_img,contributor_id=contributor_id,
                                 agency_level=agency_level,carry_plan_name=carry_plan_name,
                                 date_field=date_field,uni_key=uni_key,status=status)
        order_carry.save()
    except Exception, e:
        print Exception, ":", e
        print "severe error +++"
