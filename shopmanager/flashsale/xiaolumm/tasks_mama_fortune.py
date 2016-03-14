# -*- encoding:utf-8 -*-

from django.db.models import F, Sum
from celery.task import task

import logging

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_fortune import MamaFortune, ActiveValue, OrderCarry, ReferalRelationship
from flashsale.xiaolumm.models_fans import XlmmFans

import sys, datetime


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


def get_action_value(action_key):
    if action_key in action_dict:
        return action_dict[action_key]
    return {'carry_param': 0, 'cash_param': 0}


@task()
def task_increment_mamafortune_cash_and_carry(mama_id, amount, action_key):
    """
    动态更新小鹿妈妈的cash和carry，amount可以为负。
    """
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    if amount == 0:
        return

    print 'action_key:', action_key
    action_value = get_action_value(action_key)
    carry_param, cash_param = action_value['carry_param'], action_value['cash_param']
    carry_amount = amount * carry_param
    cash_amount = amount * cash_param

    mama_fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if mama_fortunes.count() > 0:
        mama_fortunes.update(carry_num=F('carry_num') + carry_amount, cash_num=F('cash_num') + cash_amount)
    else:
        mama_fortune = MamaFortune(mama_id=mama_id, carry_num=carry_amount, cash_num=cash_amount)
        mama_fortune.save()


@task()
def task_activevalue_update_mamafortune(mama_id):
    """
    更新妈妈activevalue
    """
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    
    today = datetime.datetime.now().date()
    effect_day = today - datetime.timedelta(30)
    
    values = ActiveValue.objects.filter(mama_id=mama_id, date_field__gt=effect_day, status=2).values('mama_id').annotate(value=Sum('value_num'))
    if values.count() <= 0:
        return
    
    value_num = values[0]["value"]
    
    mama_fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if mama_fortunes.count() > 0:
        mama_fortunes.update(active_value_num=value_num)
    else:
        mama_fortune = MamaFortune(mama_id=mama_id, active_value_num=value_num)
        mama_fortune.save()


@task()
def task_update_mamafortune_invite_num(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)    

    records = ReferalRelationship.objects.filter(referal_from_mama_id=mama_id)
    invite_num = records.count()
    
    mamas = MamaFortune.objects.filter(mama_id=mama_id)
    if mamas.count() > 0:
        mamas.update(invite_num=invite_num)
    else:
        mama = MamaFortune(mama_id=mama_id,invite_num=invite_num)
        mama.save()


@task()
def task_update_mamafortune_fans_num(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)    

    fans = XlmmFans.objects.filter(xlmm=mama_id)
    fans_num = fans.count()

    mamas = MamaFortune.objects.filter(mama_id=mama_id)
    if mamas.count() > 0:
        mamas.update(fans_num=fans_num)
    else:
        mama = MamaFortune(mama_id=mama_id,fans_num=fans_num)
        mama.save()
    
        
@task()
def task_update_mamafortune_order_num(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)    
    records = OrderCarry.objects.filter(mama_id=mama_id).exclude(status=3).values('contributor_id')
    order_num = records.count()
    
    mamas = MamaFortune.objects.filter(mama_id=mama_id)
    if mamas.count() > 0:
        mamas.update(order_num=order_num)
    else:
        mama = MamaFortune(mama_id=mama_id,order_num=order_num)
        mama.save()
                       
