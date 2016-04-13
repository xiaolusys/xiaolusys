# -*- coding:utf8 -*-
import os
import re
import time
import datetime
import calendar
from django.conf import settings
from celery.task import task
from celery.task.sets import subtask
from shopback.orders.tasks import saveUserIncrementOrdersTask
from shopback.fenxiao.tasks import saveUserPurchaseOrderTask, saveUserIncrementPurchaseOrderTask
from shopback.refunds.tasks import saveUserRefundOrderTask
from shopback.logistics.tasks import saveUserOrdersLogisticsTask
from shopback.amounts.tasks import updatePurchaseOrdersAmountTask, updateOrdersAmountTask
from shopapp.report.models import MonthTradeReportStatus
from shopback.monitor.models import DayMonitorStatus
from shopapp.report.reportform import TradesToXLSFile
from common.utils import format_time, parse_datetime, format_datetime, format_date, format_year_month
from shopback.users.models import User
from common.utils import single_instance_task
import logging

logger = logging.getLogger('django.request')

BLANK_CHAR = ''
MONTH_TRADE_FILE_TEMPLATE = 'D%s.xls'


@single_instance_task(24 * 60 * 60, prefix='shopapp.report.tasks.')
def updateMonthTradeXlsFileTask(year=None, month=None):
    dt = datetime.datetime.now()
    update_year_month = year and month
    if not update_year_month:
        last_month_date = dt - datetime.timedelta(dt.day, 0, 0)
    else:
        year, month = int(year), int(month)
        last_month_date = datetime.datetime(year, month, 1, 0, 0, 0)

    year_month = format_year_month(last_month_date)
    year = last_month_date.year
    month = last_month_date.month

    month_range = calendar.monthrange(year, month)
    last_month_first_days = datetime.datetime(year, month, 1, 0, 0, 0)
    last_month_last_days = datetime.datetime(year, month, month_range[1], 23, 59, 59)

    time_delta = dt - last_month_last_days
    root_path = os.path.join(settings.DOWNLOAD_ROOT, 'TD', str(year))

    if not os.path.exists(root_path):
        os.makedirs(root_path)

    file_name = os.path.join(root_path, MONTH_TRADE_FILE_TEMPLATE % year_month)

    if os.path.isfile(file_name) or (not update_year_month and time_delta.days < settings.GEN_AMOUNT_FILE_MIN_DAYS):
        return {'error': '%s is already exist or must be %d days from last month at lest!'
                         % (file_name, settings.GEN_AMOUNT_FILE_MIN_DAYS)}

    logger.warn('updateMonthTradeXlsFileTask start at :%s' % str(dt))
    start_date = last_month_first_days - datetime.timedelta(7, 0, 0)

    interval_date = dt - start_date
    for user in User.effect_users.TAOBAO:
        report_status, state = MonthTradeReportStatus.objects.get_or_create \
            (seller_id=user.visitor_id, year=year, month=month)
        try:
            if not report_status.update_order:
                for i in xrange(0, time_delta.days):
                    update_start = start_date - datetime.timedelta(i + 1, 0, 0)
                    update_end = start_date - datetime.timedelta(i, 0, 0)
                    monitor_status, state = DayMonitorStatus.objects.get_or_create(
                        user_id=user.visitor_id,
                        year=update_start.year,
                        month=update_start.month,
                        day=update_start.day)
                    if not monitor_status.update_trade_increment:
                        saveUserIncrementOrdersTask(user.visitor_id,
                                                    update_from=update_start,
                                                    update_to=update_end)
                    monitor_status.update_trade_increment = True
                    monitor_status.save()
                report_status.update_order = True

            if not report_status.update_purchase:
                for i in xrange(1, time_delta.days + 1):
                    update_start = start_date - datetime.timedelta(i + 1, 0, 0)
                    update_end = start_date - datetime.timedelta(i, 0, 0)
                    monitor_status, state = DayMonitorStatus.objects.get_or_create(user_id=user.visitor_id, \
                                                                                   year=update_start.year,
                                                                                   month=update_start.month,
                                                                                   day=update_start.day)
                    if not monitor_status.update_purchase_increment:
                        saveUserIncrementPurchaseOrderTask(user.visitor_id, update_from=update_start,
                                                           update_to=update_end)
                    monitor_status.update_purchase_increment = True
                    monitor_status.save()
                report_status.update_purchase = True

            if not report_status.update_amount:
                # updateOrdersAmountTask(user.visitor_id,update_from=last_month_first_days,update_to=dt)
                report_status.update_amount = True

            if not report_status.update_purchase_amount:
                # updatePurchaseOrdersAmountTask(user.visitor_id,update_from=last_month_first_days,update_to=dt)
                report_status.update_purchase_amount = True

            if not report_status.update_logistics:
                saveUserOrdersLogisticsTask(user.visitor_id, update_from=last_month_first_days,
                                            update_to=last_month_last_days)
                report_status.update_logistics = True

            if not report_status.update_refund:
                saveUserRefundOrderTask(user.visitor_id, update_from=start_date, update_to=last_month_last_days)
                report_status.update_refund = True

        except Exception, exc:
            report_status.save()
            logger.error('updateMonthTradeXlsFileTask excute error', exc_info=True)
            return {'error': '%s' % exc}

        report_status.save()

    try:
        if (report_status.update_order and
                report_status.update_purchase and
                report_status.update_amount and
                report_status.update_purchase_amount and
                report_status.update_logistics and
                report_status.update_refund):
            trade_file_builder = TradesToXLSFile()
            trade_file_builder.gen_report_file(last_month_first_days, last_month_last_days, file_name)
    except Exception, exc:
        logger.error('gen report file error', exc_info=True)

    dt = datetime.datetime.now()
    logger.warn('updateMonthTradeXlsFileTask end at :%s' % str(dt))
    return {'update_from': format_datetime(last_month_first_days), 'update_to': format_datetime(last_month_last_days)}
