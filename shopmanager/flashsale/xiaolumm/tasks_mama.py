# -*- encoding:utf-8 -*-

import logging
import datetime
from celery.task import task
from django.db import IntegrityError

from flashsale.xiaolumm import util_description

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models.models_fortune import OrderCarry, AwardCarry, ReferalRelationship
from flashsale.pay.models import Customer
from flashsale.xiaolumm import util_unikey
from flashsale.xiaolumm import utils
from flashsale.xiaolumm.models import XiaoluMama

import sys


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@task()
def task_update_second_level_ordercarry_by_trial(potential, order_carry):
    """
    这里的potential 是　PotentialMama instance (并且必须是is_full_member=False的)　因为转正的有转正的task写记录　不从这里写
    代理（试用／正式） <==　试用代理　<==　订单
    试用代理作为下级代理　给上级代理的　佣金记录
    """
    #if potential.is_full_member:  # 已经是正式的代理则return
    #    return
    carry_type = 3  # 下属订单类型
    parent_mama_id = potential.referal_mama  # 上级代理
    uni_key = util_unikey.gen_ordercarry_unikey(carry_type, order_carry.order_id)
    record = OrderCarry.objects.filter(uni_key=uni_key).first()
    if record:
        if order_carry.modified > record.modified:
            if record.status != order_carry.status:
                record.status = order_carry.status
                record.save(update_fields=['status', 'modified'])
        return

    mama_id = parent_mama_id
    order_id = order_carry.order_id
    order_value = order_carry.order_value
    carry_num = order_carry.carry_num * 0.2  # 20 percent carry

    sku_name = order_carry.sku_name
    sku_img = order_carry.sku_img

    contributor_nick = potential.nick
    contributor_img = potential.thumbnail
    contributor_id = potential.potential_mama  # 被推荐妈妈id

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
                        carry_description=carry_description, sku_img=sku_img,
                        contributor_nick=contributor_nick,
                        contributor_img=contributor_img, contributor_id=contributor_id,
                        agency_level=agency_level, carry_plan_name=carry_plan_name,
                        date_field=date_field, uni_key=uni_key, status=status)
    record.save()


@task()
def task_update_second_level_ordercarry(referal_relationship, order_carry):
    print "%s, mama_id: %s" % (get_cur_info(), order_carry.mama_id)

    carry_type = 3  # second level
    parent_mama_id = referal_relationship.referal_from_mama_id
    uni_key = util_unikey.gen_ordercarry_unikey(carry_type, order_carry.order_id)
    record = OrderCarry.objects.filter(uni_key=uni_key).first()
    if record:
        # Then we just have to update status: only order_carry has modified time greater than
        # the current record, we do update.
        if order_carry.modified > record.modified:
            if record.status != order_carry.status:
                record.status = order_carry.status
                record.save(update_fields=['status', 'modified'])
        else:
            logger.error("%s|order_carry: %s,%s,%s;record:%s,%s,%s" % (get_cur_info(), order_carry.id, order_carry.modified,order_carry.status, record.id, record.modified,record.status))
        return

    mama_id = parent_mama_id
    order_id = order_carry.order_id
    order_value = order_carry.order_value
    carry_num = order_carry.carry_num * 0.2  # 20 percent carry

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
                        carry_description=carry_description, sku_img=sku_img,
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

    status = 0  # unpaid
    if order.is_pending():
        status = 1
    elif order.is_confirmed():
        status = 2
    elif order.is_canceled():
        status = 3

    carry_type = 1  # direct order
    if via_app:
        carry_type = 2  # app order

    carry_description = util_description.get_ordercarry_description(via_app=via_app)
    carry_num = carry_amount
            
    order_id = order.oid
    # each order can only generate carry once for one type.
    uni_key = util_unikey.gen_ordercarry_unikey(carry_type, order_id)

    order_carry = OrderCarry.objects.filter(uni_key=uni_key).first()
    if order_carry:
        update_fields = []
        if order_carry.status != status:
            # We only update status change. We assume no price/value change.
            # We dont do updates on changes other than status change.
            order_carry.status = status
            update_fields.append('status')
        if order_carry.carry_type != carry_type:
            order_carry.carry_type = carry_type
            update_fields.append('carry_type')
        if order_carry.carry_num != carry_num:
            order_carry.carry_num = carry_num
            update_fields.append('carry_num')
        if order_carry.carry_description != carry_description:
            order_carry.carry_description = carry_description
            update_fields.append('carry_description')
        if update_fields:
            update_fields.append('modified')
            order_carry.save(update_fields=update_fields)
        return

    try:
        order_value = order.payment * 100

        sku_name = order.title
        sku_img = order.pic_path

        # We dont use pay_time, because when it gets created, it might not be paid.
        if isinstance(order.pay_time, datetime.datetime):
            date_field = order.pay_time.date()
        else:
            date_field = order.created.date()

        customer = Customer.objects.get(id=customer_pk)
        contributor_nick = customer.nick
        contributor_img = customer.thumbnail
        contributor_id = customer_pk

        order_carry = OrderCarry(mama_id=mama_id, order_id=order_id, order_value=order_value,
                                 carry_num=carry_num, carry_type=carry_type, sku_name=sku_name,
                                 carry_description=carry_description, sku_img=sku_img,
                                 contributor_nick=contributor_nick,
                                 contributor_img=contributor_img, contributor_id=contributor_id,
                                 agency_level=agency_level, carry_plan_name=carry_plan_name,
                                 date_field=date_field, uni_key=uni_key, status=status)
        order_carry.save()
    except IntegrityError as exc:
        logger.warn("IntegrityError - task_update_ordercarry | mama_id: %s, order_id: %s" % (mama_id, order_id))


#award_carry_array99 = [[0, 0], [1, 1500], [4, 2000], [8, 2500], [21, 3500], [41, 4500], [101, 5500]]
#award_carry_array188 = [[0, 0], [1, 3000], [4, 4000], [8, 5000], [21, 7000], [41, 9000], [101, 11000]]
#group_carry_array = [[0, 0], [50, 1000], [200, 1500], [500, 2000], [1000, 3000]]
#
#
#def get_award_carry_num(num, referal_type):
#    """
#    find out award_num
#    referal_type：　邀请类型
#    """
#    idx = 0
#    carry_map = {
#        XiaoluMama.HALF: award_carry_array99,
#        XiaoluMama.FULL: award_carry_array188
#    }
#    award_carry_array = carry_map[referal_type]
#    for entry in award_carry_array:
#        if num < entry[0]:
#            break
#        idx += 1
#
#    if idx == 1:
#        logger.error("get_award_carry_num | num: %s, referal_type: %s" % (num, referal_type))
#    
#    return award_carry_array[idx - 1][1]
#
#
#def get_group_carry_num(num):
#    idx = 0
#    for entry in group_carry_array:
#        if num < entry[0]:
#            break
#        idx += 1
#    return group_carry_array[idx - 1][1]


@task()
def task_referal_update_awardcarry(relationship):
    #print "%s, mama_id: %s" % (get_cur_info(), relationship.referal_from_mama_id)
    from_mama_id = relationship.referal_from_mama_id
    to_mama_id = relationship.referal_to_mama_id
    carry_type = 1 # 直接推荐
    
    #uni_key = util_unikey.gen_awardcarry_unikey(from_mama_id, to_mama_id)
    uni_key = AwardCarry.gen_uni_key(to_mama_id, carry_type)

    rr_cnt = ReferalRelationship.objects.filter(referal_from_mama_id=from_mama_id, referal_type__gte=XiaoluMama.HALF).exclude(referal_to_mama_id=to_mama_id).count()
    rr_cnt += 1
    
    carry_num = utils.get_award_carry_num(rr_cnt, relationship.referal_type)

    status = 1
    carry_description = u'加入正式会员，奖金就会确认哦！'
    
    if relationship.is_confirmed():
        status = 2  # confirmed
        carry_description = util_description.get_awardcarry_description(carry_type)

    award_carry = AwardCarry.objects.filter(uni_key=uni_key).first()
    if award_carry:
        from core.options import log_action, CHANGE, get_systemoa_user
        logmsg = 'mama_id:%s->%s|carry_num:%s->%s|status:%s->%s' % (award_carry.mama_id,from_mama_id,award_carry.carry_num,carry_num,award_carry.status,status)
        update_fields = []
        if award_carry.mama_id != from_mama_id:
            award_carry.mama_id = from_mama_id
            update_fields.append('mama_id')
        if award_carry.carry_num != carry_num:
            award_carry.carry_num = carry_num
            update_fields.append('carry_num')
        if award_carry.status != status:
            award_carry.status = status
            update_fields.append('status')
            if status == 2:
                award_carry.date_field = datetime.date.today()
                update_fields.append('date_field')
        if award_carry.carry_description != carry_description:
            award_carry.carry_description = carry_description
            update_fields.append('carry_description')
        if update_fields:
            update_fields.append('modified')
            award_carry.save(update_fields=update_fields)
            sys_oa = get_systemoa_user()
            log_action(sys_oa, award_carry, CHANGE, logmsg)
        return
    
    if not award_carry:
        date_field = relationship.created.date()
        award_carry = AwardCarry(mama_id=from_mama_id, carry_num=carry_num, carry_type=carry_type,
                                 carry_description=carry_description,
                                 contributor_nick=relationship.referal_to_mama_nick,
                                 contributor_img=relationship.referal_to_mama_img,
                                 contributor_mama_id=relationship.referal_to_mama_id,
                                 date_field=date_field, uni_key=uni_key, status=status)
        award_carry.save()


@task()
def task_update_group_awardcarry(relationship):
    from flashsale.xiaolumm.models.models_fortune import AwardCarry, ReferalRelationship, GroupRelationship

    from_mama_id = relationship.referal_from_grandma_id
    to_mama_id = relationship.referal_to_mama_id
    carry_type = 2 # 团队推荐

    status = 1
    carry_description = u'%s推荐，加入正式会员，奖金就会确认哦！' % relationship.referal_from_mama_id
    
    if relationship.is_confirmed():
        status = 2  # confirmed
        carry_description = util_description.get_awardcarry_description(carry_type)

    direct_referal_num = ReferalRelationship.objects.filter(referal_from_mama_id=from_mama_id, referal_type__gte=XiaoluMama.HALF).exclude(referal_to_mama_id=to_mama_id).count()
    group_referal_num = ReferalRelationship.objects.filter(referal_from_grandma_id=from_mama_id, referal_type__gte=XiaoluMama.HALF).count()
    group_num = direct_referal_num + group_referal_num + 1
    carry_num = utils.get_group_carry_num(group_num)

    # if direct_referal_num >= 15, at least get 1000 cents for group referal
    if carry_num <= 0 and direct_referal_num >= 15:
        carry_num = 1000

    if carry_num <= 0:
        return

    uni_key = AwardCarry.gen_uni_key(to_mama_id, carry_type)
    award_carry = AwardCarry.objects.filter(uni_key=uni_key).first()
    
    if award_carry:
        from core.options import log_action, CHANGE, get_systemoa_user
        logmsg = 'mama_id:%s->%s|carry_num:%s->%s|status:%s->%s' % (award_carry.mama_id,from_mama_id,award_carry.carry_num,carry_num,award_carry.status,status)
        update_fields = []
        if award_carry.mama_id != from_mama_id:
            award_carry.mama_id = from_mama_id
            update_fields.append('mama_id')
        if award_carry.carry_num != carry_num:
            award_carry.carry_num = carry_num
            update_fields.append('carry_num')
        if award_carry.status != status:
            award_carry.status = status
            update_fields.append('status')
            if status == 2:
                award_carry.date_field = datetime.date.today()
                update_fields.append('date_field')
        if award_carry.carry_description != carry_description:
            award_carry.carry_description = carry_description
            update_fields.append('carry_description')
        if update_fields:
            update_fields.append('modified')
            award_carry.save(update_fields=update_fields)
            sys_oa = get_systemoa_user()
            log_action(sys_oa, award_carry, CHANGE, logmsg)
        return

    date_field = relationship.created.date()
    award_carry = AwardCarry(mama_id=from_mama_id, carry_num=carry_num, carry_type=carry_type,
                             contributor_nick=relationship.referal_to_mama_nick,
                             contributor_img=relationship.referal_to_mama_img,
                             contributor_mama_id=relationship.referal_to_mama_id,
                             date_field=date_field, uni_key=uni_key, status=status)
    award_carry.save()





def get_self_mama(unionid, created_time):
    if created_time:
        record = XiaoluMama.objects.filter(openid=unionid, status=XiaoluMama.EFFECT, charge_status=XiaoluMama.CHARGED, charge_time__lte=created_time).first()
        return record
    return None



@task()
def task_order_trigger(sale_order):
    from flashsale.xiaolumm.models.models_fans import XlmmFans
    logger.info("%s, saleorder_pk: %s" % (get_cur_info(), sale_order.id))

    customer_id = sale_order.sale_trade.buyer_id
    customer = Customer.objects.get(id=customer_id)
    self_mama = None
    if customer.unionid:
        self_mama = get_self_mama(customer.unionid, sale_order.created)

    mm_linkid_mama = XiaoluMama.objects.get_by_saletrade(sale_order.sale_trade)

    via_app = sale_order.sale_trade.is_paid_via_app()
    if self_mama:
        mm_linkid_mama = self_mama
        if isinstance(mm_linkid_mama.renew_time,
                      datetime.datetime) and mm_linkid_mama.renew_time < datetime.datetime.now():
            # 如果订单是代理自己购买的　并且这个代理已经过期　则计算为代理的推荐人提成
            referal_ship = ReferalRelationship.objects.filter(referal_to_mama_id=mm_linkid_mama.id,
                                                              status=ReferalRelationship.VALID).first()
            if referal_ship:
                mm_linkid_mama = XiaoluMama.objects.filter(id=referal_ship.referal_from_mama_id,
                                                           status=XiaoluMama.EFFECT,
                                                           charge_status=XiaoluMama.CHARGED,
                                                           charge_time__lte=sale_order.created).first()
    else:
        # customer itself is not a xiaolumama, then check
        # 1) if customer is a fan of a mama and the order is paid via app; or
        # 2) if customer is coming from a mama's share link;
        if via_app:
            # check fan's relationship
            fans_record = XlmmFans.objects.filter(fans_cusid=customer_id, created__lt=sale_order.created).first()
            if fans_record:
                mm_linkid_mama = XiaoluMama.objects.filter(id=fans_record.xlmm,status=XiaoluMama.EFFECT,charge_status=XiaoluMama.CHARGED, charge_time__lte=sale_order.created).first()

    if (not via_app) and (not mm_linkid_mama):
        # handle this case: order is not from app, and order does not have mm_linkid
        fans_record = XlmmFans.objects.filter(fans_cusid=customer_id, created__lt=sale_order.created).first()
        if fans_record:
            mm_linkid_mama = XiaoluMama.objects.filter(id=fans_record.xlmm,status=XiaoluMama.EFFECT,charge_status=XiaoluMama.CHARGED, charge_time__lte=sale_order.created).first()

    if not mm_linkid_mama:
        return

    order_num = 1
    payment = sale_order.payment
    if sale_order.num > 1:
        order_num = sale_order.num
        payment = sale_order.payment / order_num

    from shopback.items.models import Product
    products = Product.objects.filter(id=sale_order.item_id)

    if products.count() <= 0:
        return

    product = products[0]

    carry_scheme = mm_linkid_mama.get_Mama_Order_Rebeta_Scheme(product)
    agency_level = mm_linkid_mama.agencylevel

    #carry_amount = carry_scheme.get_scheme_rebeta(agencylevel=agency_level, payment=payment)
    carry_amount = carry_scheme.calculate_carry(agency_level, payment) * 100 * order_num

    if via_app:
        if self_mama:
            carry_amount = int(carry_amount * 1.08) # 8 percent boost for app orders
        else:
            carry_amount = int(carry_amount * 1.1) # 10 percent boost for app orders

    #logger.warn("carry_amount %s, agency_level: %s, payment: %s, order_id: %s" % (carry_amount, agency_level, payment, sale_order.oid))

    task_update_ordercarry.delay(mm_linkid_mama.pk, sale_order, customer_id, carry_amount, agency_level,
                                 carry_scheme.name, via_app)
    #task_update_ordercarry.apply_async(args=[mm_linkid_mama.pk, sale_order, customer_id, carry_amount, agency_level,
    #                             carry_scheme.name, via_app], countdown=1)

@task()
def carryrecord_update_xiaolumama_active_hasale(mmid):
    from flashsale.xiaolumm.models import CarryRecord
    from flashsale.xiaolumm import tasks_mama_fortune
    mama = XiaoluMama.objects.get(id=mmid)
    if not mama.active:
        active = CarryRecord.objects.filter(mama_id=mmid, carry_type=CarryRecord.CR_CLICK, status__in=[1, 2]).exists()
        if active:
            mama.set_active()
    if not mama.hasale:
        hasale = CarryRecord.objects.filter(mama_id=mmid, carry_type=CarryRecord.CR_ORDER, status__in=[1, 2]).exists()
        if hasale:
            mama.set_hasale()
    for mm_id in mama.get_parent_mama_ids():
        tasks_mama_fortune.task_update_mamafortune_active_num(mm_id)
    # if hasale and mama.hasale != hasale:
    #     mama.set_hasale()
    # elif not hasale and mama.hasale != hasale:
    #     mama.hasale = False
    #     mama.hasale_time = None
    #     mama.save()
