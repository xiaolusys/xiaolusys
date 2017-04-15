# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import sys
import datetime
from django.db import IntegrityError

from flashsale.xiaolumm import util_description
from flashsale.xiaolumm.models.models_fortune import OrderCarry, AwardCarry, ReferalRelationship, ExchangeSaleOrder
from flashsale.pay.models import Customer
from flashsale.xiaolumm import util_unikey
from flashsale.xiaolumm import utils
from flashsale.xiaolumm import constants
from flashsale.xiaolumm.models import XiaoluMama

import logging

logger = logging.getLogger('service')


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@app.task()
def task_update_second_level_ordercarry_by_trial(potential, order_carry):
    """
    这里的potential 是　PotentialMama instance (并且必须是is_full_member=False的)　因为转正的有转正的task写记录　不从这里写
    代理（试用／正式） <==　试用代理　<==　订单
    试用代理作为下级代理　给上级代理的　佣金记录
    """
    # if potential.is_full_member:  # 已经是正式的代理则return
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


def get_level_differential(model_product, high_level, low_level):
    """
    获得商品在2个妈妈等级之间的级差
    """
    from flashsale.pay.apis.v1.product import get_level_differential_from_boutique_modelproduct
    level_prices = get_level_differential_from_boutique_modelproduct(model_product)
    elite_level_map = {
        'Associate': 0,
        'Director': 1,
        'VP': 2,
        'Partner': 3,
        'SP': 4
    }
    high_index = elite_level_map[high_level]
    if low_level:
        low_index = elite_level_map[low_level]
        # 有时候下级比上级等级还高，那么就返回金额为0
        if level_prices[high_index] - level_prices[low_index] >= 0:
            return level_prices[high_index] - level_prices[low_index]
        else:
            return 0
    else:
        return level_prices[high_index]


def gen_ordercarry(referal_relationship, order_carry, carry_type, carry_num):
    """
    referal_relationship 拿到上一级
    order_carry参考的前一级ordercarry
    carry_type类型
    """

    parent_mama_id = referal_relationship.referal_from_mama_id
    # 为了跟以前保持兼容，第2级的unikey不带count
    if carry_type == OrderCarry.REFERAL_ORDER:
        if order_carry.carry_type == OrderCarry.WAP_ORDER or order_carry.carry_type == OrderCarry.APP_ORDER:
            uni_key = util_unikey.gen_ordercarry_unikey(OrderCarry.REFERAL_ORDER, order_carry.order_id)
        else:
            # 要看自己是哪一级，才能唯一确定自己上级的等级
            l2_uni_key = util_unikey.gen_ordercarry_unikey(OrderCarry.REFERAL_ORDER, order_carry.order_id)
            if order_carry.uni_key == l2_uni_key:
                uni_key = '-'.join(['order', str(carry_type), order_carry.order_id, str(3)])
            else:
                keys = order_carry.split('-')
                count = int(keys[-1])
                uni_key = '-'.join(['order', str(carry_type), order_carry.order_id, str(count + 1)])
    else:
        uni_key = util_unikey.gen_ordercarry_unikey(carry_type, order_carry.order_id)
    record = OrderCarry.objects.filter(uni_key=uni_key).first()
    if record:
        if record.status != order_carry.status:
            record.status = order_carry.status
            record.save(update_fields=['status', 'modified'])
        if record.carry_num != carry_num:
            record.carry_num = carry_num  # temp fix data 20170415
            record.save(update_fields=['carry_num'])
        return

    mama_id = parent_mama_id
    order_id = order_carry.order_id
    order_value = order_carry.order_value

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

    try:
        record = OrderCarry(mama_id=mama_id, order_id=order_id, order_value=order_value,
                            carry_num=carry_num, carry_type=carry_type, sku_name=sku_name,
                            carry_description=carry_description, sku_img=sku_img,
                            contributor_nick=contributor_nick,
                            contributor_img=contributor_img, contributor_id=contributor_id,
                            agency_level=agency_level, carry_plan_name=carry_plan_name,
                            date_field=date_field, uni_key=uni_key, status=status)
        record.save()
    except IntegrityError as exc:
        logger.warn("IntegrityError - gen_ordercarry | mama_id: %s, order_id: %s" % (mama_id, order_id))


@app.task()
def task_update_second_level_ordercarry(referal_relationship, order_carry):
    logger.info({
        'action': 'task_update_second_level_ordercarry',
        'order_no': order_carry.order_id,
        'mama_id': order_carry.mama_id,
        'created': datetime.datetime.now(),
    })
    records = OrderCarry.objects.filter(order_id=order_carry.order_id, carry_type__in=[OrderCarry.REFERAL_ORDER,
                                                                                       OrderCarry.ADVANCED_MAMA_REFERAL_ORDER])
    if records.exists():
        for record in records:
            if record.status != order_carry.status:
                record.status = order_carry.status
                record.save(update_fields=['status', 'modified'])
        # return  # temp add data fix

    from flashsale.pay.models.trade import SaleOrder
    sale_order = SaleOrder.objects.filter(oid=order_carry.order_id).first()
    # 这个订单第一级获得收益的妈妈
    mm_linkid_mama = XiaoluMama.objects.filter(id=order_carry.mama_id, status=XiaoluMama.EFFECT,
                                               charge_status=XiaoluMama.CHARGED).first()
    from shopback.items.models import Product
    products = Product.objects.filter(id=sale_order.item_id)
    if products.count() <= 0:
        logger.info({
            'action': 'task_update_second_level_ordercarry',
            'order_no': sale_order.oid,
            'desc': 'not found product',
            'mm_linkid_mama': mm_linkid_mama,
            'product_id': sale_order.item_id,
            'created': datetime.datetime.now(),
        })
        return

    product = products[0]
    model_product = product.get_product_model()
    if model_product:
        if model_product.is_boutique_product:
            # 第一级的妈妈已经是direct，那么就没有后面ordercarry存在必要了
            if mm_linkid_mama.referal_from == XiaoluMama.DIRECT:
                logger.info({
                    'action': 'task_update_second_level_ordercarry',
                    'order_no': sale_order.oid,
                    'desc': 'first level is direct,return',
                    'mm_linkid_mama': mm_linkid_mama.id,
                    'referal': mm_linkid_mama.referal_from,
                    'created': datetime.datetime.now(),
                })
                return
            if not (mm_linkid_mama.referal_from == XiaoluMama.INDIRECT and mm_linkid_mama.elite_score <
                constants.ELITEMM_DESC_INFO[constants.ELITEMM_VP].get('min_score')):
                carry_num = 0  # 第1等级已经到vp了，不能自动发佣
                gen_ordercarry(referal_relationship, order_carry, OrderCarry.REFERAL_ORDER, carry_num)  # second level
                logger.info({
                    'action': 'task_update_second_level_ordercarry',
                    'order_no': sale_order.oid,
                    'desc': 'first level is more than vp',
                    'mm_linkid_mama': mm_linkid_mama.id,
                    'elitescore': mm_linkid_mama.elite_score,
                    'created': datetime.datetime.now(),
                })
                return
            low_mama = mm_linkid_mama
            while low_mama.referal_from == XiaoluMama.INDIRECT and low_mama.elite_score < \
                    constants.ELITEMM_DESC_INFO[constants.ELITEMM_VP].get('min_score'):

                relationship = ReferalRelationship.objects.filter(referal_to_mama_id=low_mama.id,
                                                                  created__lt=order_carry.created).first()
                # 实物商品把第2级的价格填入
                if relationship:
                    upper_mama = XiaoluMama.objects.filter(id=relationship.referal_from_mama_id,
                                                           status=XiaoluMama.EFFECT,
                                                           charge_status=XiaoluMama.CHARGED).first()
                    if upper_mama:
                        if upper_mama.is_elite_mama and upper_mama.elite_score < \
                                constants.ELITEMM_DESC_INFO[constants.ELITEMM_VP].get('min_score'):
                            diff = get_level_differential(model_product, upper_mama.elite_level,
                                                          mm_linkid_mama.elite_level)
                            carry_num = int(round((diff * sale_order.payment / sale_order.price) * 100))
                            logger.info({
                                'action': 'task_update_second_level_ordercarry',
                                'order_no': sale_order.oid,
                                'desc': 'referal order, upper mama < vp',
                                'mm_linkid_mama': low_mama.id,
                                'upper mama': upper_mama.id,
                                'carry_um': carry_num,
                                'created': datetime.datetime.now(),
                            })
                            gen_ordercarry(relationship, order_carry, OrderCarry.REFERAL_ORDER, carry_num)
                            if upper_mama.referal_from == XiaoluMama.DIRECT:
                                # 遇到direct，自动发佣就结束了
                                exchg_sale_order = ExchangeSaleOrder.objects.filter(
                                    order_oid=order_carry.order_id).first()
                                if not exchg_sale_order:
                                    exchg_record = ExchangeSaleOrder(order_oid=order_carry.order_id, has_exchanged=True,
                                                                     exchg_type=1, uni_key=order_carry.order_id)
                                    exchg_record.save()
                                else:
                                    exchg_sale_order.has_exchanged = True
                                    exchg_sale_order.exchg_type = 1
                                    exchg_sale_order.save()
                                logger.info({
                                    'action': 'task_update_second_level_ordercarry',
                                    'order_no': sale_order.oid,
                                    'desc': 'upper is direct, auto exchg over',
                                    'mm_linkid_mama': mm_linkid_mama.id,
                                    'upper mama': upper_mama.id,
                                    'created': datetime.datetime.now(),
                                })
                                break
                            else:
                                # 继续循环，找下一级别妈妈
                                low_mama = upper_mama
                        else:
                            # 上级的等级是vp或以上，不能自动发佣了，需要生成一个高级mama下属订单用来兑换,能兑换的金额就不是订单价，是下属妈妈的购买价了
                            carry_num = 0
                            gen_ordercarry(relationship, order_carry, OrderCarry.ADVANCED_MAMA_REFERAL_ORDER, carry_num)
                            from flashsale.pay.apis.v1.product import get_level_price_from_boutique_modelproduct
                            can_exchg_payment = get_level_price_from_boutique_modelproduct(model_product,
                                                                                           low_mama.elite_level)
                            # 为了便于存储，单位用分
                            can_exchg_payment = int(
                                round((can_exchg_payment * sale_order.payment / sale_order.price) * 100))
                            exchg_sale_order = ExchangeSaleOrder.objects.filter(order_oid=order_carry.order_id).first()
                            if not exchg_sale_order:
                                exchg_record = ExchangeSaleOrder(order_oid=order_carry.order_id,
                                                                 can_exchg_payment=can_exchg_payment,
                                                                 uni_key=order_carry.order_id)
                                exchg_record.save()
                            else:
                                exchg_sale_order.can_exchg_payment = can_exchg_payment
                                exchg_sale_order.save()
                            logger.info({
                                'action': 'task_update_second_level_ordercarry',
                                'order_no': sale_order.oid,
                                'desc': 'upper bigger than vp',
                                'mm_linkid_mama': mm_linkid_mama.id,
                                'upper mama': upper_mama.id,
                                'can_exchg_payment': can_exchg_payment,
                                'created': datetime.datetime.now(),
                            })
                            break
                    else:
                        logger.warn({
                            'action': 'task_update_second_level_ordercarry',
                            'order_no': sale_order.oid,
                            'desc': 'not found effect uppermama',
                            'low_mama': low_mama.id,
                            'uppermama': relationship.referal_from_mama_id,
                            'created': datetime.datetime.now(),
                        })
                        return

        elif model_product.is_boutique_coupon:
            # 券订单都是给上级兑换的，自己这一级金额没意义，不能为非0
            carry_num = 0
            gen_ordercarry(referal_relationship, order_carry, OrderCarry.REFERAL_ORDER, carry_num)  # second level
        else:
            carry_num = order_carry.carry_num * 0.2  # 20 percent carry
            gen_ordercarry(referal_relationship, order_carry, OrderCarry.REFERAL_ORDER, carry_num)  # second level
    else:
        logger.warn({
            'action': 'task_update_second_level_ordercarry',
            'order_no': sale_order.oid,
            'desc': 'not found model product',
            'mm_linkid_mama': mm_linkid_mama,
            'product_id': sale_order.item_id,
            'created': datetime.datetime.now(),
        })
        return


@app.task(serializer='pickle')
def task_update_ordercarry(mama_id, order, customer_pk, carry_amount, agency_level, carry_plan_name, via_app):
    """
    Whenever a sku order gets saved, trigger this task to update
    corresponding order_carry record.
    """
    logger.info({
        'action': 'task_update_ordercarry',
        'order_no': order.oid,
        'desc': 'task_update_ordercarry begin ',
        'mama_id': mama_id,
        'customer_pk': customer_pk,
        'carry_amount': carry_amount,
        'agency_level': agency_level,
        'carry_plan_name': carry_plan_name,
        'via_app': via_app,
    })
    status = OrderCarry.STAGING  # unpaid
    if order.need_send():
        status = OrderCarry.ESTIMATE
    elif order.is_confirmed():
        status = OrderCarry.CONFIRM
    elif order.is_canceled():
        status = OrderCarry.CANCEL

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
        logger.info({
            'action': 'task_update_ordercarry',
            'order_no': order.oid,
            'desc': 'order_carry exist',
            'mama_id': mama_id,
            'carry_num': carry_num,
            'agency_level': agency_level,
            'via_app': via_app,
            'carry_type': carry_type,
            'status': status,
        })

        update_fields = []

        if order_carry.status != status:
            order_carry.status = status
            update_fields.append('status')

        if update_fields:
            order_carry.save(update_fields=update_fields)
        return

    logger.info({
        'action': 'task_update_ordercarry',
        'order_no': order.oid,
        'desc': 'task_update_ordercarry save ',
        'mama_id': mama_id,
        'customer_pk': customer_pk,
        'carry_amount': carry_amount,
        'agency_level': agency_level,
        'carry_plan_name': carry_plan_name,
        'via_app': via_app,
        'carry_type': carry_type,
        'status': status,
    })
    try:
        order_value = round(order.payment * 100, 0)
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


# award_carry_array99 = [[0, 0], [1, 1500], [4, 2000], [8, 2500], [21, 3500], [41, 4500], [101, 5500]]
# award_carry_array188 = [[0, 0], [1, 3000], [4, 4000], [8, 5000], [21, 7000], [41, 9000], [101, 11000]]
# group_carry_array = [[0, 0], [50, 1000], [200, 1500], [500, 2000], [1000, 3000]]
#
#
# def get_award_carry_num(num, referal_type):
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
# def get_group_carry_num(num):
#    idx = 0
#    for entry in group_carry_array:
#        if num < entry[0]:
#            break
#        idx += 1
#    return group_carry_array[idx - 1][1]


@app.task()
def task_referal_update_awardcarry(relationship):
    # print "%s, mama_id: %s" % (get_cur_info(), relationship.referal_from_mama_id)

    if relationship.referal_type == XiaoluMama.ELITE:
        return

    from_mama_id = relationship.referal_from_mama_id
    to_mama_id = relationship.referal_to_mama_id
    carry_type = 1  # 直接推荐

    # uni_key = util_unikey.gen_awardcarry_unikey(from_mama_id, to_mama_id)
    uni_key = AwardCarry.gen_uni_key(to_mama_id, carry_type)

    rr_cnt = ReferalRelationship.objects.filter(referal_from_mama_id=from_mama_id,
                                                referal_type__gte=XiaoluMama.HALF).exclude(
        referal_to_mama_id=to_mama_id).count()
    rr_cnt += 1

    carry_num = utils.get_award_carry_num(rr_cnt, relationship.referal_type)

    status = 1
    carry_description = u'加入正式会员，奖金就会确认哦！'

    if relationship.is_confirmed():
        status = 2  # confirmed
        carry_description = util_description.get_awardcarry_description(carry_type)
    else:
        # 20161229 delete试用3的邀请奖励预计收益，只有正式的才有
        return

    award_carry = AwardCarry.objects.filter(uni_key=uni_key).first()
    if award_carry:
        from core.options import log_action, CHANGE, get_systemoa_user
        logmsg = 'mama_id:%s->%s|carry_num:%s->%s|status:%s->%s' % (
            award_carry.mama_id, from_mama_id, award_carry.carry_num, carry_num, award_carry.status, status)
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


@app.task()
def task_update_group_awardcarry(relationship):
    from flashsale.xiaolumm.models.models_fortune import AwardCarry, ReferalRelationship, GroupRelationship

    if relationship.referal_type == XiaoluMama.ELITE:
        return

    from_mama_id = relationship.referal_from_grandma_id
    to_mama_id = relationship.referal_to_mama_id
    carry_type = 2  # 团队推荐

    status = 1
    carry_description = u'%s推荐，加入正式会员，奖金就会确认哦！' % relationship.referal_from_mama_id

    if relationship.is_confirmed():
        status = 2  # confirmed
        carry_description = util_description.get_awardcarry_description(carry_type)
    else:
        # 20161229 delete试用3的邀请奖励预计收益，只有正式的才有
        return

    direct_referal_num = ReferalRelationship.objects.filter(referal_from_mama_id=from_mama_id,
                                                            referal_type__gte=XiaoluMama.HALF).count()
    group_referal_num = ReferalRelationship.objects.filter(referal_from_grandma_id=from_mama_id,
                                                           referal_type__gte=XiaoluMama.HALF).exclude(
        referal_to_mama_id=to_mama_id).count()
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
        logmsg = 'mama_id:%s->%s|carry_num:%s->%s|status:%s->%s' % (
            award_carry.mama_id, from_mama_id, award_carry.carry_num, carry_num, award_carry.status, status)
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


def validate_self_mama(mama, order_created_time):
    if (mama and mama.status == XiaoluMama.EFFECT and mama.charge_status == XiaoluMama.CHARGED and
            mama.charge_time and mama.charge_time < order_created_time and
            mama.renew_time and mama.renew_time > order_created_time):
        return True
    if (mama and mama.status == XiaoluMama.EFFECT and mama.charge_status == XiaoluMama.CHARGED and
                mama.last_renew_type == XiaoluMama.ELITE):
        return True
    return False


@app.task(serializer='pickle')
def task_order_trigger(sale_order):
    from flashsale.xiaolumm.models.models_fans import XlmmFans

    customer_id = sale_order.sale_trade.buyer_id
    customer = Customer.objects.get(id=customer_id)
    self_mama = None
    if customer.unionid:
        self_mama = XiaoluMama.objects.filter(openid=customer.unionid).first()

    mm_linkid_mama = XiaoluMama.objects.get_by_saletrade(sale_order.sale_trade)
    if self_mama and mm_linkid_mama and self_mama.id == mm_linkid_mama.id:
        mm_linkid_mama = None

    validata_mama = validate_self_mama(self_mama, sale_order.pay_time or sale_order.created)

    logger.info({
        'action': 'ordercarry',
        'order_no': sale_order.oid,
        'desc': 'task_order_trigger start ',
        'self_mama': self_mama,
        'validata_mama': validata_mama,
        'mm_linkid_mama': mm_linkid_mama,
        'created': datetime.datetime.now(),
        'order_created': sale_order.created,
    })

    if self_mama and not validata_mama:
        self_mama = None

    via_app = sale_order.sale_trade.is_paid_via_app()
    if self_mama:
        mm_linkid_mama = self_mama
    else:
        # customer itself is not a xiaolumama, then check
        # 1) if customer is a fan of a mama and the order is paid via app; or
        # 2) if customer is coming from a mama's share link;
        if via_app:
            # check fan's relationship
            fans_record = XlmmFans.objects.filter(fans_cusid=customer_id, created__lt=sale_order.created).first()
            if fans_record:
                mm_linkid_mama = XiaoluMama.objects.filter(id=fans_record.xlmm, status=XiaoluMama.EFFECT,
                                                           charge_status=XiaoluMama.CHARGED,
                                                           charge_time__lte=sale_order.created).first()

    if (not via_app) and (not mm_linkid_mama):
        # handle this case: order is not from app, and order does not have mm_linkid
        fans_record = XlmmFans.objects.filter(fans_cusid=customer_id, created__lt=sale_order.created).first()
        if fans_record:
            mm_linkid_mama = XiaoluMama.objects.filter(id=fans_record.xlmm, status=XiaoluMama.EFFECT,
                                                       charge_status=XiaoluMama.CHARGED,
                                                       charge_time__lte=sale_order.created).first()

    if not mm_linkid_mama:
        logger.info({
            'action': 'ordercarry',
            'order_no': sale_order.oid,
            'desc': 'no mm_linkid_mama ',
            'self_mama': self_mama,
            'validata_mama': validata_mama,
            'mm_linkid_mama': mm_linkid_mama,
            'created': datetime.datetime.now(),
        })
        return

    order_num = 1
    payment = sale_order.payment
    if sale_order.num > 1:
        order_num = sale_order.num
        payment = sale_order.payment / order_num

    from shopback.items.models import Product
    products = Product.objects.filter(id=sale_order.item_id)

    if products.count() <= 0:
        logger.info({
            'action': 'ordercarry',
            'order_no': sale_order.oid,
            'desc': 'not found product',
            'mm_linkid_mama': mm_linkid_mama,
            'product_id': sale_order.item_id,
            'payment': payment,
            'order_num': order_num,
            'created': datetime.datetime.now(),
        })
        return

    product = products[0]
    carry_scheme = mm_linkid_mama.get_Mama_Order_Rebeta_Scheme(product)
    agency_level = mm_linkid_mama.agencylevel
    # 20170331 will use 0401
    model_product = product.get_product_model()
    if model_product:
        if model_product.is_boutique_product:
            if mm_linkid_mama.is_elite_mama and mm_linkid_mama.elite_score < constants.ELITEMM_DESC_INFO[
                constants.ELITEMM_VP].get('min_score'):
                # 实物商品把第一级的价格填入
                diff = get_level_differential(model_product, mm_linkid_mama.elite_level, None)
                carry_amount = int(round((diff * sale_order.payment / sale_order.price) * 100))
                exchg_sale_order = ExchangeSaleOrder.objects.filter(order_oid=sale_order.oid).first()
                if not exchg_sale_order:
                    exchg_record = ExchangeSaleOrder(order_oid=sale_order.oid, auto_given_carry=True,
                                                     uni_key=sale_order.oid)
                    exchg_record.save()
                else:
                    exchg_sale_order.auto_given_carry = True
                    exchg_sale_order.save()
                logger.info({
                    'action': 'ordercarry',
                    'order_no': sale_order.oid,
                    'desc': 'first level auto given carry',
                    'mm_linkid_mama': mm_linkid_mama.id,
                    'carry_amount': carry_amount,
                    'elite_score': mm_linkid_mama.elite_score,
                    'order_num': order_num,
                    'created': datetime.datetime.now(),
                })
            else:
                carry_amount = 0
        elif model_product.is_boutique_coupon:
            # 券订单都是给上级兑换的，自己这一级没意义
            carry_amount = 0
        else:
            carry_amount = carry_scheme.calculate_carry(agency_level, payment) * 100 * order_num
    else:
        logger.warn({
            'action': 'ordercarry',
            'order_no': sale_order.oid,
            'desc': 'not found model product',
            'mm_linkid_mama': mm_linkid_mama,
            'product_id': sale_order.item_id,
            'payment': payment,
            'order_num': order_num,
            'created': datetime.datetime.now(),
        })
        return

    task_update_ordercarry(mm_linkid_mama.pk, sale_order, customer_id, carry_amount, agency_level,
                           carry_scheme.name, via_app)
    # task_update_ordercarry.apply_async(args=[mm_linkid_mama.pk, sale_order, customer_id, carry_amount, agency_level,
    #                             carry_scheme.name, via_app], countdown=1)


@app.task()
def carryrecord_update_xiaolumama_active_hasale(mmid):
    from flashsale.xiaolumm.models import CarryRecord
    from . import tasks_mama_fortune

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
        if mm_id > 0:
            tasks_mama_fortune.task_update_mamafortune_active_num(mm_id)
