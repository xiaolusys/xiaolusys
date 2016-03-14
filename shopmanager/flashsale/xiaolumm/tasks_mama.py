# -*- encoding:utf-8 -*-

from django.db.models import F
from celery.task import task
from flashsale.xiaolumm import util_description

import logging

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_fortune import MamaFortune, CarryRecord, OrderCarry, AwardCarry, ClickCarry

import sys

def get_click_price_and_limit(order_num):
    MAX_ORDER_NUM = 5
    DEFAULT_PRICE = 10
    DEFAULT_LIMIT = 10
    
    if order_num > MAX_ORDER_NUM:
        order_num = MAX_ORDER_NUM
        
    key = str(order_num)

    from flashsale.xiaolumm.models_fortune import ClickPlan
    click_plans = ClickPlan.objects.filter(status=0)
    if click_plans.count() > 0:
        click_plan = click_plans[0]
        rules = click_plan.order_rules

        if key in rules:
            price, limit = rules[key]
        else:
            price, limit = DEFAULT_PRICE, DEFAULT_LIMIT
    return price, limit


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    #return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


#STATUS_TYPES = ((0, u'未付款'), (1, u'待确定'), (2, u'已确定'),(3, u'取消'), )
action_dict = {
    "01": {'carry_param':  1, 'cash_param': 0},
    "02": {'carry_param':  1, 'cash_param': 1},
    "03": {'carry_param':  0, 'cash_param': 0},
    "10": {'carry_param': -1, 'cash_param': 0},
    "12": {'carry_param':  0, 'cash_param': 1},
    "13": {'carry_param': -1, 'cash_param': 0},
    "20": {'carry_param': -1, 'cash_param':-1},
    "21": {'carry_param':  0, 'cash_param':-1},
    "23": {'carry_param': -1, 'cash_param':-1},
    "30": {'carry_param':  0, 'cash_param': 0},
    "31": {'carry_param':  1, 'cash_param': 0},
    "32": {'carry_param':  1, 'cash_param': 1}
}

order_active_dict = {
    "02":"incr",
    "12":"incr",
    "32":"incr",
    "20":"decr",
    "21":"decr",
    "23":"decr"
}


def get_action_value(action_key):
    if action_key in action_dict:
        return action_dict[action_key]
    return {'carry_param': 0, 'cash_param': 0}


@task()
def update_second_level_ordercarry(referal_relationship, order_carry):
    print "%s, mama_id: %s" % (get_cur_info(), order_carry.mama_id)
    from flashsale.xiaolumm.models_fortune import gen_ordercarry_unikey

    parent_mama_id = referal_relationship.referal_from_mama_id
    uni_key = gen_ordercarry_unikey(parent_mama_id, order_carry.order_id)
    records = OrderCarry.objects.filter(uni_key=uni_key)
    if records.count() > 0:
        record = records[0]
        if record.status != order_carry.status:
            record.status = order_carry.status
            record.save()
        return

    mama_id = parent_mama_id
    order_id = order_carry.order_id
    order_value = order_carry.order_value
    carry_num = order_carry.carry_num * 0.1  # 10 percent carry
    carry_type = 3  # second level
    sku_name = order_carry.sku_name
    sku_img = order_carry.sku_img

    contributor_nick = referal_relationship.referal_to_mama_nick
    contributor_img = referal_relationship.referal_to_mama_img
    contributor_id = referal_relationship.referal_to_mama_id

    agency_level = order_carry.agency_level
    carry_plan_name = order_carry.carry_plan_name

    date_field = order_carry.date_field
    status = order_carry.status
    carry_description = util_description.get_ordercarry_description(second_level=True)
    
    record = OrderCarry(mama_id=mama_id, order_id=order_id, order_value=order_value,
                        carry_num=carry_num, carry_type=carry_type, sku_name=sku_name,
                        sku_img=sku_img, contributor_nick=contributor_nick,
                        contributor_img=contributor_img, contributor_id=contributor_id,
                        agency_level=agency_level, carry_plan_name=carry_plan_name,
                        date_field=date_field, uni_key=uni_key, status=status)
    record.save()


@task()
def update_carryrecord(carry_data, carry_type):
    print "%s, mama_id: %s" % (get_cur_info(), carry_data.mama_id)

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
            from flashsale.xiaolumm.tasks_mama_fortune import task_increment_mamafortune_cash_and_carry
            task_increment_mamafortune_cash_and_carry.s(carry_data.mama_id, carry_data.carry_num, action_key)()
        else:
            print "nothing to do, status' the same!+++"
        return

    # We create CarryRecord upon two status: 1) paid(pending); 2) confirmed
    if not (carry_data.is_pending() or carry_data.is_confirmed()):
        return

    print "carry_record DOESN'T exists---, gonna create new one +++"
    try:
        # create new record 
        carry_record = CarryRecord(mama_id=carry_data.mama_id, carry_num=carry_data.carry_num,
                                   carry_type=carry_type, date_field=carry_data.date_field,
                                   carry_description=carry_data.carry_description,
                                   uni_key=carry_data.uni_key, status=carry_data.status)
        carry_record.save()
    except Exception, e:
        print Exception, ":", e
        print "severe error ++++"
        #log("severe error!+++++++++")
        pass


@task()
def update_carryrecord_carry_num(carry_data):
    print "%s, mama_id: %s" % (get_cur_info(), carry_data.mama_id)

    carry_records = CarryRecord.objects.filter(uni_key=carry_data.uni_key)
    if carry_records.count() > 0:
        record = carry_records[0]
        if record.carry_num != carry_data.total_value:
            # we dont update status change here, because the status 
            # change will be triggered by orders' status change.
            record.carry_num = carry_data.total_value
            record.save()
        return

    carry_type = 1  # click_carry

    try:
        # create new record 
        carry_record = CarryRecord(mama_id=carry_data.mama_id, carry_num=carry_data.total_value,
                                   carry_type=carry_type, date_field=carry_data.date_field,
                                   uni_key=carry_data.uni_key, status=carry_data.status)
        carry_record.save()
    except Exception, e:
        print Exception, ":", e
        print "severe error!+++++++++"
        pass



@task()
def update_ordercarry(mama_id, order, customer, carry_amount, agency_level, carry_plan_name, via_app):
    """
    Whenever a sku order gets saved, trigger this task to update 
    corresponding order_carry record.
    """
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    status = 0  #unpaid
    if order.is_pending():
        status = 1
    elif order.is_confirmed():
        status = 2
    elif order.is_canceled():
        status = 3

    from flashsale.xiaolumm.models_fortune import gen_ordercarry_unikey

    order_id = order.oid
    uni_key = gen_ordercarry_unikey(mama_id, order_id)

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
        carry_num = carry_amount

        carry_type = 1  # direct order
        if via_app:
            carry_type = 2  # app order

        sku_name = order.title
        sku_img = order.pic_path
        date_field = order.created.date()

        carry_description = util_description.get_ordercarry_description(via_app=via_app)
        contributor_nick = customer.nick
        contributor_img = customer.thumbnail
        contributor_id = customer.id

        order_carry = OrderCarry(mama_id=mama_id, order_id=order_id, order_value=order_value,
                                 carry_num=carry_num, carry_type=carry_type, sku_name=sku_name,
                                 carry_description=carry_description,sku_img=sku_img,
                                 contributor_nick=contributor_nick,
                                 contributor_img=contributor_img, contributor_id=contributor_id,
                                 agency_level=agency_level, carry_plan_name=carry_plan_name,
                                 date_field=date_field, uni_key=uni_key, status=status)
        order_carry.save()
    except Exception, e:
        print Exception, ":", e
        print "severe error +++"


@task()
def task_activevalue_update_mamafortune(active_value, action="incr"):
    """
    更新妈妈财富数值
    """
    print "%s, mama_id: %s" % (get_cur_info(), active_value.mama_id)

    from flashsale.xiaolumm.models_fortune import MamaFortune

    mama_id = active_value.mama_id
    value_type = active_value.value_type

    base_num, value_num = 1, active_value.value_num
    if action == "decr":
        base_num = -1
        value_num = -active_value.value_num

    mama_fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if mama_fortunes.count() > 0:
        if value_type == 4:  #fans
            mama_fortunes.update(fans_num=F('fans_num') + base_num, active_value_num=F('active_value_num') + value_num)
        elif value_type == 3:  # referal
            mama_fortunes.update(invite_num=F('invite_num') + base_num,
                                 active_value_num=F('active_value_num') + value_num)
        elif value_type == 2:  # order
            mama_fortunes.update(invite_num=F('order_num') + base_num,
                                 active_value_num=F('active_value_num') + value_num)
        elif value_type == 1:  # click
            mama_fortunes.update(active_value_num=F('active_value_num') + value_num)
    else:
        if value_type == 4:  #fans
            mama_fortune = MamaFortune(fans_num=base_num, active_value_num=value_num)
        elif value_type == 3:  # referal
            mama_fortune = MamaFortune(invite_num=base_num, active_value_num=value_num)
        elif value_type == 2:  # order
            mama_fortune = MamaFortune(invite_num=base_num, active_value_num=value_num)
        elif value_type == 1:  # click
            mama_fortune = MamaFortune(active_value_num=value_num)
        else:
            return
        mama_fortune.save()





@task()
def task_update_referal_relationship(from_mama_id, to_mama_id, customer):
    from flashsale.xiaolumm.models_fortune import ReferalRelationship
    print "%s, mama_id: %s" % (get_cur_info(), from_mama_id)    

    records = ReferalRelationship.objects.filter(referal_to_mama_id=to_mama_id)
    if records.count() <= 0:
        record = ReferalRelationship(referal_from_mama_id=from_mama_id,referal_to_mama_id=to_mama_id,
                                     referal_to_mama_nick=customer.nick,
                                     referal_to_mama_img=customer.thumbnail)
        record.save()
    else:
        print "server error++"
        pass
        #log("something wrong")
        
    

@task()
def task_update_group_relationship(leader_mama_id, referal_relationship):
    from flashsale.xiaolumm.models_fortune import GroupRelationship
    print "%s, mama_id: %s" % (get_cur_info(), referal_relationship.referal_from_mama_id)
    
    records = GroupRelationship.objects.filter(member_mama_id=referal_relationship.referal_to_mama_id)
    if records.count() <= 0:
        record = GroupRelationship(leader_mama_id=leader_mama_id,
                                   referal_from_mama_id=referal_relationship.referal_from_mama_id,
                                   member_mama_id=referal_relationship.referal_to_mama_id,
                                   member_mama_nick=referal_relationship.referal_to_mama_nick,
                                   member_mama_img=referal_relationship.referal_to_mama_img)

        record.save()
    else:
        print "server error++"
        pass
        #log("something wrong")

    pass


award_carry_array = [[0,0],[1, 3000],[4, 4000],[8, 5000],[21, 7000],[41, 9000],[101,11000]]
group_carry_array = [[0,0],[50,1000],[200,1500],[500,2000],[1000,3000]]


def get_award_carry_num(num):
    """
    find out award_num
    """
    idx = 0
    for entry in award_carry_array:
        if num < entry[0]:
            break
        idx += 1
    return award_carry_array[idx-1][1]


def get_group_carry_num(num):
    idx = 0
    for entry in group_carry_array:
        if num < entry[0]:
            break
        idx += 1
    return group_carry_array[idx-1][1]
    
    


@task()
def task_referal_update_awardcarry(relationship):
    print "%s, mama_id: %s" % (get_cur_info(), relationship.referal_from_mama_id)
    from_mama_id = relationship.referal_from_mama_id
    to_mama_id = relationship.referal_to_mama_id
    
    from flashsale.xiaolumm.models_fortune import gen_awardcarry_unikey
    uni_key = gen_awardcarry_unikey(from_mama_id, to_mama_id)
    
    from flashsale.xiaolumm.models_fortune import AwardCarry, ReferalRelationship
    award_carrys = AwardCarry.objects.filter(uni_key=uni_key)
    if award_carrys.count() <= 0:
        records = ReferalRelationship.objects.filter(referal_from_mama_id=from_mama_id)
        
        carry_num = get_award_carry_num(records.count())
        carry_type = 1 # direct referal
        date_field = relationship.created.date()
        status = 2 # confirmed
        carry_description = util_description.get_awardcarry_description(carry_type)
        award_carry = AwardCarry(mama_id=from_mama_id,carry_num=carry_num,carry_type=carry_type,
                                 contributor_nick=relationship.referal_to_mama_nick,
                                 contributor_img=relationship.referal_to_mama_img,
                                 contributor_mama_id=relationship.referal_to_mama_id,
                                 date_field=date_field,uni_key=uni_key,status=status)
        award_carry.save()

    

@task()
def task_group_update_awardcarry(relationship):
    from_mama_id = relationship.leader_mama_id
    to_mama_id = relationship.member_mama_id

    from flashsale.xiaolumm.models_fortune import AwardCarry, ReferalRelationship, GroupRelationship, gen_awardcarry_unikey
    uni_key = gen_awardcarry_unikey(from_mama_id, to_mama_id)
    
    from flashsale.xiaolumm.models_fortune import AwardCarry
    award_carrys = AwardCarry.objects.filter(uni_key=uni_key)
    if award_carrys.count() <= 0:
        direct_referal_num = ReferalRelationship.objects.filter(referal_from_mama_id=from_mama_id).count()
        group_referal_num = GroupRelationship.objects.filter(leader_mama_id=from_mama_id).count()
        carry_num = get_group_carry_num(group_referal_num+direct_referal_num)
        
        # if direct_referal_num >= 15, at least get 10 for group referal
        if carry_num <= 0 and direct_referal_num >= 15:
            carry_num = 10
            
        carry_type = 2 # group referal
        date_field = relationship.created.date()
        status = 2 # confirmed
        award_carry = AwardCarry(mama_id=from_mama_id,carry_num=carry_num,carry_type=carry_type,
                                 contributor_nick=relationship.member_mama_nick,
                                 contributor_img=relationship.member_mama_img,
                                 contributor_mama_id=relationship.member_mama_id,
                                 date_field=date_field,uni_key=uni_key,status=status)
        award_carry.save()


@task()
def task_update_unique_visitor(mama_id, openid, appkey, click_time):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    from flashsale.xiaolumm.models import XiaoluMama
    if XiaoluMama.objects.filter(pk=mama_id).count() <= 0:
        return

    from shopapp.weixin.options import get_unionid_by_openid
    nick,img = '',''
    unionid = get_unionid_by_openid(openid, appkey)
    if unionid:
        customers = Customer.objects.filter(unionid=unionid)
        if customers.count() > 0:
            nick,img = customers[0].nick,customers[0].thumbnail
    else:
        # if no unionid exists, then use openid
        unionid = openid
    
    date_field = click_time.date()
    uni_key = '-'.join([openid, str(date_field)])
    
    try:
        from flashsale.xiaolumm.models_fortune import UniqueVisitor
        visitor = UniqueVisitor(mama_id=mama_id,visitor_unionid=unionid,visitor_nick=nick,
                                visitor_img=img,uni_key=uni_key,date_field=date_field)
        visitor.save()
    except Exception,e:
        print Exception, ":", e
        pass
    

@task()
def task_visitor_increment_clickcarry(mama_id, date_field):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    
    from flashsale.xiaolumm.util_unikey import gen_clickcarry_unikey
    uni_key = gen_clickcarry_unikey(mama_id, date_field)

    click_carrys = ClickCarry.objects.filter(uni_key=uni_key)
    
    if click_carrys.count() <= 0:
        status = 1 #pending
        carry_description = util_description.get_clickcarry_description()
        
        order_num = 0
        price,limit = get_click_price_and_limit(order_num)
        total_value = price * 1
        
        click_carry = ClickCarry(mama_id=mama_id, click_num=1, init_click_price=price,
                                 init_click_limit=limit,total_value=total_value,
                                 uni_key=uni_key, date_field=date_field, status=status)
        click_carry.save()
    else:
        price = click_carrys[0].init_click_price
        limit = click_carrys[0].init_click_limit
        click_num = click_carrys[0].click_num
        if click_num < limit:
            total_value = (click_num + 1) * price
            click_carrys.update(click_num=F('click_num')+1, total_value=total_value)
        else:
            click_carrys.update(click_num=F('click_num')+1)
        

@task()
def task_update_clickcarry_order_number(mama_id, date_field):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    from flashsale.xiaolumm.models_fortune import OrderCarry, ClickCarry

    records = OrderCarry.objects.filter(mama_id=mama_id,date_field=date_field).exclude(status=0).exclude(status=3).exclude(carry_type=3).values('contributor_id')
    order_num = records.count()
    
    click_carrys = ClickCarry.objects.filter(mama_id=mama_id, date_field=date_field)
    if click_carrys.count() > 0:
        # only update order number if clickcarry record exists.
        # if record doesnt exist, that means no click happens.
        price, limit = get_click_price_and_limit(order_num)
        click_num = click_carrys[0].click_num
        total_value = click_num * price
        if click_carrys[0].is_confirmed():
            click_carrys.update(confirmed_order_num=order_num, confirmed_click_price=price, 
                                confirmed_click_limit=limit, total_value=total_value)
        else:
            click_carrys.update(init_order_num=order_num, init_click_price=price, 
                                init_click_limit=limit, total_value=total_value)
                
        
    
                       
