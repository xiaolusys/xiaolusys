# -*- encoding:utf-8 -*-

from celery.task import task
from flashsale.xiaolumm import util_description

import logging

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_fortune import OrderCarry, AwardCarry, ReferalRelationship
from flashsale.pay.models import SaleOrder
from flashsale.pay.models_user import Customer
from flashsale.xiaolumm import util_unikey

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
def task_update_second_level_ordercarry(referal_relationship, order_carry):
    print "%s, mama_id: %s" % (get_cur_info(), order_carry.mama_id)

    parent_mama_id = referal_relationship.referal_from_mama_id
    uni_key = util_unikey.gen_ordercarry_unikey(parent_mama_id, order_carry.order_id)
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

    if mama_id == contributor_id:
        # parent cant be myself; stop recursive invoking
        return
    
    agency_level = order_carry.agency_level
    carry_plan_name = order_carry.carry_plan_name

    date_field = order_carry.date_field
    status = order_carry.status
    carry_description = util_description.get_ordercarry_description(second_level=True)
    
    record = OrderCarry(mama_id=mama_id, order_id=order_id, order_value=order_value,
                        carry_num=carry_num, carry_type=carry_type, sku_name=sku_name,
                        carry_description=carry_description,sku_img=sku_img,
                         contributor_nick=contributor_nick,
                        contributor_img=contributor_img, contributor_id=contributor_id,
                        agency_level=agency_level, carry_plan_name=carry_plan_name,
                        date_field=date_field, uni_key=uni_key, status=status)
    record.save()



@task()
def task_update_ordercarry(mama_id, order, customer_pk, carry_amount, agency_level, carry_plan_name, via_app):
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

    order_id = order.oid
    uni_key = util_unikey.gen_ordercarry_unikey(mama_id, order_id)

    order_carrys = OrderCarry.objects.filter(uni_key=uni_key)
    if order_carrys.count() > 0:
        order_carry = order_carrys[0]
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
        customer = Customer.objects.get(id=customer_pk)
        contributor_nick = customer.nick
        contributor_img = customer.thumbnail
        contributor_id = customer_pk

        order_carry = OrderCarry(mama_id=mama_id, order_id=order_id, order_value=order_value,
                                 carry_num=carry_num, carry_type=carry_type, sku_name=sku_name,
                                 carry_description=carry_description,sku_img=sku_img,
                                 contributor_nick=contributor_nick,
                                 contributor_img=contributor_img, contributor_id=contributor_id,
                                 agency_level=agency_level, carry_plan_name=carry_plan_name,
                                 date_field=date_field, uni_key=uni_key, status=status)
        order_carry.save()
    except Exception, e:
        logger.error(e.message, exc_info=True)



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
    
    uni_key = util_unikey.gen_awardcarry_unikey(from_mama_id, to_mama_id)
    

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
    from flashsale.xiaolumm.models_fortune import AwardCarry, ReferalRelationship, GroupRelationship
    
    from_mama_id = relationship.leader_mama_id
    to_mama_id = relationship.member_mama_id

    
    uni_key = util_unikey.gen_awardcarry_unikey(from_mama_id, to_mama_id)
    
    from flashsale.xiaolumm.models_fortune import AwardCarry
    award_carrys = AwardCarry.objects.filter(uni_key=uni_key)
    if award_carrys.count() <= 0:
        direct_referal_num = ReferalRelationship.objects.filter(referal_from_mama_id=from_mama_id).count()
        group_referal_num = GroupRelationship.objects.filter(leader_mama_id=from_mama_id).count()
        carry_num = get_group_carry_num(group_referal_num+direct_referal_num)
        
        # if direct_referal_num >= 15, at least get 1000 cents for group referal
        if carry_num <= 0 and direct_referal_num >= 15:
            carry_num = 1000
        
        if carry_num <= 0:
            return
        
        carry_type = 2 # group referal
        date_field = relationship.created.date()
        status = 2 # confirmed
        award_carry = AwardCarry(mama_id=from_mama_id,carry_num=carry_num,carry_type=carry_type,
                                 contributor_nick=relationship.member_mama_nick,
                                 contributor_img=relationship.member_mama_img,
                                 contributor_mama_id=relationship.member_mama_id,
                                 date_field=date_field,uni_key=uni_key,status=status)
        award_carry.save()



from flashsale.xiaolumm.models import XiaoluMama
from flashsale.xiaolumm.tasks_mama_relationship_visitor import task_update_referal_relationship


def get_self_mama(unionid):
    records = XiaoluMama.objects.filter(openid=unionid, status=XiaoluMama.EFFECT, charge_status=XiaoluMama.CHARGED)
    if records.count() > 0:
        return records[0]
    return None
        

@task()
def task_order_trigger(sale_order):
    print "%s, saleorder_pk: %s" % (get_cur_info(), sale_order.id)

    customer_id = sale_order.sale_trade.buyer_id
    customer = Customer.objects.get(id=customer_id)

    self_mama = get_self_mama(customer.unionid)

    mm_linkid_mama = XiaoluMama.objects.get_by_saletrade(sale_order.sale_trade)
    
    if sale_order.is_deposit():
        if sale_order.is_confirmed():
            if mm_linkid_mama:
                task_update_referal_relationship.s(mm_linkid_mama.pk, self_mama.pk, customer_id)()
        return


    via_app = sale_order.sale_trade.is_paid_via_app()    
    if self_mama:
        mm_linkid_mama = self_mama
    else:
        # customer itself is not a xiaolumama, then check 
        # 1) if customer is a fan of a mama and the order is paid via app; or
        # 2) if customer is coming from a mama's share link; 
        if via_app:
            # check fan's relationship
            from flashsale.xiaolumm.models_fans import XlmmFans
            
            fans_records = XlmmFans.objects.filter(fans_cusid=customer_id)    
            if fans_records.count() > 0:
                mama_id = fans_records[0].xlmm
                mm_linkid_mama = XiaoluMama.objects.get(id=mama_id)

    if not mm_linkid_mama:
        return
    
    payment = sale_order.payment * 100
    
    from shopback.items.models import Product
    products = Product.objects.filter(id=sale_order.item_id)
    
    if products.count() <= 0:
        return
    
    product = products[0]
    
    carry_scheme = mm_linkid_mama.get_Mama_Order_Rebeta_Scheme(product)
    agency_level = mm_linkid_mama.agencylevel
    carry_amount = carry_scheme.get_scheme_rebeta(agencylevel=agency_level,payment=payment)
    
    task_update_ordercarry.s(mm_linkid_mama.pk, sale_order, customer_id, carry_amount, agency_level, carry_scheme.name, via_app)()

    
    
