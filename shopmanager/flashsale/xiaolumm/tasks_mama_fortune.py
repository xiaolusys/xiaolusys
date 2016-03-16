# -*- encoding:utf-8 -*-

from django.db.models import F, Sum
from celery.task import task

import logging

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_fortune import MamaFortune, ActiveValue, OrderCarry, ReferalRelationship, CarryRecord, GroupRelationship, MAMA_FORTUNE_HISTORY_LAST_DAY
from flashsale.xiaolumm.models import CashOut
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


@task()
def task_xiaolumama_update_mamafortune(mama_id, cash):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    
    fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if fortunes.count() > 0:
        fortune = fortunes[0]
        fortune.history_confirmed = cash
        fortune.save()
    else:
        fortune = MamaFortune(mama_id=mama_id,history_confirmed=cash)
        fortune.save()
        

@task()
def task_cashout_update_mamafortune(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    cashouts = CashOut.objects.filter(xlmm=mama_id, status=CashOut.APPROVED).values('status').annotate(total=Sum('value'))

    cashout_confirmed = 0
    for entry in cashouts:
        if entry["status"] == CashOut.APPROVED: # confirmed
            cashout_confirmed = entry["total"]
    
    fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if fortunes.count() > 0:
        fortune = fortunes[0]
        if fortune.carry_cashout != cashout_confirmed:
            fortune.carry_cashout = cashout_confirmed
            fortune.save()
    else:
        fortune = MamaFortune(mama_id=mama_id,carry_cashout=cashout_confirmed)
        fortune.save()
    



@task()
def task_carryrecord_update_mamafortune(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    
    carrys = CarryRecord.objects.filter(mama_id=mama_id, date_field__gt=MAMA_FORTUNE_HISTORY_LAST_DAY).values('status').annotate(carry=Sum('carry_num'))
    carry_pending,carry_confirmed,carry_cashout = 0,0,0
    for entry in carrys:
        if entry["status"] == 1: # pending
            carry_pending = entry["carry"]
        elif entry["status"] == 2: # confirmed
            carry_confirmed = entry["carry"]
    
    fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if fortunes.count() > 0:
        fortune = fortunes[0]
        flag = False
        if fortune.carry_pending != carry_pending:
            fortune.carry_pending   = carry_pending
            flag = True
        if fortune.carry_confirmed != carry_confirmed:
            fortune.carry_confirmed = carry_confirmed
            flag = True
        if flag:
            fortune.save()
    else:
        fortune = MamaFortune(mama_id=mama_id,carry_pending=carry_pending,
                              carry_confirmed=carry_confirmed)
        fortune.save()
        

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
        mama = mamas[0]
        if mama.invite_num != invite_num:
            mama.invite_num=invite_num
            mama.save()
    else:
        mama = MamaFortune(mama_id=mama_id,invite_num=invite_num)
        mama.save()


@task()
def task_update_mamafortune_mama_level(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)    

    records = ReferalRelationship.objects.filter(referal_from_mama_id=mama_id)
    invite_num = records.count()

    groups = GroupRelationship.objects.filter(leader_mama_id=mama_id)
    group_num = groups.count()

    total = invite_num + group_num

    level = 0
    if invite_num >= 15 or total >= 50:
        level = 1
    if total >= 200:
        level = 2
    if total >= 500:
        level = 3
    if total >= 1000:
        level = 4
    
    mamas = MamaFortune.objects.filter(mama_id=mama_id)
    if mamas.count() > 0:
        mama = mamas[0]
        if mama.mama_level != level:
            mama.mama_level = level
            mama.save()
    else:
        mama = MamaFortune(mama_id=mama_id,mama_level=level)
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
                       
