# -*- encoding:utf-8 -*-

from celery.task import task
from django.db.models import F, Sum
from flashsale.xiaolumm.models_fortune import DailyStats, UniqueVisitor, OrderCarry, CarryRecord
from flashsale.xiaolumm import util_unikey
import datetime

import sys

def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    #return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


def create_dailystats_with_integrity(mama_id, date_field, uni_key, **kwargs):
    try:
        stats = DailyStats(mama_id=mama_id, date_field=date_field, uni_key=uni_key, **kwargs)
        stats.save()
    except IntegrityError as e:
        logger.error("IntegrityError - DailyStats | mama_id: %s, uni_key: %s, params: %s" % (mama_id, uni_key, kwargs))
        DailyStats.objects.filter(mama_id=mama_id, date_field=date_field, uni_key=uni_key).update(**kwargs)


@task()
def task_confirm_previous_dailystats(mama_id, today_date_field, num_days):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    end_date_field = today_date_field - datetime.timedelta(days=num_days)
    records = DailyStats.objects.filter(mama_id=mama_id, date_field__lte=end_date_field, status=1).order_by('-date_field')[:7]
    if records.count() <= 0:
        return
    
    for stats in records:
        date_field = stats.date_field
        today_visitor_num = UniqueVisitor.objects.filter(mama_id=mama_id,date_field=date_field).count()
        stats.today_visitor_num = today_visitor_num

        today_order_num = OrderCarry.objects.filter(mama_id=mama_id, date_field=date_field).count()
        stats.today_order_num = today_order_num

        carrys = CarryRecord.objects.filter(mama_id=mama_id, date_field=date_field).exclude(status=3).values('date_field').annotate(carry=Sum('carry_num'))
        today_carry_num = 0
        if len(carrys) > 0:
            if carrys[0]["date_field"] == date_field:
                today_carry_num = carrys[0]["carry"] 

    
        stats.today_carry_num = today_carry_num
        stats.status = 2 #confirm
        stats.save()


@task()
def task_visitor_increment_dailystats(mama_id, date_field):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    uni_key = util_unikey.gen_dailystats_unikey(mama_id, date_field)
    records = DailyStats.objects.filter(uni_key=uni_key)
    
    if records.count() <= 0:
        create_dailystats_with_integrity(mama_id, date_field, uni_key, today_carry_num=1)
        
        task_confirm_previous_dailystats.s(mama_id, date_field, 2)()
    else:
        records.update(today_visitor_num=F('today_visitor_num')+1)


    
@task()
def task_carryrecord_update_dailystats(mama_id, date_field):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    uni_key = util_unikey.gen_dailystats_unikey(mama_id, date_field)
    records = DailyStats.objects.filter(uni_key=uni_key)
    carrys = CarryRecord.objects.filter(mama_id=mama_id, date_field=date_field).exclude(status=3).values('date_field').annotate(carry=Sum('carry_num'))
    
    today_carry_num = 0
    if len(carrys) > 0:
        if carrys[0]["date_field"] == date_field:
            today_carry_num = carrys[0]["carry"] 

    if records.count() <= 0:
        create_dailystats_with_integrity(mama_id, date_field, uni_key, today_carry_num=today_carry_num)
        task_confirm_previous_dailystats.s(mama_id, date_field, 2)()
    else:
        stats = records[0]
        stats.today_carry_num = today_carry_num
        stats.save()
    


@task()
def task_ordercarry_increment_dailystats(mama_id, date_field):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    uni_key = util_unikey.gen_dailystats_unikey(mama_id, date_field)
    records = DailyStats.objects.filter(uni_key=uni_key)
    #today_order_num = OrderCarry.objects.filter(mama_id=mama_id, date_field=date_field).count()
    
    if records.count() <= 0:
        create_dailystats_with_integrity(mama_id, date_field, uni_key, today_order_num=1)
        task_confirm_previous_dailystats.s(mama_id, date_field, 2)()
    else:
        records.update(today_order_num=F('today_order_num')+1)

    

        
    
