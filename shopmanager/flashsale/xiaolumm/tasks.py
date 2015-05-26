#-*- encoding:utf8 -*-
import time
import datetime
from django.db.models import F
from django.conf import settings
from celery.task import task

from flashsale.xiaolumm.models import Clicks,XiaoluMama,CarryLog

__author__ = 'meixqhi'

@task()
def task_Create_Click_Record(xlmmid,openid,click_time):
    
    xlmmid = int(xlmmid)
    
    today = datetime.datetime.now()
    tf = datetime.datetime(today.year,today.month,today.day,0,0,0)
    tt = datetime.datetime(today.year,today.month,today.day,23,59,59)
    
    isvalid = False
    clicks = Clicks.objects.filter(openid=openid,created__range=(tf,tt))
    click_linkids = set([l.get('linkid') for l in clicks.values('linkid').distinct()])
    click_count   = len(click_linkids)
    xlmms = XiaoluMama.objects.filter(id=xlmmid)
    
    if click_count < Clicks.CLICK_DAY_LIMIT and xlmms.count() > 0 and xlmmid not in click_linkids:
        isvalid = True
        
    Clicks.objects.create(linkid=xlmmid,openid=openid,isvalid=isvalid,click_time=click_time)
    
    
@task()
def task_Pull_Pending_Carry(day_ago=7):
    
    date_to  = datetime.datetime.now().date()
    date_from    = date_to - datetime.timedelta(days=day_ago)
    
    c_logs = CarryLog.objects.filter(carry_date__range=(date_from,date_to),
                                     log_type__in=(CarryLog.ORDER_REBETA,),#CarryLog.CLICK_REBETA
                                     status=CarryLog.CONFIRMED)

    for cl in c_logs:
        #重新计算pre_date之前订单金额，取消退款订单提成
        
        #将carrylog里的金额更新到最新，然后将金额写入mm的钱包帐户
        xlmms = XiaoluMama.objects.filter(id=cl.xlmm)
        
        if cl.carry_date == datetime.datetime(2015,5,15).date():
            urows = xlmms.update(cash=F('cash') - cl.value)
        else:
            urows = xlmms.update(pending=F('pending') - cl.value)
        
        if urows > 0:
            cl.status = CarryLog.PENDING
            cl.save()

@task()
def task_Push_Pending_Carry_Cash(day_ago=7, xlmm_id=None):
    
    from flashsale.mmexam.models import Result
    
    pre_date = datetime.date.today() - datetime.timedelta(days=day_ago)
    
    c_logs = CarryLog.objects.filter(log_type__in=(CarryLog.ORDER_REBETA,
                                                   CarryLog.CLICK_REBETA), 
                                     status=CarryLog.PENDING)\
                                     .exclude(carry_date__gt=pre_date,log_type=CarryLog.ORDER_REBETA)
    
    if xlmm_id:
        xlmm  = XiaoluMama.objects.get(id=xlmm_id)
        c_logs = c_logs.filter(xlmm=xlmm.id)
        
    for cl in c_logs:
        
        xlmms = XiaoluMama.objects.filter(id=cl.xlmm)
        if xlmms.count() == 0:
            continue
        
        xlmm = xlmms[0]
        #是否考试通过
        results = Result.objects.filter(daili_user=xlmm.openid)
        if results.count() == 0 or not results[0].is_Exam_Funished():
            continue
        #重新计算pre_date之前订单金额，取消退款订单提成
        
        #将carrylog里的金额更新到最新，然后将金额写入mm的钱包帐户
        
        if cl.carry_type != CarryLog.CARRY_IN:
            continue
        
        urows = xlmms.update(cash=F('cash') + cl.value, pending=F('pending') - cl.value)
        if urows > 0:
            cl.status = CarryLog.CONFIRMED
            cl.save()
            




### 代理提成表 的task任务  每个月 8号执行 计算 每个妈妈的代理提成，上交的给推荐人提成，订单成交额超过1000人民币的提成

from flashsale.clickrebeta.models import StatisticsShopping
from flashsale.xiaolumm.models import Clicks,XiaoluMama,CarryLog,CarryLogTest

@task()
def task_ThousandRebeta_AgencySubsidy_MamaContribu():
    today = datetime.datetime.today()

    if today.month == 1:
        time_from = datetime.datetime(today.year-1, 12, 1, 0, 0, 0)  # 上个月初
        time_to = datetime.datetime(today.year, today.month, 1, 0, 0, 0)  # 这个月初
    else:
        time_from = datetime.datetime(today.year, today.month, 1, 0, 0, 0)  # 上个月初
        time_to = datetime.datetime(today.year, today.month, 28, 0, 0, 0)  # 这个月初


    xlmms = XiaoluMama.objects.all()
    for xlmm in xlmms:
        # 千元补贴
        sum_wxorderamount = 0
        shoppings = StatisticsShopping.objects.filter(linkid=xlmm.id, shoptime__gt=time_from, shoptime__lt=time_to)
        # 过去一个月的成交额
        for shopping in shoppings:
            sum_wxorderamount = sum_wxorderamount + shopping.wxorderamount
        if sum_wxorderamount > 100000: # 分单位
            # 写一条carry_log记录
            carry_log = CarryLogTest()
            carry_log.xlmm = xlmm.id
            carry_log.buyer_nick = xlmm.mobile
            print '千元提成', xlmm.mobile
            carry_log.carry_type = CarryLogTest.CARRY_IN
            carry_log.log_type = CarryLogTest.THOUSAND_REBETA
            carry_log.value = (sum_wxorderamount*5)/100   # 上个月的千元提成
            carry_log.save()

        sub_xlmms = XiaoluMama.objects.filter(referal_from=xlmm.mobile)  # 找到的本代理的子代理
        sub_sum_wxorderamount = 0  # 上个月子代理的总成交额
        for sub_xlmm in sub_xlmms:
            # 扣除记录
            sub_shoppings = StatisticsShopping.objects.filter(linkid=sub_xlmm.id, shoptime__gt=time_from, shoptime__lt=time_to)
            for sub_shopping in sub_shoppings:
                sub_sum_wxorderamount = sub_sum_wxorderamount + sub_shopping.wxorderamount
            carry_log_sub = CarryLogTest()
            carry_log_sub.xlmm = sub_xlmm.id  # 锁定子代理 :每个子代理都生成一个分成值  妈妈贡献的ID 是子代理的ID
            carry_log_sub.buyer_nick = sub_xlmm.mobile  # 这里写的是子代理的电话号码
            print '妈妈贡献', (sub_xlmm.mobile)
            carry_log_sub.carry_type = CarryLogTest.CARRY_OUT
            carry_log_sub.log_type = CarryLogTest.MAMA_CONTRIBU  # 妈妈贡献类型
            carry_log_sub.value = (sub_sum_wxorderamount*5)/100  # 上个月给本代理的分成
            print((sub_sum_wxorderamount*5)/100)
            carry_log_sub.save()

            carry_log_f = CarryLogTest()
            carry_log_f.xlmm = xlmm.id  # 锁定本代理
            carry_log_f.buyer_nick = xlmm.mobile
            print '代理补贴', (xlmm.mobile)
            carry_log_f.carry_type = CarryLogTest.CARRY_IN
            carry_log_f.log_type = CarryLogTest.AGENCY_SUBSIDY  # 子代理给的补贴类型
            carry_log_f.value = (sub_sum_wxorderamount*5)/100  # 上个月给本代理的分成
            carry_log_f.save()
