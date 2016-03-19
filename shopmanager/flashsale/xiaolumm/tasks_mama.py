# -*- encoding:utf-8 -*-

from django.db.models import F
from celery.task import task
from flashsale.xiaolumm import util_description

import logging

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_fortune import CarryRecord, OrderCarry, AwardCarry, ClickCarry, ReferalRelationship, UniqueVisitor
from flashsale.pay.models import SaleOrder
from flashsale.pay.models_user import Customer
from flashsale.xiaolumm import util_unikey

import sys
import datetime


def get_click_plan(order_num):
    MAX_ORDER_NUM = 5
    DEFAULT_PRICE = 10
    DEFAULT_LIMIT = 10
    DEFAULT_NAME = "Default"
    
    if order_num > MAX_ORDER_NUM:
        order_num = MAX_ORDER_NUM
        
    key = str(order_num)

    from flashsale.xiaolumm.models_fortune import ClickPlan
    click_plans = ClickPlan.objects.filter(status=0)
    if click_plans.count() > 0:
        click_plan = click_plans[0]
        rules = click_plan.order_rules

        if key in rules:
            price, limit, name = rules[key][0], rules[key][1], click_plan.name
        else:
            price, limit, name = DEFAULT_PRICE, DEFAULT_LIMIT, DEFAULT_NAME
    return price, limit, name


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    #return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@task()
def task_update_second_level_ordercarry(referal_relationship_pk, order_carry_pk):
    referal_relationship = ReferalRelationship.objects.get(pk=referal_relationship_pk)
    order_carry = OrderCarry.objects.get(pk=order_carry_pk)
    
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
def task_update_ordercarry(mama_id, order_pk, customer_pk, carry_amount, agency_level, carry_plan_name, via_app):
    """
    Whenever a sku order gets saved, trigger this task to update 
    corresponding order_carry record.
    """
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    order = SaleOrder.objects.get(pk=order_pk)
    
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
        customer = Customer.objects.get(pk=customer_pk)
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
def task_group_update_awardcarry(pk):
    from flashsale.xiaolumm.models_fortune import AwardCarry, ReferalRelationship, GroupRelationship

    relationship = GroupRelationship.objects.get(pk=pk)
    
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
            
        carry_type = 2 # group referal
        date_field = relationship.created.date()
        status = 2 # confirmed
        award_carry = AwardCarry(mama_id=from_mama_id,carry_num=carry_num,carry_type=carry_type,
                                 contributor_nick=relationship.member_mama_nick,
                                 contributor_img=relationship.member_mama_img,
                                 contributor_mama_id=relationship.member_mama_id,
                                 date_field=date_field,uni_key=uni_key,status=status)
        award_carry.save()



def confirm_twodays_ago_zero_order_clickcarry(mama_id, today_date_field):
    """
    This is how a zero order clickcarry gets confirmed:
    everytime a new clickcarry gets created, we confirm
    two-days-ago clickcarry, if and only if the 
    clickcarry doesnt have an order related to it. 
    e.g init_order_num == 0
    """
    date_field = today_date_field - datetime.timedelta(days=2)
    click_carrys = ClickCarry.objects.filter(mama_id=mama_id, date_field=date_field)
    if click_carrys.count() <= 0:
        return
    
    click_carry = click_carrys[0]
    if click_carry.init_order_num > 0:
        return

    click_num = UniqueVisitor.objects.filter(mama_id=mama_id,date_field=date_field).count()
    click_carry.click_num = click_num
    price = click_carry.init_click_price
    limit = click_carry.init_click_limit
    if click_num > limit:
        click_num = limit
    total_value = click_num * price
    click_carry.total_value = total_value
    click_carry.status = 2 #confirm
    click_carry.save()

    

def create_clickcarry_upon_click(mama_id, date_field):
    # count all pending+confirmed orders
    order_num = OrderCarry.objects.filter(mama_id=mama_id,date_field=date_field).exclude(status=0).exclude(status=3).exclude(carry_type=3).values('contributor_id').distinct().count()
    click_num = 1
    status = 1 #pending
    price,limit,name = get_click_plan(order_num)        
    uni_key = util_unikey.gen_clickcarry_unikey(mama_id, date_field)
    carry_description = util_description.get_clickcarry_description()
    total_value = price * click_num
    carry = ClickCarry(mama_id=mama_id,click_num=click_num,init_order_num=order_num,
                       init_click_price=price,init_click_limit=limit,total_value=total_value,
                       carry_plan_name=name,carry_description=carry_description,
                       date_field=date_field,uni_key=uni_key,status=status)
    carry.save()


def update_clickcarry_upon_order(click_carry, mama_id, date_field):
    # We count all pending+confirmed orders, and simply update init fields.
    order_num = OrderCarry.objects.filter(mama_id=mama_id,date_field=date_field).exclude(status=0).exclude(status=3).exclude(carry_type=3).values('contributor_id').distinct().count()
    if click_carry.init_order_num != order_num:
        # update price, limit, total_value
        price,limit,name = get_click_plan(order_num)
        click_num = click_carry.click_num
        if click_num > limit:
            click_num = limit
        total_value = click_num * price
        
        click_carry.init_order_num = order_num
        click_carry.init_click_price = price
        click_carry.init_click_limit = limit
        click_carry.total_value = total_value
        click_carry.save()

        
def confirm_clickcarry(click_carry, mama_id, date_field):
    # Get confirmed order number and write back to clickcarry
    confirmed_order_num = OrderCarry.objects.filter(mama_id=mama_id,date_field=date_field,status=2).exclude(carry_type=3).values('contributor_id').distinct().count()
    price,limit,name = get_click_plan(confirmed_order_num)
    click_num = UniqueVisitor.objects.filter(mama_id=mama_id,date_field=date_field).count()
    click_carry.click_num = click_num
    if click_num > limit:
        click_num = limit
    total_value = click_num * price
    click_carry.confirmed_order_num = confirmed_order_num
    click_carry.confirmed_click_price = price
    click_carry.confirmed_click_limit = limit
    click_carry.total_value = total_value
    click_carry.status = 2 #confirm
    click_carry.save()


@task()
def task_visitor_increment_clickcarry(mama_id, date_field):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    
    uni_key = util_unikey.gen_clickcarry_unikey(mama_id, date_field)
    click_carrys = ClickCarry.objects.filter(uni_key=uni_key)
    
    if click_carrys.count() <= 0:
        create_clickcarry_upon_click(mama_id, date_field)
        confirm_twodays_ago_zero_order_clickcarry(mama_id, date_field)
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
    
    click_carrys = ClickCarry.objects.filter(mama_id=mama_id, date_field=date_field)
    if click_carrys.count() <= 0:
        return
    
    # now we have click carry record exists.
    click_carry = click_carrys[0]
    today = datetime.datetime.now().date()
    if today == date_field:
        update_clickcarry_upon_order(click_carry, mama_id, date_field)
        return

    # check whether we should confirm the clickcarry
    pending_order_num = OrderCarry.objects.filter(mama_id=mama_id,date_field=date_field,status=1).exclude(carry_type=3).values('contributor_id').distinct().count()
    print pending_order_num
    if pending_order_num == 0:
        confirm_clickcarry(click_carry, mama_id, date_field)
    else:
        update_clickcarry_upon_order(click_carry, mama_id, date_field)




from flashsale.xiaolumm.models import XiaoluMama
from flashsale.xiaolumm.tasks_mama_relationship_visitor import task_update_referal_relationship


def get_self_mama(unionid):
    records = XiaoluMama.objects.filter(openid=unionid, status=XiaoluMama.EFFECT, progress=XiaoluMama.PASS)
    if records.count() > 0:
        return records[0]
    return None
        

@task()
def task_order_trigger(saleorder_pk):
    print "%s, saleorder_pk: %s" % (get_cur_info(), saleorder_pk)
    
    sale_order = SaleOrder.objects.get(pk=saleorder_pk)
    
    customer_id = sale_order.sale_trade.buyer_id
    customer = Customer.objects.get(pk=customer_id)

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
                mm_linkid_mama = XiaoluMama.objects.get(pk=mama_id)

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
    
    task_update_ordercarry.s(mm_linkid_mama.pk, saleorder_pk, customer_id, carry_amount, agency_level, carry_scheme.name, via_app)()

    
    
