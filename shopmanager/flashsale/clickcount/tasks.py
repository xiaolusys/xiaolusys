# -*- encoding:utf8 -*-
import datetime
from django.db.models import F
from celery.task import task

from flashsale.xiaolumm.models import XiaoluMama, Clicks, CarryLog, AgencyLevel
from .models import ClickCount
import logging

__author__ = 'linjie'

logger = logging.getLogger('celery.handler')

@task()
def task_Push_ClickCount_To_MamaCash(target_date):
    """ 计算每日妈妈点击数现金提成，并更新到妈妈钱包账户"""
    from flashsale.clickrebeta.models import StatisticsShopping
    
    carry_no = int(target_date.strftime('%y%m%d'))
    time_from = datetime.datetime(target_date.year,target_date.month,target_date.day,0,0,0)
    time_end = datetime.datetime(target_date.year,target_date.month,target_date.day,23,59,59)
    
    mm_clickcounts = ClickCount.objects.filter(date=target_date,valid_num__gt=0)
    for mm_cc in mm_clickcounts:
        xlmms = XiaoluMama.objects.filter(id=mm_cc.linkid)
        if xlmms.count() == 0:
            continue
        
        xlmm = xlmms[0]
        buyercount = StatisticsShopping.objects.filter(linkid=xlmm.id,
                            shoptime__range=(time_from, time_end)).values('openid').distinct().count()
                            
        agency_level = AgencyLevel.objects.get(id=xlmm.agencylevel)
        click_price  = agency_level.get_Click_Price(buyercount)
        click_rebeta = mm_cc.valid_num * click_price 
        
        c_log,state = CarryLog.objects.get_or_create(xlmm=xlmm.id,
                                                     order_num=carry_no,
                                                     log_type=CarryLog.CLICK_REBETA)
        if not state or mm_cc.valid_num == 0:
            continue

        c_log.value = click_rebeta
        c_log.carry_type = CarryLog.CARRY_IN
        c_log.status = CarryLog.CONFIRMED
        c_log.save()
        
        urows = XiaoluMama.objects.filter(id=mm_cc.linkid).update(pending=F('pending') + click_rebeta)
        if urows == 0:
            raise Exception(u'小鹿妈妈订单提成返现更新异常:%s,%s'%(xlmm.id,urows))


@task(max_retry=3, default_retry_delay=5)
def task_Record_User_Click(pre_day=1):
    """ 计算每日妈妈点击数，汇总"""
    pre_date = datetime.date.today() - datetime.timedelta(days=pre_day)
    time_from = datetime.datetime(pre_date.year, pre_date.month, pre_date.day)  # 生成带时间的格式  开始时间
    time_to = datetime.datetime(pre_date.year, pre_date.month, pre_date.day, 23, 59, 59)  # 停止时间

    xiaolumamas = XiaoluMama.objects.all()  # 所有小鹿妈妈们

    for xiaolumama in xiaolumamas:  #
        clicks = Clicks.objects.filter(created__gt=time_from, created__lt=time_to,
                                       linkid=xiaolumama.id)  # 根据代理的id过滤出点击表中属于该代理的点击
        
        click_num = clicks.count()  # 点击数量
        user_num  = clicks.values('openid').distinct().count()  # 点击人数
        valid_num = clicks.filter(isvalid=True).values('openid').distinct().count()
        
        clickcount, state = ClickCount.objects.get_or_create(date=pre_date,
                                                             linkid=xiaolumama.id)  # 在点击统计表中找今天的记录 如果 有number和小鹿妈妈的id相等的 说明已经该记录已经统计过了
        
        clickcount.weikefu = xiaolumama.weikefu  # 写名字到统计表
        clickcount.username = xiaolumama.manager  # 接管人
        clickcount.click_num = click_num
        clickcount.mobile = xiaolumama.mobile
        clickcount.user_num = user_num
        clickcount.valid_num = valid_num
        clickcount.save()
    
    #update xlmm click rebeta
    task_Push_ClickCount_To_MamaCash(pre_date)
    


