# -*- encoding:utf-8 -*-

from celery.task import task
from flashsale.xiaolumm import util_description

import logging

logger = logging.getLogger('celery.handler')

from flashsale.pay.models_user import Customer
from flashsale.promotion.models_freesample import RedEnvelope
import sys, random


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    #return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


def get_application(event_id, openid=None, mobile=None):
    if openid:
        xls = XLSampleApply.objects.filter(event_id=event_id,user_openid=openid).order_by('-created')
        if xls.exists():
            return xls[0]
    if mobile:
        xls = XLSampleApply.objects.filter(event_id=event_id,mobile=mobile).order_by('-created')
        if xls.exists():
            return xls[0]
    return None


def gen_cash_value():
    return random.random()


def gen_envelope_type_value_pair(customer_id, event_id):
    records = RedEnvelope.objects.filter(customer_id=customer_id,event_id=event_id,type=1)
    if records.count() >= 9:
        return (0, gen_cash_value())

    if random.random() <= 0.5:
        # cash
        return (0, gen_cash_value())
    else:
        # card
        slots = [1,2,3,4,5,6,7,8,9]
        for item in records:
            slots.remove(item.value)
        return (1, random.choice(slots))
    

@task()
def task_generate_red_envelope(event_id, from_customer_id, customer):
    uni_key1 = '%s-%s' % (event_id, customer.id)

    # problem: how could we apply the red-envelope policy here, such that
    # first day people get all cards easier than people join later days??
    #
    # or, simply an easy policy: every envelope has 50% percent chance bing a card.

    # whoever invites my get a red envelope upon activating my application
    type,value = gen_envelope_type_value_pair(from_customer_id, event_id)
    envelope1 = RedEnvelope(customer_id=from_customer_id,event_id=event_id,uni_key=uni_key1,type=type,
                            value=value,friend_img=customer.thumbnail,friend_nick=customer.nick)
    envelope1.save()

    # when activating my application, i get one red envelope (with type 'card')
    type = 1 #card
    uni_key2 = 'self-'+uni_key1
    value = random.choices([1,2,3,4,5,6,7,8,9])
    envelope2 = RedEnvelope(customer_id=customer.id,event_id=event_id,uni_key=uni_key2,type=type,
                            vale=value, friend_img=customer.thumbnail,friend_nick=customer.nick)
    envelope2.save()


@task()
def task_activate_application(event_id, customer):
    openid, mobile = customer.openid, customer.mobile
    application = get_application(event_id, openid, mobile)
    from_customer_id = application.from_customer
    
    if application and not application.is_activated():
        application.status = XLSampleApply.ACTIVED
        application.save()
        
        task_generate_red_envelope.delay(event_id, from_customer_id, customer)

    

