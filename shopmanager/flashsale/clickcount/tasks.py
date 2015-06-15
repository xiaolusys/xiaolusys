# -*- encoding:utf8 -*-
import datetime
from django.db.models import F, Sum
from celery.task import task

from flashsale.xiaolumm.models import XiaoluMama, Clicks, CarryLog, AgencyLevel
from .models import ClickCount, WeekCount
import logging

__author__ = 'linjie'

logger = logging.getLogger('celery.handler')

CLICK_ACTIVE_START_TIME = datetime.datetime(2015,6,15,10)
CLICK_MAX_LIMIT_DATE  = datetime.date(2015,6,5)

def task_patch_mamacash_61():
    
    time_end = datetime.datetime(2015,6,1,23,59,59)
    carry_no = int(time_end.strftime('%y%m%d'))
    
    total_rebeta = 0
    mm_clickcounts = ClickCount.objects.filter(date=time_end.date(),valid_num__gt=0)
    for mm_cc in mm_clickcounts:
        xlmms = XiaoluMama.objects.filter(id=mm_cc.linkid)
        if xlmms.count() == 0:
            continue
        
        xlmm = xlmms[0]
                            
        agency_levels = AgencyLevel.objects.filter(id=xlmm.agencylevel)
        if agency_levels.count() == 0:
            continue
        agency_level = agency_levels[0]
        if agency_level.id != 2:
            continue
        
        click_qs = Clicks.objects.filter(linkid=mm_cc.linkid,click_time__range=(CLICK_ACTIVE_START_TIME,time_end),isvalid=True)
        ten_click_num = click_qs.values('openid').distinct().count()
        ten_click_price = 30
        
        click_rebeta = ten_click_num * ten_click_price
        if mm_cc.valid_num == 0 or click_rebeta <= 0:
            continue
        
        c_log,state = CarryLog.objects.get_or_create(xlmm=xlmm.id,
                                                      order_num=carry_no,
                                                      log_type=CarryLog.CLICK_REBETA)
#         
        c_log.value = c_log.value + click_rebeta
        c_log.save()
        
        urows = xlmms.update(cash=F('cash') + click_rebeta)
        total_rebeta += click_rebeta
    
    print 'debug total_rebeta:',total_rebeta


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
                            
        click_price  = xlmm.get_Mama_Click_Price(buyercount)
        click_num    = mm_cc.valid_num
        
        #设置最高有效最高点击上限
        if time_from.date() >= CLICK_MAX_LIMIT_DATE:
            max_click_count = xlmm.get_Mama_Max_Valid_Clickcount(buyercount)
            click_num = min(max_click_count,click_num )
        
        click_rebeta = click_num  * click_price
        
#         ten_click_num   = 0
#         ten_click_price = 0
#         if CLICK_ACTIVE_START_TIME.date() == time_from.date():
#             click_qs = Clicks.objects.filter(linkid=mm_cc.linkid,click_time__range=(CLICK_ACTIVE_START_TIME,time_end),isvalid=True)
#             ten_click_num = click_qs.values('openid').distinct().count()
#             ten_click_price = click_price + 30
#         click_rebeta = (mm_cc.valid_num - ten_click_num) * click_price + ten_click_num * ten_click_price

        if mm_cc.valid_num == 0 or click_price <= 0:
            continue
        
        
        c_log,state = CarryLog.objects.get_or_create(xlmm=xlmm.id,
                                                     order_num=carry_no,
                                                     log_type=CarryLog.CLICK_REBETA)
        if not state :
            continue
        
        c_log.value = click_rebeta
        c_log.carry_date = target_date
        c_log.carry_type = CarryLog.CARRY_IN
        c_log.status = CarryLog.PENDING
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
        
        clicks = Clicks.objects.filter(click_time__range=(time_from, time_to),
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
        clickcount.agencylevel = xiaolumama.agencylevel
        clickcount.user_num = user_num
        clickcount.valid_num = valid_num
        clickcount.save()
    
    #update xlmm click rebeta
    task_Push_ClickCount_To_MamaCash(pre_date)
    

from flashsale.clickrebeta.models import StatisticsShoppingByDay

@task(max_retry=3, default_retry_delay=5)
def task_Record_User_Click_Weekly(date_from, date_to, week_code):
    """ 功能：统计date_from - date_to 时间段 的点击 购买 情况 计算转化率
        查询： ClickCount  StatisticsShoppingByDay
        写数据：WeekCount（linkid 、weikefu 、user_num 、valid_num 、buyercount 、ordernumcount  、conversion_rate）
    """
    # 只是对2级并且已经接管的代理做统计
    xlmms = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED)
    for xlmm in xlmms:
        click_count = ClickCount.objects.filter(linkid=xlmm.id, date__gt=date_from, date__lt=date_to)
        shoppings = StatisticsShoppingByDay.objects.filter(linkid=xlmm.id, tongjidate__gt=date_from,
                                                           tongjidate__lt=date_to)
        # 总点击人数
        sum_user_num = click_count.aggregate(total_user_num=Sum('user_num')).get('total_user_num') or 0
        # 总有效点击数
        sum_valid_num = click_count.aggregate(total_valid_num=Sum('valid_num')).get('total_valid_num') or 0
        # 订单总数
        sum_ordernumcount = shoppings.aggregate(total_ordernumcount=Sum('ordernumcount')).get('total_ordernumcount')or 0
        # 购买总人数
        sum_buyercount = shoppings.aggregate(total_buyercount=Sum('buyercount')).get('total_buyercount') or 0
        # 转化率计算
        if sum_user_num == 0:
            conversion_rate = 0
        else:
            conversion_rate = float(sum_buyercount)/sum_user_num  # 转化率等于 购买人数 除以 点击人数
        #创建一条周记录
        week_count, state = WeekCount.objects.get_or_create(linkid=xlmm.id, week_code=week_code)
        week_count.weikefu = xlmm.weikefu
        week_count.user_num = sum_user_num
        week_count.valid_num = sum_valid_num
        week_count.buyercount = sum_buyercount
        week_count.ordernumcount = sum_ordernumcount
        week_count.conversion_rate = conversion_rate
        week_count.save()


@task()
def week_Count_week_Handdle(pre_week_start_dt=None):
    """计算上一周的 开始时间 和 结束时间
    编码周= 'year + month + id'  id = 上一周是本年的 第 id 周
    """
    today = datetime.date.today() #datetime.datetime.today()
    if not pre_week_start_dt:
        weekday = int(today.strftime("%w"))
        dura_days = weekday == 0 and (7 + 6) or (7 + weekday - 1)
        pre_week_start_dt = today - datetime.timedelta(days=dura_days)
            
    pre_week_end_dt = pre_week_start_dt + datetime.timedelta(days=6)
    
    time_from = datetime.datetime(pre_week_start_dt.year,pre_week_start_dt.month,pre_week_start_dt.day,0,0,0)
    time_to   = datetime.datetime(pre_week_end_dt.year,pre_week_end_dt.month,pre_week_end_dt.day,23,59,59)
    
    week_code = str(pre_week_start_dt.year) + pre_week_start_dt.strftime('%U')
    
    task_Record_User_Click_Weekly(time_from, time_to, week_code)
    
#     today_b = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)  # 今天的 开始时间
#     prev_day = today_b - datetime.timedelta(days=1)  # 昨天的开始
#     x_day = prev_day.strftime('%w')  # 获取昨天的星期数
#     # 判断昨天是不是这一周最后一天
#     if x_day == '6':
#     # 如果是则执行
#         if prev_day.strftime('%U') == '00':
#         # 判断昨天是不是一年中的第一周 00
#             date_from = datetime.datetime(today.year, today.month, 1, 0, 0, 0)
#             # 开始时间 是 这一年的第一天
#             date_to = datetime.datetime(prev_day.year,prev_day.month, prev_day.day, 23, 59, 59)  # 包含第七天
#             # 结束时间就是昨天的结束时间（因为上面已经判断了昨天是不是周末）
#             week_code = str(today.year) + '00'
#             # week_code = year+ '00'
#             task_Record_User_Click_Weekly(date_from, date_to, week_code)
#             # 调用 task_Record_User_Click_Weekly (date_from, date_to, week_code) 函数
#         else:
#         # 如果昨天不是这一年的第一周
#             date_from = prev_day - datetime.timedelta(days=6)
#             # 开始时间是 昨天的开始时间 - 6 个整天
#             date_to = datetime.datetime(prev_day.year, prev_day.month, prev_day.day, 23, 59, 59)  # 包含第七天
#             
#             # 结束时间是昨天的结束时间
#             task_Record_User_Click_Weekly(date_from, date_to, week_code)
#             # 调用 task_Record_User_Click_Weekly (date_from, date_to, week_code) 函数


def push_history_week_data():  # 初始执行
    
    today = datetime.datetime.today()
    weekday = int(today.strftime("%w"))
    dura_days = weekday == 0 and  6 or weekday - 1
    week_start = today - datetime.timedelta(days=dura_days)
    
    for i in xrange(1,14):
        week_date = week_start - datetime.timedelta(days=7*i)
        print 'start date:',week_date
        week_Count_week_Handdle(pre_week_start_dt = week_date)
