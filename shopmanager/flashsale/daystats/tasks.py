# -*- encoding:utf8 -*-
import datetime
from django.db.models import F,Sum
from celery.task import task

from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShopping
from flashsale.xiaolumm.models import Clicks, CarryLog
from flashsale.pay.models import Customer
from .models import DailyStat, PopularizeCost

import logging

__author__ = 'yann'

logger = logging.getLogger('celery.handler')

@task()
def task_Push_Sales_To_DailyStat(target_date):
    
    df = datetime.datetime(target_date.year,target_date.month,target_date.day,0,0,0)
    dt = datetime.datetime(target_date.year,target_date.month,target_date.day,23,59,59)
    
    seven_day_ago = target_date - datetime.timedelta(days=7)
    seven_day_before = datetime.datetime(seven_day_ago.year,seven_day_ago.month,seven_day_ago.day,0,0,0)
#     click_count = ClickCount.objects.get(date=target_date)
#     cc_stats = click_count.aggregate(total_user_num=Sum('user_num'),
#                                      total_valid_num=Sum('valid_num'))
    clicks = Clicks.objects.filter(click_time__range=(df,dt))
    
    total_click_count = clicks.values('linkid','openid').distinct().count()
    total_user_num  = clicks.values('openid').distinct().count()
    total_valid_count = clicks.filter(isvalid=True).values('linkid','openid').distinct().count()
    
    total_old_visiter_num = 0
    click_openids = clicks.values('openid').distinct()
    for stat in click_openids:
        last_clicks = Clicks.objects.filter(click_time__lte=df,openid=stat['openid'])
        if last_clicks.count() > 0:
            total_old_visiter_num += 1
    
    shoping_stats     = StatisticsShopping.objects.filter(shoptime__range=(df,dt))
    total_payment     = shoping_stats.aggregate(total_payment=Sum('wxorderamount')).get('total_payment') or 0
    total_order_num   = shoping_stats.values('wxorderid').distinct().count()
    total_buyer_num   = shoping_stats.values('openid').distinct().count()
    
    total_old_buyer_num = 0
    seven_old_buyer_num = 0
    
    total_old_order_num = 0
    stats_openids = shoping_stats.values('openid').distinct()
    for stat in stats_openids:
        day_ago_stats = StatisticsShopping.objects.filter(shoptime__lte=df,openid=stat['openid'])
        if day_ago_stats.count() > 0:
            total_old_buyer_num += 1
            total_old_order_num += shoping_stats.filter(openid=stat['openid']).values('wxorderid').distinct().count()
        
        seven_day_ago_stats = StatisticsShopping.objects.filter(shoptime__lte=seven_day_before,
                                                                openid=stat['openid'])
        if seven_day_ago_stats.count() > 0:
            seven_old_buyer_num += 1
            
    dstat, state = DailyStat.objects.get_or_create(day_date=target_date)
    dstat.total_click_count = total_click_count
    dstat.total_valid_count = total_valid_count
    dstat.total_visiter_num = total_user_num
    dstat.total_new_visiter_num = total_user_num - total_old_visiter_num
    
    dstat.total_payment     = total_payment
    dstat.total_order_num   = total_order_num
    dstat.total_new_order_num   = total_order_num - total_old_order_num
    
    dstat.total_buyer_num   = total_buyer_num
    dstat.total_old_buyer_num   = total_old_buyer_num
    dstat.seven_buyer_num   = seven_old_buyer_num
    dstat.save()
    
@task()
def task_Calc_Sales_Stat_By_Day(pre_day=1):
    
    pre_date = datetime.date.today() - datetime.timedelta(days=pre_day)
    
    task_Push_Sales_To_DailyStat(pre_date)


def carrylogs_By_Date(date):
    carrylogs_order = CarryLog.objects.filter(log_type=CarryLog.ORDER_REBETA, carry_date=date).exclude(
        status=CarryLog.CANCELED)  # 订单返现
    carrylog_order = carrylogs_order.aggregate(total_carry_order=Sum('value')).get(
        'total_carry_order') or 0
    carrylog_order = carrylog_order / 100.0
    carrylogs_click = CarryLog.objects.filter(log_type=CarryLog.CLICK_REBETA, carry_date=date).exclude(
        status=CarryLog.CANCELED)  # 点击返现
    carrylog_click = carrylogs_click.aggregate(total_carry_click=Sum('value')).get(
        'total_carry_click') or 0
    carrylog_click = carrylog_click / 100.0
    carrylogs_thousand = CarryLog.objects.filter(log_type=CarryLog.THOUSAND_REBETA, carry_date=date).exclude(
        status=CarryLog.CANCELED)  # 千元提成
    carrylog_thousand = carrylogs_thousand.aggregate(total_carry_thousand=Sum('value')).get(
        'total_carry_thousand') or 0
    carrylog_thousand = carrylog_thousand / 100.0
    carrylogs_agency = CarryLog.objects.filter(log_type=CarryLog.AGENCY_SUBSIDY, carry_date=date).exclude(
        status=CarryLog.CANCELED)  # 代理补贴
    carrylog_agency = carrylogs_agency.aggregate(total_carry_agency=Sum('value')).get(
        'total_carry_agency') or 0
    carrylog_agency = carrylog_agency / 100.0
    carrylogs_recruit = CarryLog.objects.filter(log_type=CarryLog.MAMA_RECRUIT, carry_date=date).exclude(
        status=CarryLog.CANCELED)  # 招募奖金
    carrylog_recruit = carrylogs_recruit.aggregate(total_carry_recruit=Sum('value')).get(
        'total_carry_recruit') or 0
    carrylog_recruit = carrylog_recruit / 100.0

    carrylogs_order_buy = CarryLog.objects.filter(log_type=CarryLog.ORDER_BUY, carry_date=date).exclude(
        status=CarryLog.CANCELED)  # 消费支出
    carrylog_order_buy = carrylogs_order_buy.aggregate(total_carry_order_buy=Sum('value')).get(
        'total_carry_order_buy') or 0
    carrylog_order_buy = carrylog_order_buy / 100.0
    carrylogs_refund_return = CarryLog.objects.filter(log_type=CarryLog.REFUND_RETURN, carry_date=date).exclude(
        status=CarryLog.CANCELED)  # 退款返现
    carrylog_refund_return = carrylogs_refund_return.aggregate(total_carry_refund=Sum('value')).get(
        'total_carry_refund') or 0
    carrylog_refund_return = carrylog_refund_return / 100.0
    carrylogs_cash_out = CarryLog.objects.filter(log_type=CarryLog.CASH_OUT, carry_date=date).exclude(
        status=CarryLog.CANCELED)  # 提现
    carrylog_cash_out = carrylogs_cash_out.aggregate(total_carry_cashout=Sum('value')).get(
        'total_carry_cashout') or 0
    carrylog_cash_out = carrylog_cash_out / 100.0
    carrylogs_deposit = CarryLog.objects.filter(log_type=CarryLog.DEPOSIT, carry_date=date).exclude(
        status=CarryLog.CANCELED)  # 押金
    carrylog_deposit = carrylogs_deposit.aggregate(total_carry_deposit=Sum('value')).get(
        'total_carry_deposit') or 0
    carrylog_deposit = carrylog_deposit / 100.0

    # carry_in
    total_carrys_in = CarryLog.objects.filter(carry_type=CarryLog.CARRY_IN, carry_date=date)  # 推广费用
    total_carry_in = total_carrys_in.aggregate(total_in=Sum('value')).get(
        'total_in') or 0
    total_carry_in = total_carry_in / 100.0
    # carry_out
    total_carrys_out = CarryLog.objects.filter(carry_type=CarryLog.CARRY_OUT, carry_date=date)  # 妈妈支出
    total_carry_out = total_carrys_out.aggregate(total_out=Sum('value')).get(
        'total_out') or 0
    total_carry_out = total_carry_out / 100.0

    return carrylog_order, carrylog_click, carrylog_thousand, carrylog_agency, carrylog_recruit, \
           carrylog_order_buy, carrylog_refund_return, carrylog_cash_out, carrylog_deposit, \
           total_carry_in, total_carry_out


@task()
def task_PopularizeCost_By_Day(pre_day=1):
    # PopularizeCost
    # 写昨天的数据（确认状态 AND pending 状态的）
    pre_date = datetime.date.today() - datetime.timedelta(days=pre_day)

    carrylog_order, carrylog_click, carrylog_thousand, carrylog_agency, carrylog_recruit,\
    carrylog_order_buy, carrylog_refund_return, carrylog_cash_out, carrylog_deposit, \
    total_carry_in, total_carry_out = carrylogs_By_Date(pre_date)

    # 创建推广记录
    popu_cost, state = PopularizeCost.objects.get_or_create(date=pre_date)
    popu_cost.carrylog_order = carrylog_order
    popu_cost.carrylog_click = carrylog_click
    popu_cost.carrylog_thousand = carrylog_thousand
    popu_cost.carrylog_agency = carrylog_agency
    popu_cost.carrylog_recruit = carrylog_recruit

    popu_cost.carrylog_order_buy = carrylog_order_buy
    popu_cost.carrylog_cash_out = carrylog_cash_out
    popu_cost.carrylog_deposit = carrylog_deposit
    popu_cost.carrylog_refund_return = carrylog_refund_return

    popu_cost.total_carry_in = total_carry_in
    popu_cost.total_carry_out = total_carry_out
    popu_cost.save()

    twelve_date = datetime.date.today() - datetime.timedelta(days=12)

    # 修改12天前的推广记录
    try:
        twelve_date_popu_cost = PopularizeCost.objects.get(date=twelve_date)

        carrylog_order_twelve, carrylog_click_twelve, carrylog_thousand_twelve, carrylog_agency_twelve, carrylog_recruit_twelve,\
        carrylog_order_buy_twelve, carrylog_refund_return_twelve, carrylog_cash_out_twelve, carrylog_deposit_twelve, \
        total_carry_in_twelve, total_carry_out_twelve = carrylogs_By_Date(twelve_date)

        twelve_date_popu_cost.carrylog_order = carrylog_order_twelve
        twelve_date_popu_cost.carrylog_click = carrylog_click_twelve
        twelve_date_popu_cost.carrylog_thousand = carrylog_thousand_twelve
        twelve_date_popu_cost.carrylog_agency = carrylog_agency_twelve
        twelve_date_popu_cost.carrylog_recruit = carrylog_recruit_twelve

        twelve_date_popu_cost.carrylog_order_buy = carrylog_order_buy_twelve
        twelve_date_popu_cost.carrylog_cash_out = carrylog_cash_out_twelve
        twelve_date_popu_cost.carrylog_deposit = carrylog_deposit_twelve
        twelve_date_popu_cost.carrylog_refund_return = carrylog_refund_return_twelve

        twelve_date_popu_cost.total_carry_in = total_carry_in_twelve
        twelve_date_popu_cost.total_carry_out = total_carry_out_twelve
        twelve_date_popu_cost.save()
    except:
        pass





