#-*- encoding:utf8 -*-
import time
import datetime
from django.db.models import F,Sum
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
            


### 代理提成表 的task任务  每个月 8号执行 计算 订单成交额超过1000人民币的提成

from flashsale.clickrebeta.models import StatisticsShopping

@task()
def task_ThousandRebeta(date_from,date_to):

    xlmms = XiaoluMama.objects.filter(agencylevel=2,charge_status=XiaoluMama.CHARGED) # 过滤出已经接管的类别是2的代理
    for xlmm in xlmms:
        # 千元补贴
        shoppings = StatisticsShopping.objects.filter(linkid=xlmm.id, shoptime__range=(date_from,date_to))
#         # 过去一个月的成交额
        sum_wxorderamount = shoppings.aggregate(total_order_amount=Sum('wxorderamount')).get('total_order_amount') or 0

        if sum_wxorderamount > 100000: # 分单位
            # 写一条carry_log记录
            carry_log = CarryLog()
            carry_log.xlmm = xlmm.id
            carry_log.buyer_nick = xlmm.mobile
            carry_log.carry_type = CarryLog.CARRY_IN
            carry_log.log_type   = CarryLog.THOUSAND_REBETA
            carry_log.value      = sum_wxorderamount * 0.05   # 上个月的千元提成
            carry_log.buyer_nick = xlmm.mobile
            carry_log.status     = CarryLog.PENDING
            carry_log.save()


def get_pre_month(year,month):
    
    if month == 1:
        return year - 1, 12
    return year,month - 1
    
import calendar

@task
def task_Calc_Month_ThousRebeta(pre_month=1):
    
    today = datetime.datetime.now()
    year,month = today.year,today.month
    for m in range(pre_month):
        year,month = get_pre_month(year,month)
    
    month_range = calendar.monthrange(year,month)
    
    date_from = datetime.datetime(year,month,1,0,0,0)
    date_to   = datetime.datetime(year,month,month_range[1],23,59,59)
    
    task_ThousandRebeta(date_from,date_to)

### 代理提成表 的task任务   计算 每个妈妈的代理提成，上交的给推荐人的提成

@task()
def task_AgencySubsidy_MamaContribu(target_date):      # 每天 写入记录
    
    time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)  # 生成带时间的格式  开始时间
    time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)  # 停止时间

    xlmms = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED) # 过滤出已经接管的类别是2的代理
    for xlmm in xlmms:
        sub_xlmms = XiaoluMama.objects.filter(agencylevel=2,referal_from=xlmm.mobile)  # 找到的本代理的子代理
        sum_wxorderamount = 0  # 昨天订单总额
        for sub_xlmm in sub_xlmms:
            # 扣除记录
            sub_shoppings = StatisticsShopping.objects.filter(linkid=sub_xlmm.id, shoptime__range=(time_from,time_to))
            # 过滤出子代理昨天的订单
            sum_wxorderamount = sub_shoppings.aggregate(total_order_amount=Sum('wxorderamount')).get('total_order_amount') or 0
            
            commission = sum_wxorderamount * 0.05
            if commission == 0:  # 如果订单总额是0则不做记录
                continue
            
#             carry_log_sub = CarryLog()
#             carry_log_sub.xlmm       = sub_xlmm.id  # 锁定子代理 :每个子代理都生成一个分成值  妈妈贡献的ID 是子代理的ID
#             carry_log_sub.order_num  = xlmm.id       # 这里写的是 上级代理的ID
#             carry_log_sub.buyer_nick = sub_xlmm.mobile  # 这里写的是子代理的电话号码
#             carry_log_sub.carry_type = CarryLog.CARRY_OUT
#             carry_log_sub.log_type   = CarryLog.MAMA_CONTRIBU  # 妈妈贡献类型
#             carry_log_sub.value      = commission  # 上个月给本代理的分成
#             carry_log_sub.carry_date = target_date
#             carry_log_sub.status     = CarryLog.PENDING
#             carry_log_sub.save()

            carry_log_f  = CarryLog()
            carry_log_f.xlmm       = xlmm.id  # 锁定本代理
            carry_log_f.order_num  = sub_xlmm.id      # 这里写的是子代理的ID
            carry_log_f.buyer_nick = xlmm.mobile
            carry_log_f.carry_type = CarryLog.CARRY_IN
            carry_log_f.log_type   = CarryLog.AGENCY_SUBSIDY  # 子代理给的补贴类型
            carry_log_f.value      = commission  # 上个月给本代理的分成
            carry_log_f.carry_date = target_date
            carry_log_f.status     = CarryLog.PENDING
            carry_log_f.save()

@task
def task_Calc_Agency_Contribu(pre_day=1):
    
    pre_date = datetime.date.today() - datetime.timedelta(days=pre_day)
    
    task_AgencySubsidy_MamaContribu(pre_date)
    
    