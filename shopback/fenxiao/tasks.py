# -*- coding:utf8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task as task

import time
import datetime
from django.conf import settings
from shopback.fenxiao.models import PurchaseOrder, FenxiaoProduct, SubPurchaseOrder
from shopapp.taobao.exceptions import UserFenxiaoUnuseException, TaobaoRequestException
from shopback.monitor.models import TradeExtraInfo, SystemConfig, DayMonitorStatus
from shopback import paramconfig as pcfg
from shopback.users.models import User as Seller
from common.utils import (format_time,
                          format_datetime,
                          format_year_month,
                          parse_datetime,)
from shopapp.taobao import apis
import logging

__author__ = 'meixqhi'

logger = logging.getLogger('django.request')


@task()
def saveUserFenxiaoProductTask(seller_id):
    seller = Seller.getSellerByVisitorId(seller_id)
    if not seller.has_fenxiao:
        return

    fenxiao_product_ids = []
    try:
        has_next = True
        cur_page = 0

        while has_next:
            response_list = apis.taobao_fenxiao_products_get(page_no=cur_page,
                                                             page_size=settings.TAOBAO_PAGE_SIZE / 2,
                                                             tb_user_id=seller_id)

            products = response_list['fenxiao_products_get_response']
            if products['total_results'] > 0:
                fenxiao_product_list = products['products']['fenxiao_product']
                for fenxiao_product in fenxiao_product_list:
                    FenxiaoProduct.save_fenxiao_product_dict(seller_id, fenxiao_product)

                    fenxiao_product_ids.append(fenxiao_product['pid'])

            total_nums = products['total_results']
            cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE / 2
            has_next = cur_nums < total_nums
            cur_page += 1

    except UserFenxiaoUnuseException, exc:
        logger.warn(u'该用户非分销平台用户:%s,%s' % (str(seller_id), exc.message))

    except TaobaoRequestException, exc:
        logger.error(u'分销商品更新异常：%s' % exc.message, exc_info=True)

    else:
        FenxiaoProduct.objects.filter(user__visitor_id=seller_id) \
            .exclude(pid__in=fenxiao_product_ids).update(status=FenxiaoProduct.DOWN)


@task(max_retries=3)
def saveUserPurchaseOrderTask(seller_id, update_from=None, update_to=None, status=None):
    seller = Seller.getSellerByVisitorId(seller_id)
    if not seller.has_fenxiao:
        return

    from shopback.trades.service import TradeService, PurchaseOrderService

    try:
        if not (update_from and update_to):
            update_from = datetime.datetime.now() - datetime.timedelta(28, 0, 0)
            update_to = datetime.datetime.now()

        exec_times = (update_to - update_from).days / 7 + 1
        for i in range(0, exec_times):
            dt_f = update_from + datetime.timedelta(i * 7, 0, 0)
            dt_t = update_from + datetime.timedelta((i + 1) * 7, 0, 0)

            has_next = True
            cur_page = 1

            while has_next:

                response_list = apis.taobao_fenxiao_orders_get(tb_user_id=seller_id,
                                                               page_no=cur_page,
                                                               time_type='trade_time_type',
                                                               page_size=settings.TAOBAO_PAGE_SIZE / 2,
                                                               start_created=dt_f,
                                                               end_created=dt_t,
                                                               status=status)

                orders_list = response_list['fenxiao_orders_get_response']
                if orders_list['total_results'] > 0:
                    for o in orders_list['purchase_orders']['purchase_order']:

                        modified = datetime.datetime.strptime(o['modified'], '%Y-%m-%d %H:%M:%S')

                        if TradeService.isValidPubTime(seller_id, o['id'], modified):
                            purchase_order = PurchaseOrderService.savePurchaseOrderByDict(seller_id, o)
                            PurchaseOrderService.createMergeTrade(purchase_order)

                total_nums = orders_list['total_results']
                cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE
                has_next = cur_nums < total_nums
                cur_page += 1

    except Exception, exc:
        logger.error(u'分销订单下载失败:%s' % exc.message, exc_info=True)

        raise saveUserPurchaseOrderTask.retry(exc=exc, countdown=60)


@task()
def saveUserIncrementPurchaseOrderTask(seller_id, update_from=None, update_to=None):
    seller = Seller.getSellerByVisitorId(seller_id)
    if not seller.has_fenxiao:
        return

    update_from = format_datetime(update_from)
    update_to = format_datetime(update_to)

    from shopback.trades.service import TradeService, PurchaseOrderService

    has_next = True
    cur_page = 1

    while has_next:
        response_list = apis.taobao_fenxiao_orders_get(tb_user_id=seller_id,
                                                       page_no=cur_page,
                                                       time_type='update_time_type',
                                                       page_size=settings.TAOBAO_PAGE_SIZE / 2,
                                                       start_created=update_from,
                                                       end_created=update_to)

        orders_list = response_list['fenxiao_orders_get_response']
        if orders_list['total_results'] > 0:
            for o in orders_list['purchase_orders']['purchase_order']:

                modified = datetime.datetime.strptime(o['modified'], '%Y-%m-%d %H:%M:%S')

                if TradeService.isValidPubTime(seller_id, o['id'], modified):
                    purchase_order = PurchaseOrderService.savePurchaseOrderByDict(seller_id, o)
                    PurchaseOrderService.createMergeTrade(purchase_order)

        total_nums = orders_list['total_results']
        cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE
        has_next = cur_nums < total_nums
        cur_page += 1


@task()
def updateAllUserIncrementPurchaseOrderTask(update_from=None, update_to=None):
    update_handler = update_from and update_to
    dt = datetime.datetime.now()

    if update_handler:
        time_delta = update_to - update_from
        update_days = time_delta.days + 1
    else:
        update_to = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)
        update_days = 1

    sellers = Seller.effect_users.TAOBAO

    for user in sellers:
        for i in xrange(0, update_days):
            update_start = update_to - datetime.timedelta(i + 1, 0, 0)
            update_end = update_to - datetime.timedelta(i, 0, 0)

            year = update_start.year
            month = update_start.month
            day = update_start.day

            monitor_status, state = DayMonitorStatus.objects.get_or_create(user_id=user.visitor_id,
                                                                           year=year,
                                                                           month=month,
                                                                           day=day)
            try:
                if not monitor_status.update_purchase_increment:
                    saveUserIncrementPurchaseOrderTask(user.visitor_id,
                                                       update_from=update_start,
                                                       update_to=update_end)
            except Exception, exc:
                logger.error('%s' % exc, exc_info=True)
            else:
                monitor_status.update_purchase_increment = True
                monitor_status.save()


@task()
def updateAllUserIncrementPurchasesTask():
    """ 增量更新分销平台订单信息 """

    dt = datetime.datetime.now()
    sysconf = SystemConfig.getconfig()
    sellers = Seller.effect_users.TAOBAO
    updated = sysconf.fenxiao_order_updated

    try:
        for user in sellers:
            if not updated:
                saveUserPurchaseOrderTask(user.visitor_id,
                                          status=pcfg.WAIT_SELLER_SEND_GOODS)
                continue

            bt_dt = dt - updated
            if bt_dt.days >= 1:
                saveUserPurchaseOrderTask(user.visitor_id,
                                          status=pcfg.WAIT_SELLER_SEND_GOODS)
            else:
                saveUserIncrementPurchaseOrderTask(user.visitor_id,
                                                   update_from=updated,
                                                   update_to=dt)
                saveUserPurchaseOrderTask(user.visitor_id,
                                          status=pcfg.WAIT_SELLER_SEND_GOODS)

    except Exception, exc:
        logger.error('%s' % exc, exc_info=True)
    else:
        SystemConfig.objects.filter(id=sysconf.id).update(fenxiao_order_updated=dt)
