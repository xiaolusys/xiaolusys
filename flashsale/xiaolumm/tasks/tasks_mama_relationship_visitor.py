# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import sys
from django.db import IntegrityError

from flashsale.xiaolumm.models.models_fortune import ReferalRelationship, GroupRelationship, UniqueVisitor
from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama, PotentialMama
from flashsale.xiaolumm import utils

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


@app.task()
def task_update_referal_relationship(sale_order):
    sale_trade = sale_order.sale_trade
    customer_id = sale_trade.buyer_id
    customer = Customer.objects.get(pk=customer_id)

    logger.warn("id=%s, oid=%s" % (sale_order.id, sale_order.oid))
    referal_type = XiaoluMama.SCAN
    if sale_order.is_1_deposit():
        referal_type = XiaoluMama.TRIAL
    elif sale_order.is_99_deposit():
        referal_type = XiaoluMama.HALF
    elif sale_order.is_188_deposit():
        referal_type = XiaoluMama.FULL
    else:
        logger.warn("id=%s, oid=%s, is not deposit,return" % (sale_order.id, sale_order.oid))
        return
    
    mama = XiaoluMama.objects.filter(openid=customer.unionid).first()
    if not mama:  # 当前订单用户不是代理　则不做处理
        logger.warn("id=%s, oid=%s, order user is not mama, return" % (sale_order.id, sale_order.oid))
        return

    # mama status is taken care of by some other logic, so we ignore.
    # mamas.update(status=XiaoluMama.EFFECT, progress=XiaoluMama.PAY, charge_status=XiaoluMama.CHARGED)
    to_mama_id = mama.id  # 被推荐的妈妈id

    mm_linkid = utils.get_sale_order_mama_id(sale_order)
    if (not mm_linkid) or (mm_linkid == mama.id):  # 从订单没有找到推荐记录或者点击自己链接支付的则先找潜在妈妈  如果潜在妈妈 没有 则 找粉丝记录
        potential = PotentialMama.objects.filter(potential_mama=mama.id).first()
        if potential and (potential.referal_mama != mama.id):
            mm_linkid = potential.referal_mama  # 推荐人妈妈id
        if (not mm_linkid) or (mm_linkid == mama.id):
            fans = XlmmFans.objects.filter(fans_cusid=customer.id).first()
            mm_linkid = fans.xlmm if fans else 0

    referal_mm = XiaoluMama.objects.filter(id=mm_linkid).first()

    if not referal_mm:  # 没有推荐人　
        logger.warn("to_mama_id=%s, referal_mm none,return" % to_mama_id)
        return
    if not referal_mm.is_relationshipable():  # 可以记录
        logger.warn("mm_linkid=%s, to_mama_id=%s, referal mm is not relationshipable" % ( mm_linkid, to_mama_id))
        return
    if referal_mm.id == mama.id:  # 如果推荐人 是自己 则 return
        logger.warn("mm_linkid=%s, to_mama_id=%s, mama and referal mm is same" % ( mm_linkid, to_mama_id))
        return

    referal_type = 0
    if sale_order.is_99_deposit():
        referal_type = XiaoluMama.HALF
    elif sale_order.is_188_deposit():
        referal_type = XiaoluMama.FULL
    else:
        logger.warn(" mm_linkid=%s, to_mama_id=%s, saleorder is not 99/188 deposit" % (mm_linkid, to_mama_id))
        return
        
    mm_linkid = referal_mm.id
    logger.warn("%s: mm_linkid=%s, to_mama_id=%s" % (get_cur_info(), mm_linkid, to_mama_id))

    record = ReferalRelationship.objects.filter(referal_to_mama_id=to_mama_id).first()
    if record:
        update_fields = []
        if record.referal_type <= referal_type:
            record.referal_type = referal_type
            update_fields.append('referal_type')
            
            # only when we upgrade referal_type, we update oid.
            if record.order_id != sale_order.oid:
                record.order_id = sale_order.oid
                update_fields.append('order_id')
            if record.referal_from_mama_id != mm_linkid:
                record.referal_from_mama_id = mm_linkid
                update_fields.append('referal_from_mama_id')

                referal_from_grandma_id = 0
                parentship = ReferalRelationship.objects.filter(referal_to_mama_id=mm_linkid).first()
                if parentship:
                    referal_from_grandma_id = parentship.referal_from_mama_id
               
                if record.referal_from_grandma_id != referal_from_grandma_id:
                    record.referal_from_grandma_id = referal_from_grandma_id
                    update_fields.append('referal_from_grandma_id')
                    
            record.save(update_fields=update_fields)
        return
    parentship = ReferalRelationship.objects.filter(referal_to_mama_id=mm_linkid).first()
    record = ReferalRelationship(referal_from_grandma_id=parentship.referal_from_mama_id if parentship else 0,
                                 referal_from_mama_id=mm_linkid,
                                 referal_to_mama_id=to_mama_id,
                                 referal_to_mama_nick=customer.nick,
                                 referal_to_mama_img=customer.thumbnail,
                                 referal_type=referal_type,
                                 order_id=sale_order.oid)
    record.save()


@app.task()
def task_update_group_relationship(leader_mama_id, referal_relationship):

    records = GroupRelationship.objects.filter(member_mama_id=referal_relationship.referal_to_mama_id)
    if records.count() <= 0:
        record = GroupRelationship(leader_mama_id=leader_mama_id,
                                   referal_from_mama_id=referal_relationship.referal_from_mama_id,
                                   member_mama_id=referal_relationship.referal_to_mama_id,
                                   member_mama_nick=referal_relationship.referal_to_mama_nick,
                                   member_mama_img=referal_relationship.referal_to_mama_img,
                                   referal_type=referal_relationship.referal_type,
                                   status=referal_relationship.status)

        record.save()


from flashsale.xiaolumm.util_unikey import gen_uniquevisitor_unikey
from shopapp.weixin.options import get_unionid_by_openid


@app.task()
def task_update_unique_visitor(mama_id, openid, appkey, click_time):

    if XiaoluMama.objects.filter(pk=mama_id).count() <= 0:
        return

    nick, img = '', ''
    unionid = get_unionid_by_openid(openid, appkey)
    if unionid:
        from shopapp.weixin.models_base import WeixinUserInfo
        userinfo = WeixinUserInfo.objects.filter(unionid=unionid).first()
        if userinfo:
            nick, img = userinfo.nick, userinfo.thumbnail
    else:
        # if no unionid exists, then use openid
        unionid = openid

    date_field = click_time.date()
    uni_key = gen_uniquevisitor_unikey(openid, date_field)

    try:
        visitor = UniqueVisitor(mama_id=mama_id, visitor_unionid=unionid, visitor_nick=nick,
                                visitor_img=img, uni_key=uni_key, date_field=date_field)
        visitor.save()
    except IntegrityError:
        logger.warn("IntegrityError - UniqueVisitor | mama_id: %s, uni_key: %s" % (mama_id, uni_key))
        pass
        # visitor already visited a mama's link, ignoring.


from flashsale.promotion.models import AppDownloadRecord
from flashsale.xiaolumm.models.models_fans import XlmmFans


@app.task()
def task_login_activate_appdownloadrecord(user):
    customer = Customer.objects.normal_customer.filter(user=user).first()
    if not customer:
        return

    fan = XlmmFans.objects.filter(fans_cusid=customer.id).first()
    if fan:
        # already a fan
        logger.warn("activate appdownload: already a fan")
        return

    self_mama = None
    if customer.unionid:
        self_mama = XiaoluMama.objects.filter(openid=customer.unionid,status=XiaoluMama.EFFECT,charge_status=XiaoluMama.CHARGED,last_renew_type__gt=XiaoluMama.TRIAL).first()
        
    if self_mama:
        # XiaoluMama can't be a fan of any others.
        logger.warn("activate appdownload: already a mama")
        return
    
    unionid = customer.unionid
    mobile = customer.mobile

    records = None
    if unionid:
        records = AppDownloadRecord.objects.filter(unionid=unionid, status=AppDownloadRecord.UNUSE).order_by('-modified')
        record = records.first()
        if record:
            record.status = AppDownloadRecord.USED
            record.save()
            logger.warn("task_login_activate_appdownloadrecord|customer_id:%s, record_id:%s" % (customer.id, record.id))
            return
    
    if mobile and len(mobile) == 11:
        records = AppDownloadRecord.objects.filter(mobile=mobile, status=AppDownloadRecord.UNUSE).order_by('-modified')
        record = records.first()
        if record:
            record.status = AppDownloadRecord.USED
            record.save()
            logger.warn("task_login_activate_appdownloadrecord|customer_id:%s, record_id:%s" % (customer.id, record.id))

    
 
@app.task()
def task_login_create_appdownloadrecord(user):
    customer = Customer.objects.normal_customer.filter(user=user).first()
    if not customer:
        return

    fan = XlmmFans.objects.filter(fans_cusid=customer.id).first()
    if not fan:
        return

    mobile = customer.mobile
    if len(mobile) != 11:
        return

    mobile_customer = Customer.objects.normal_customer.filter(mobile=mobile,unionid='').first()
    if not mobile_customer:
        return

    from_customer = fan.xlmm_cusid
    record = AppDownloadRecord.objects.filter(from_customer=from_customer,mobile=mobile).first()
    if record:
        return
    
    record = AppDownloadRecord(from_customer=from_customer,status=AppDownloadRecord.USED,mobile=mobile)
    logger.warn("task_login_create_appdownloadrecord|from_customer:%s, mobile:%s" % (from_customer, mobile))
    record.save()
    

    
    

    
