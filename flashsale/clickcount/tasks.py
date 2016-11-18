# coding=utf-8
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import datetime
from django.db.models import F, Sum
from django.conf import settings
from celery import chain

from flashsale.xiaolumm.models import XiaoluMama, CarryLog, AgencyLevel
from .models import Clicks, UserClicks, ClickCount, WeekCount
from shopapp.weixin.models import WeixinUnionID
from common.modelutils import update_model_change_fields
from . import constants

import logging
logger = logging.getLogger(__name__)

CLICK_ACTIVE_START_TIME = datetime.datetime(2015, 6, 15, 10)
CLICK_MAX_LIMIT_DATE = datetime.date(2015, 6, 5)
# 切换小鹿妈妈点击提成到新小鹿妈妈结算体系日期
SWITCH_CLICKREBETA_DATE = datetime.date(2016, 2, 24)


@app.task()
def task_Create_Click_Record(xlmmid, openid, unionid, click_time, app_key):
    """
    异步保存妈妈分享点击记录
    xlmm_id:小鹿妈妈id,
    openid:妈妈微信openid,
    click_time:点击时间
    """
    mama_id = int(xlmmid)
    mama = XiaoluMama.objects.filter(id=mama_id, status=XiaoluMama.EFFECT, charge_status=XiaoluMama.CHARGED).first()
    
    if not mama:
        return

    #now = datetime.datetime.now()
    #isvalid = True
    #if mama.renew_time < now:
    #    #如果妈妈的续费时间已过，不计点击记录.
    #    return
    
    #tf = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
    #tt = datetime.datetime(now.year, now.month, now.day, 23, 59, 59)
    #
    #isvalid = False
    #clicks = Clicks.objects.filter(openid=openid, click_time__range=(tf, tt))
    #click_linkids = set([l.get('linkid') for l in clicks.values('linkid').distinct()])
    #click_count = len(click_linkids)
    #
    #if click_count < Clicks.CLICK_DAY_LIMIT and xlmmid not in click_linkids:
    #    isvalid = True

    click = Clicks(linkid=mama_id, openid=openid, isvalid=True, click_time=click_time, app_key=app_key)
    click.save()

    return click.id


@app.task()
def task_Update_User_Click(click_id, *args, **kwargs):
    if not click_id:
        return

    click = Clicks.objects.get(id=click_id)
    openid = click.openid
    app_key = click.app_key
    click_time = click.click_time
    wxunions = WeixinUnionID.objects.filter(openid=openid, app_key=app_key)
    if not wxunions.exists():
        return

    unionid = wxunions[0].unionid
    user_click, state = UserClicks.objects.get_or_create(unionid=unionid)
    params = {}
    if (not user_click.click_end_time or
            (click_time > user_click.click_end_time and
                     click_time.date() != user_click.click_end_time.date())):
        params.update(visit_days=F('visit_days') + 1)

    if not user_click.click_start_time or user_click.click_start_time > click_time:
        params.update(click_start_time=click_time)

    if not user_click.click_end_time or user_click.click_end_time < click_time:
        params.update(click_end_time=click_time)

    update_model_change_fields(user_click, update_params=params)


def calc_Xlmm_ClickRebeta(xlmm, time_from, time_to, xlmm_cc=None):
    from flashsale.clickrebeta.models import StatisticsShopping

    if not xlmm_cc:
        mama_ccs = ClickCount.objects.filter(date=time_from.date(), linkid=xlmm.id)
        if mama_ccs.count() == 0:
            return 0
        xlmm_cc = mama_ccs[0]

    buyercount = StatisticsShopping.normal_objects.filter(linkid=xlmm.id,
                                                          shoptime__range=(time_from, time_to)).values(
        'openid').distinct().count()
    day_date = time_from.date()
    click_price = xlmm.get_Mama_Click_Price_By_Day(buyercount, day_date=day_date)
    click_num = xlmm_cc.valid_num

    # 设置最高有效最高点击上限
    max_click_count = xlmm.get_Mama_Max_Valid_Clickcount(buyercount, day_date=day_date)
    #         click_rebeta = click_num  * click_price

    ten_click_num = 0
    ten_click_price = 0
    if CLICK_ACTIVE_START_TIME.date() == time_from.date():
        click_qs = Clicks.objects.filter(linkid=xlmm_cc.linkid,
                                         click_time__range=(CLICK_ACTIVE_START_TIME, time_to), isvalid=True)
        ten_click_num = click_qs.values('openid').distinct().count()
        ten_click_price = click_price + 0

    if time_from.date() >= CLICK_MAX_LIMIT_DATE:
        click_num = min(max_click_count, click_num - ten_click_num)
        ten_click_num = min(ten_click_num, max_click_count)

    click_rebeta = click_num * click_price + ten_click_num * ten_click_price
    return click_rebeta


@app.task()
def task_Push_ClickCount_To_MamaCash(target_date):
    """ 计算每日妈妈点击数现金提成，并更新到妈妈钱包账户"""

    carry_no = int(target_date.strftime('%y%m%d'))
    time_from = datetime.datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    time_end = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

    mm_clickcounts = ClickCount.objects.filter(date=target_date, valid_num__gt=0)
    for mm_cc in mm_clickcounts:
        xlmms = XiaoluMama.objects.filter(id=mm_cc.linkid)
        if xlmms.count() == 0:
            continue

        xlmm = xlmms[0]
        click_rebeta = calc_Xlmm_ClickRebeta(xlmm, time_from, time_end, xlmm_cc=mm_cc)

        if mm_cc.valid_num == 0 or click_rebeta == 0:
            continue

        c_log, state = CarryLog.objects.get_or_create(xlmm=xlmm.id,
                                                      order_num=carry_no,
                                                      log_type=CarryLog.CLICK_REBETA)
        if not state and c_log.status != CarryLog.PENDING:
            continue

        c_log.value = click_rebeta
        c_log.carry_date = target_date
        c_log.carry_type = CarryLog.CARRY_IN
        c_log.status = CarryLog.PENDING
        c_log.save()

        XiaoluMama.objects.filter(id=mm_cc.linkid).update(pending=F('pending') + click_rebeta)


@app.task
def task_Delete_Mamalink_Clicks(pre_date):
    clicks = Clicks.objects.filter(created__lt=pre_date)
    clicks.delete()


@app.task(max_retries=3, default_retry_delay=5)
def task_Record_User_Click(pre_day=1):
    """ 计算每日妈妈点击数，汇总"""
    pre_date = datetime.date.today() - datetime.timedelta(days=pre_day)
    time_from = datetime.datetime(pre_date.year, pre_date.month, pre_date.day)  # 生成带时间的格式  开始时间
    time_to = datetime.datetime(pre_date.year, pre_date.month, pre_date.day, 23, 59, 59)  # 停止时间
    # 代理级别为2 和 3　的　并且id　大于134的
    xlmms = XiaoluMama.objects.filter(agencylevel__gte=XiaoluMama.VIP_LEVEL, id__gt=134)
    for xiaolumama in xlmms:  #
        clicks = Clicks.objects.filter(click_time__range=(time_from, time_to),
                                       linkid=xiaolumama.id)  # 根据代理的id过滤出点击表中属于该代理的点击
        click_num = clicks.count()  # 点击数量
        user_num = clicks.values('openid').distinct().count()  # 点击人数
        valid_num = clicks.filter(isvalid=True).values('openid').distinct().count()  # 有效点击数量
        if click_num > 0 or user_num > 0 or valid_num > 0:  # 有不为0的数据是后才产生统计数字
            clickcount, state = ClickCount.objects.get_or_create(date=pre_date,
                                                                 linkid=xiaolumama.id)
            # 在点击统计表中找今天的记录 如果 有number和小鹿妈妈的id相等的 说明已经该记录已经统计过了
            clickcount.weikefu = xiaolumama.weikefu  # 写名字到统计表
            clickcount.username = xiaolumama.manager  # 接管人
            clickcount.click_num = click_num
            clickcount.mobile = xiaolumama.mobile
            clickcount.agencylevel = xiaolumama.agencylevel
            clickcount.user_num = user_num
            clickcount.valid_num = valid_num
            clickcount.save()

    if pre_date < SWITCH_CLICKREBETA_DATE:
        # update xlmm click rebeta
        task_Push_ClickCount_To_MamaCash(pre_date)

    # delete ximm click some days ago
    pre_delete_date = (datetime.datetime.today() -
                       datetime.timedelta(days=constants.CLICK_RECORDS_REMAIN_DAYS))
    task_Delete_Mamalink_Clicks(pre_delete_date)



from flashsale.clickrebeta.models import StatisticsShoppingByDay


@app.task(max_retries=3, default_retry_delay=5)
def task_Record_User_Click_Weekly(date_from, date_to, week_code):
    """ 功能：统计date_from - date_to 时间段 的点击 购买 情况 计算转化率
        查询： ClickCount  StatisticsShoppingByDay
        写数据：WeekCount（linkid 、weikefu 、user_num 、valid_num 、buyercount 、ordernumcount  、conversion_rate）
    """
    # 只是对2级并且已经接管的代理做统计
    xlmms = XiaoluMama.objects.filter(charge_status=XiaoluMama.CHARGED)
    for xlmm in xlmms:
        click_count = ClickCount.objects.filter(linkid=xlmm.id, date__gt=date_from, date__lt=date_to)
        shoppings = StatisticsShoppingByDay.objects.filter(linkid=xlmm.id, tongjidate__gt=date_from,
                                                           tongjidate__lt=date_to)
        # 总点击人数
        sum_user_num = click_count.aggregate(total_user_num=Sum('user_num')).get('total_user_num') or 0
        # 总有效点击数
        sum_valid_num = click_count.aggregate(total_valid_num=Sum('valid_num')).get('total_valid_num') or 0
        # 订单总数
        sum_ordernumcount = shoppings.aggregate(total_ordernumcount=Sum('ordernumcount')).get(
            'total_ordernumcount') or 0
        # 购买总人数
        sum_buyercount = shoppings.aggregate(total_buyercount=Sum('buyercount')).get('total_buyercount') or 0
        # 转化率计算
        if sum_user_num == 0:
            conversion_rate = 0
        else:
            conversion_rate = float(sum_buyercount) / sum_user_num  # 转化率等于 购买人数 除以 点击人数
        # 创建一条周记录
        week_count, state = WeekCount.objects.get_or_create(linkid=xlmm.id, week_code=week_code)
        week_count.weikefu = xlmm.weikefu
        week_count.user_num = sum_user_num
        week_count.valid_num = sum_valid_num
        week_count.buyercount = sum_buyercount
        week_count.ordernumcount = sum_ordernumcount
        week_count.conversion_rate = conversion_rate
        week_count.save()


@app.task()
def week_Count_week_Handdle(pre_week_start_dt=None):
    """计算上一周的 开始时间 和 结束时间
    编码周= 'year + month + id'  id = 上一周是本年的 第 id 周
    """
    today = datetime.date.today()  # datetime.datetime.today()
    if not pre_week_start_dt:
        weekday = int(today.strftime("%w"))
        dura_days = weekday == 0 and (7 + 6) or (7 + weekday - 1)
        pre_week_start_dt = today - datetime.timedelta(days=dura_days)

    pre_week_end_dt = pre_week_start_dt + datetime.timedelta(days=6)

    time_from = datetime.datetime(pre_week_start_dt.year, pre_week_start_dt.month, pre_week_start_dt.day, 0, 0, 0)
    time_to = datetime.datetime(pre_week_end_dt.year, pre_week_end_dt.month, pre_week_end_dt.day, 23, 59, 59)

    week_code = str(pre_week_start_dt.year) + pre_week_start_dt.strftime('%U')

    task_Record_User_Click_Weekly(time_from, time_to, week_code)


def push_history_week_data():  # 初始执行

    today = datetime.datetime.today()
    weekday = int(today.strftime("%w"))
    dura_days = weekday == 0 and 6 or weekday - 1
    week_start = today - datetime.timedelta(days=dura_days)

    for i in xrange(1, 14):
        week_date = week_start - datetime.timedelta(days=7 * i)

        week_Count_week_Handdle(pre_week_start_dt=week_date)


@app.task()
def task_Count_ClickCount_Info(instance=None, created=None):
    if not created:
        return

    date = instance.created.date()
    # 这里只是捕获创建记录　当有创建的时候　才会去获取或者修改该　点击统计的记录
    click_count, state = ClickCount.objects.get_or_create(date=date, linkid=instance.linkid)
    try:
        xlmm = XiaoluMama.objects.get(id=instance.linkid)
        if xlmm.agencylevel < XiaoluMama.VIP_LEVEL:  # 未接管的不去统计
            return
        if state:  # 表示创建统计记录
            click_count.user_num = 1
            click_count.valid_num = 1
            click_count.click_num = 1
            click_count.date = date
            click_count.save()
        else:  # 表示获取到了　修改该统计记录
            time_from = datetime.datetime(date.year, date.month, date.day)
            time_to = datetime.datetime(date.year, date.month, date.day, 23, 59, 59)
            clicks = Clicks.objects.filter(click_time__range=(time_from, time_to), linkid=xlmm.id)
            click_count.click_num = F('click_num') + 1  # 累加１
            click_count.valid_num = clicks.filter(isvalid=True).values('openid').distinct().count()  # 有效点击数量
            click_count.user_num = clicks.values('openid').distinct().count()  # 点击人数
            click_count.date = date
            click_count.save()
    except XiaoluMama.DoesNotExist:
        return
