from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import datetime
from shopback.orders.models import Order, Trade
from shopback.monitor.models import TradeExtraInfo
from shopback.fenxiao.models import PurchaseOrder
from shopback.users.models import User
from shopback.amounts.models import TradeAmount
from shopback import paramconfig as pcfg
from shopapp.taobao import apis

import logging

logger = logging.getLogger('django.request')


@app.task()
def updateOrdersAmountTask(user_id, update_from=None, update_to=None):
    finish_trades = Trade.objects.filter(user__visitor_id=user_id, consign_time__gte=update_from,
                                         consign_time__lte=update_to, status__in=pcfg.ORDER_OK_STATUS)

    for trade in finish_trades:
        trade_extra_info, state = TradeExtraInfo.objects.get_or_create(tid=trade.id)

        if trade_extra_info.is_update_amount:
            continue

        response_list = apis.taobao_trade_amount_get(tid=trade.id, tb_user_id=user_id)

        tamt = response_list['trade_amount_get_response']['trade_amount']
        TradeAmount.save_trade_amount_through_dict(user_id, tamt)

        trade_extra_info.is_update_amount = True
        trade_extra_info.save()


@app.task()
def updateAllUserOrdersAmountTask(days=0, dt_f=None, dt_t=None):
    hander_update = dt_f and dt_t
    if not hander_update:
        dt = datetime.datetime.now()
        dt_f = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0) \
               - datetime.timedelta(days, 0, 0)
        dt_t = datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59) \
               - datetime.timedelta(1, 0, 0)

    users = User.objects.all()
    for user in users:
        if hander_update:
            updateOrdersAmountTask(user.visitor_id, update_from=dt_f, update_to=dt_t)
        else:
           updateOrdersAmountTask.delay(user.visitor_id, update_from=dt_f, update_to=dt_t)


@app.task()
def updatePurchaseOrdersAmountTask(user_id, update_from=None, update_to=None):
    user = User.objects.get(visitor_id=user_id)
    if not user.has_fenxiao:
        return

    purchase_orders = PurchaseOrder.objects.filter(user__visitor_id=user_id, consign_time__gte=update_from,
                                                   consign_time__lte=update_to, status__in=pcfg.ORDER_OK_STATUS)

    for order in purchase_orders:
        trade_extra_info, state = TradeExtraInfo.objects.get_or_create(tid=order.id)

        if trade_extra_info.is_update_amount:
            continue

        response_list = apis.taobao_trade_amount_get(tid=order.id, tb_user_id=user_id)

        tamt = response_list['trade_amount_get_response']['trade_amount']
        TradeAmount.save_trade_amount_through_dict(user_id, tamt)

        trade_extra_info.is_update_amount = True
        trade_extra_info.save()


@app.task()
def updateAllUserPurchaseOrdersAmountTask(days=0, dt_f=None, dt_t=None):
    hander_update = dt_f and dt_t
    if not hander_update:
        dt = datetime.datetime.now()
        dt_f = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0) \
               - datetime.timedelta(days, 0, 0)
        dt_t = datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59) \
               - datetime.timedelta(1, 0, 0)

    users = User.objects.all()
    for user in users:
        if hander_update:
            updatePurchaseOrdersAmountTask(user.visitor_id, update_from=dt_f, update_to=dt_t)
        else:
            updatePurchaseOrdersAmountTask.delay(user.visitor_id, update_from=dt_f, update_to=dt_t)
