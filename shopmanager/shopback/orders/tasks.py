# -*- coding:utf8 -*-
import os
import time
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.orders.models import Order, Trade
from shopback.users.models import User
from shopback.monitor.models import TradeExtraInfo, SystemConfig, DayMonitorStatus
from auth.apis.exceptions import (RemoteConnectionException,
                                  AppCallLimitedException,
                                  UserFenxiaoUnuseException,
                                  APIConnectionTimeOutException,
                                  ServiceRejectionException)
from shopback import paramconfig as pcfg
from common.utils import (format_time,
                          format_datetime,
                          format_year_month,
                          parse_datetime,
                          single_instance_task)
from auth import apis

import logging

logger = logging.getLogger('django.request')
BLANK_CHAR = ''

TASK_SUCCESS = 'SUCCESS'
TASK_FAIL = 'FAIL'


@task(max_retries=3)
def saveUserDuringOrdersTask(user_id, update_from=None, update_to=None, status=None):
    """ 下载用户商城订单 """
    update_tids = []
    try:
        update_from = format_datetime(update_from) if update_from else None
        update_to = format_datetime(update_to) if update_to else None

        has_next = True
        cur_page = 1

        from shopback.trades.service import TradeService, OrderService
        while has_next:
            response_list = apis.taobao_trades_sold_get(tb_user_id=user_id,
                                                        page_no=cur_page,
                                                        use_has_next='true',
                                                        fields='tid,modified',
                                                        page_size=settings.TAOBAO_PAGE_SIZE,
                                                        start_created=update_from,
                                                        end_created=update_to,
                                                        status=status)

            order_list = response_list['trades_sold_get_response']
            if order_list.has_key('trades'):
                for trade in order_list['trades']['trade']:

                    modified = parse_datetime(trade['modified']) if trade.get('modified', None) else None

                    if TradeService.isValidPubTime(user_id, trade['tid'], modified):
                        try:
                            trade_dict = OrderService.getTradeFullInfo(user_id, trade['tid'])
                            order_trade = OrderService.saveTradeByDict(user_id, trade_dict)
                            OrderService.createMergeTrade(order_trade)

                        except Exception, exc:
                            logger.error(u'淘宝订单下载失败:%s' % exc.message, exc_info=True)

                    update_tids.append(trade['tid'])

            has_next = order_list['has_next']
            cur_page += 1
    except Exception, exc:
        logger.error(u'淘宝订单批量下载错误：%s' % exc.message, exc_info=True)
        raise saveUserDuringOrdersTask.retry(exc=exc, countdown=60)

    else:
        from shopback.trades.models import MergeTrade
        wait_update_trades = MergeTrade.objects.filter(user__visitor_id=user_id,
                                                       type=pcfg.TAOBAO_TYPE,
                                                       status=pcfg.WAIT_SELLER_SEND_GOODS) \
            .exclude(tid__in=update_tids)
        for trade in wait_update_trades:
            tid = trade.tid
            if tid.find('-') == len(tid) - 2:
                continue
            try:
                TradeService(user_id, trade.tid).payTrade()
            except Exception, exc:
                logger.error(u'更新订单信息异常:%s' % exc, exc_info=True)


@task()
def saveUserIncrementOrdersTask(user_id, update_from=None, update_to=None):
    s_dt_f = format_datetime(update_from)
    s_dt_t = format_datetime(update_to)

    has_next = True
    cur_page = 1

    from shopback.trades.service import TradeService, OrderService
    while has_next:
        response_list = apis.taobao_trades_sold_increment_get(tb_user_id=user_id,
                                                              page_no=cur_page,
                                                              fields='tid,modified',
                                                              page_size=settings.TAOBAO_PAGE_SIZE,
                                                              use_has_next='true',
                                                              start_modified=s_dt_f,
                                                              end_modified=s_dt_t)
        trade_list = response_list['trades_sold_increment_get_response']

        if trade_list.has_key('trades'):
            for trade in trade_list['trades']['trade']:
                modified = parse_datetime(trade['modified']) if trade.get('modified', None) else None
                if TradeService.isValidPubTime(user_id, trade['tid'], modified):
                    try:
                        trade_dict = OrderService.getTradeFullInfo(user_id, trade['tid'])
                        order_trade = OrderService.saveTradeByDict(user_id, trade_dict)
                        OrderService.createMergeTrade(order_trade)
                    except Exception, exc:
                        logger.error(u'淘宝订单下载失败:%s' % exc.message, exc_info=True)

        has_next = trade_list['has_next']
        cur_page += 1


@task()
def updateAllUserIncrementOrdersTask(update_from=None, update_to=None):
    """ 使用淘宝增量交易接口更新订单信息 """

    update_handler = update_from and update_to
    dt = datetime.datetime.now()

    if update_handler:
        time_delta = update_to - update_from
        update_days = time_delta.days + 1
    else:
        update_to = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)
        update_days = 1
    users = User.effect_users.TAOBAO
    for user in users:
        for i in xrange(0, update_days):
            update_start = update_to - datetime.timedelta(i + 1, 0, 0)
            update_end = update_to - datetime.timedelta(i, 0, 0)
            year = update_start.year
            month = update_start.month
            day = update_start.day
            monitor_status, state = (DayMonitorStatus.
                                     objects.get_or_create(user_id=user.visitor_id,
                                                           year=year,
                                                           month=month,
                                                           day=day))
            try:
                if not monitor_status.update_trade_increment:
                    saveUserIncrementOrdersTask(user.visitor_id,
                                                update_from=update_start,
                                                update_to=update_end)
            except Exception, exc:
                logger.error(u'更新订单报表状态异常：%s' % exc.message, exc_info=True)
            else:
                monitor_status.update_trade_increment = True
                monitor_status.save()


@single_instance_task(12 * 60 * 60, prefix='shopback.orders.tasks.')
def updateAllUserWaitPostOrderTask():
    users = User.effect_users.TAOBAO
    for user in users:
        saveUserDuringOrdersTask(user.visitor_id,
                                 status=pcfg.WAIT_SELLER_SEND_GOODS)


@single_instance_task(60 * 60, prefix='shopback.orders.tasks.')
def updateAllUserIncrementTradesTask():
    """ 增量更新订单信息 """

    dt = datetime.datetime.now()
    sysconf = SystemConfig.getconfig()
    users = User.effect_users.TAOBAO
    updated = sysconf.mall_order_updated
    try:
        if updated:
            bt_dt = dt - updated
            if bt_dt.days >= 1:
                for user in users:
                    saveUserDuringOrdersTask(user.visitor_id,
                                             status=pcfg.WAIT_SELLER_SEND_GOODS)
            else:
                for user in users:
                    saveUserIncrementOrdersTask(user.visitor_id,
                                                update_from=updated, update_to=dt)
        else:
            for user in users:
                saveUserDuringOrdersTask(user.visitor_id,
                                         status=pcfg.WAIT_SELLER_SEND_GOODS)
    except Exception, exc:
        logger.error(u'淘宝订单下载异常:%s' % exc.message, exc_info=True)

    else:
        SystemConfig.objects.filter(id=sysconf.id).update(mall_order_updated=dt)
