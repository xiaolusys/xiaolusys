# coding=utf-8
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback import paramconfig as pcfg
from shopback.logistics.models import Logistics
from shopback.orders.models import Trade
from shopback.fenxiao.models import PurchaseOrder
from shopback.monitor.models import TradeExtraInfo
from shopback.trades.models import PackageOrder
from shopback.users.models import User
from common.utils import format_time, format_datetime, format_year_month, parse_datetime, update_model_fields
from shopapp.taobao import apis
import logging

__author__ = 'meixqhi'

logger = logging.getLogger('django.request')


@task(max_retries=3)
def saveUserOrdersLogisticsTask(user_id, update_from=None, update_to=None):
    if not (update_from and update_to):
        dt = datetime.datetime.now()
        update_from = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0) - datetime.timedelta(1, 0, 0)
        update_to = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)

    update_from = format_datetime(update_from)
    update_to = format_datetime(update_to)

    has_next = True
    cur_page = 1

    while has_next:
        response_list = apis.taobao_logistics_orders_detail_get(tb_user_id=user_id, page_no=cur_page
                                                                , page_size=settings.TAOBAO_PAGE_SIZE,
                                                                start_created=update_from, end_created=update_to)

        logistics_list = response_list['logistics_orders_detail_get_response']
        if logistics_list['total_results'] > 0:
            for logistics in logistics_list['shippings']['shipping']:
                Logistics.save_logistics_through_dict(user_id, logistics)

        total_nums = logistics_list['total_results']
        cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE
        has_next = cur_nums < total_nums
        cur_page += 1


@task()
def updateAllUserOrdersLogisticsTask(update_from=None, update_to=None):
    hander_update = update_from and update_to

    users = User.objects.all()

    for user in users:
        if hander_update:
            saveUserOrdersLogisticsTask(user.visitor_id, update_from=update_from, update_to=update_to)
        else:
            subtask(saveUserOrdersLogisticsTask).delay(user.visitor_id)


@task(max_retries=3)
def saveUserUnfinishOrdersLogisticsTask(user_id, update_from=None, update_to=None):
    trades = Trade.objects.filter(user__visitor_id=user_id, status__in=pcfg.ORDER_OK_STATUS,
                                  consign_time__gte=update_from, consign_time__lte=update_to)
    for trade in trades:
        trade_extra_info, created = TradeExtraInfo.objects.get_or_create(tid=trade.id)
        if not trade_extra_info.is_update_logistic:
            response = apis.taobao_logistics_orders_detail_get(tid=trade.id, tb_user_id=trade.seller_id)
            logistics_dict = response['logistics_orders_detail_get_response']['shippings']['shipping'][0]
            Logistics.save_logistics_through_dict(user_id, logistics_dict)

    purchase_trades = PurchaseOrder.objects.filter(user__visitor_id=user_id, status__in=pcfg.ORDER_OK_STATUS,
                                                   consign_time__gte=update_from, consign_time__lte=update_to)
    for trade in purchase_trades:
        trade_extra_info, created = TradeExtraInfo.objects.get_or_create(tid=trade.id)
        if not trade_extra_info.is_update_logistic:
            response = apis.taobao_logistics_orders_detail_get(tid=trade.id, tb_user_id=trade.seller_id)
            logistics_dict = response['logistics_orders_detail_get_response']['shippings']['shipping'][0]
            Logistics.save_logistics_through_dict(user_id, logistics_dict)


@task()
def updateAllUserUnfinishOrdersLogisticsTask(update_from=None, update_to=None):
    users = User.objects.all()

    for user in users:
        saveUserUnfinishOrdersLogisticsTask(user.visitor_id, update_from=update_from, update_to=update_to)


@task(max_retries=3, default_retry_delay=6)
def task_get_logistics_company(package_order_id):
    package_order = PackageOrder.objects.get(id=package_order_id)
    if package_order.sys_status == PackageOrder.WAIT_PREPARE_SEND_STATUS and not package_order.logistics_company:
        package_order.set_logistics_company()
