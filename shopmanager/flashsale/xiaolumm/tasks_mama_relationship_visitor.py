# -*- encoding:utf-8 -*-

from django.db.models import F
from celery.task import task
from flashsale.xiaolumm import util_description

import logging

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_fortune import ReferalRelationship, GroupRelationship, UniqueVisitor
from flashsale.pay.models_user import Customer

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
def task_update_referal_relationship(from_mama_id, to_mama_id, customer_id):
    print "%s, mama_id: %s" % (get_cur_info(), from_mama_id)    


    customer = Customer.objects.get(pk=customer_id)
    records = ReferalRelationship.objects.filter(referal_to_mama_id=to_mama_id)
    if records.count() <= 0:
        record = ReferalRelationship(referal_from_mama_id=from_mama_id,
                                     referal_to_mama_id=to_mama_id,
                                     referal_to_mama_nick=customer.nick,
                                     referal_to_mama_img=customer.thumbnail)
        record.save()
    

@task()
def task_update_group_relationship(leader_mama_id, referal_relationship):
    print "%s, mama_id: %s" % (get_cur_info(), referal_relationship.referal_from_mama_id)
    
    records = GroupRelationship.objects.filter(member_mama_id=referal_relationship.referal_to_mama_id)
    if records.count() <= 0:
        record = GroupRelationship(leader_mama_id=leader_mama_id,
                                   referal_from_mama_id=referal_relationship.referal_from_mama_id,
                                   member_mama_id=referal_relationship.referal_to_mama_id,
                                   member_mama_nick=referal_relationship.referal_to_mama_nick,
                                   member_mama_img=referal_relationship.referal_to_mama_img)

        record.save()



from flashsale.xiaolumm.util_unikey import gen_uniquevisitor_unikey
from shopapp.weixin.options import get_unionid_by_openid
from flashsale.xiaolumm.models import XiaoluMama

@task()
def task_update_unique_visitor(mama_id, openid, appkey, click_time):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    if XiaoluMama.objects.filter(pk=mama_id).count() <= 0:
        return
    
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
    uni_key = gen_uniquevisitor_unikey(openid, date_field)

    try:
        visitor = UniqueVisitor(mama_id=mama_id,visitor_unionid=unionid,visitor_nick=nick,
                                visitor_img=img,uni_key=uni_key,date_field=date_field)
        visitor.save()
    except IntegrityError:
        logger.error("IntegrityError - UniqueVisitor | mama_id: %s, uni_key: %s" % (mama_id, uni_key))
        pass
        # visitor already visited a mama's link, ignoring.

    
        
    
                       
