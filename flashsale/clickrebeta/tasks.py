# -*- encoding:utf8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import datetime
from django.db.models import F

from shopapp.weixin.models import WXOrder
from flashsale.pay.models import SaleTrade
from flashsale.clickrebeta.models import StatisticsShoppingByDay, StatisticsShopping
from flashsale.xiaolumm.models import CarryLog, XiaoluMama

import logging

__author__ = 'yann'

logger = logging.getLogger('celery.handler')


@app.task()
def task_Push_Rebeta_To_MamaCash(target_date):
    carry_no = int(target_date.strftime('%y%m%d'))

    stat_by_days = StatisticsShoppingByDay.objects.filter(tongjidate=target_date)
    for mm_stat in stat_by_days:
        xlmms = XiaoluMama.objects.filter(id=mm_stat.linkid)
        if xlmms.count() == 0:
            continue

        xlmm = xlmms[0]
        order_rebeta = mm_stat.todayamountcount
        if order_rebeta <= 0:
            continue

        c_log, state = CarryLog.objects.get_or_create(xlmm=xlmm.id,
                                                      order_num=carry_no,
                                                      log_type=CarryLog.ORDER_REBETA)
        if not state and c_log.status != CarryLog.PENDING:
            continue
        c_log.value = order_rebeta
        c_log.carry_date = target_date
        c_log.carry_type = CarryLog.CARRY_IN
        c_log.status = CarryLog.PENDING
        c_log.save()

        XiaoluMama.objects.filter(id=mm_stat.linkid).update(pending=F('pending') + order_rebeta)


from .models import tongji_wxorder, tongji_saleorder


@app.task(max_retries=3, default_retry_delay=5)
def task_Tongji_User_Order(pre_day=1):
    try:
        pre_date = datetime.date.today() - datetime.timedelta(days=pre_day)
        time_from = datetime.datetime(pre_date.year, pre_date.month, pre_date.day)
        time_to = datetime.datetime(pre_date.year, pre_date.month, pre_date.day, 23, 59, 59)

        wxorders = WXOrder.objects.filter(order_create_time__range=(time_from, time_to))
        saletrades = SaleTrade.objects.filter(pay_time__range=(time_from, time_to))

        stat_shoppings = StatisticsShopping.objects.filter(shoptime__range=(time_from, time_to))
        stat_shoppings.delete()

        tongjibyday = StatisticsShoppingByDay.objects.filter(tongjidate__range=(time_from, time_to))
        tongjibyday.delete()

        for wxorder in wxorders:
            tongji_wxorder(None, wxorder)

        for strade in saletrades:
            tongji_saleorder(None, strade)

        # update xlmm Cash
        task_Push_Rebeta_To_MamaCash(pre_date)

    except Exception, exc:
        raise task_Tongji_User_Order.retry(exc=exc)


@app.task(max_retries=3, default_retry_delay=5)
def task_Tongji_All_Order():
    try:
        StatisticsShoppingByDay.objects.all().delete()
        StatisticsShopping.objects.all().delete()
        wx_orders = WXOrder.objects.all()
        cnt = 0
        for order1 in wx_orders:
            tongji_wxorder(None, order1)
            cnt += 1
            if cnt % 1000 == 0:
                print cnt

    except Exception, exc:
        raise task_Tongji_All_Order.retry(exc=exc)


from shopback.trades.models import MergeTrade


def update_Xlmm_Shopping_OrderStatus(order_list):
    """ 更新小鹿妈妈交易订单状态 """
    for order in order_list:
        order_id = order.wxorderid
        trades = MergeTrade.objects.filter(tid=order_id,
                                           type__in=(MergeTrade.WX_TYPE, MergeTrade.SALE_TYPE))
        if trades.count() == 0:
            continue
        trade = trades[0]

        try:
            xlmm = XiaoluMama.objects.get(id=order.linkid)
        except XiaoluMama.DoesNotExist:
            xlmm = None
        if trade.type == MergeTrade.WX_TYPE:
            strade = WXOrder.objects.get(order_id=order_id)
            if trade.sys_status == MergeTrade.INVALID_STATUS or trade.status == MergeTrade.TRADE_CLOSED:
                order.status = StatisticsShopping.REFUNDED
            elif trade.sys_status == MergeTrade.FINISHED_STATUS:
                order.status = StatisticsShopping.FINISHED
        else:
            strade = SaleTrade.objects.get(tid=order_id)
            if strade.status == SaleTrade.TRADE_CLOSED:
                order.status = StatisticsShopping.REFUNDED
            elif strade.status == SaleTrade.TRADE_FINISHED:
                order.status = StatisticsShopping.FINISHED
        if order.status == StatisticsShopping.WAIT_SEND:
            order.rebetamount = xlmm and xlmm.get_Mama_Trade_Amount(strade) or 0
            order.tichengcount = xlmm and xlmm.get_Mama_Trade_Rebeta(strade) or 0
        order.save()


@app.task()
def task_Update_Shoppingorder_Status(pre_day=11):
    target_date = datetime.datetime.now() - datetime.timedelta(days=pre_day)
    shopings = StatisticsShopping.objects.filter(shoptime__lt=target_date,
                                                 status=StatisticsShopping.WAIT_SEND)
    update_Xlmm_Shopping_OrderStatus(shopings)
