import os
import re
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.fenxiao.models import PurchaseOrder
from shopback.refunds.models import Refund
from shopapp.report.models   import MonthTradeReportStatus
from shopback.users.models import User
from shopback.items.models import Item
from shopapp.report.reportform import TradesToXLSFile
from auth.utils import format_time,parse_datetime,format_datetime,format_date,format_year_month
import logging

logger = logging.getLogger('report.handler')





@task()
def updateMonthTradeXlsFileTask(year=None,month=None):

    dt = datetime.datetime.now()
    update_year_month = year and month
    if not update_year_month:
        last_month_date = dt - datetime.timedelta(dt.day,0,0)
    else:
        year,month = int(year),int(month)
        last_month_date = datetime.datetime(year,month,1,0,0,0)

    year_month = format_year_month(last_month_date)
    year       = last_month_date.year
    month      = last_month_date.month

    month_range = calendar.monthrange(year,month)
    last_month_first_days = datetime.datetime(year,month,1,0,0,0)
    last_month_last_days = datetime.datetime(year,month,month_range[1],23,59,59)

    time_delta = dt - last_month_last_days
    file_name  = settings.DOWNLOAD_ROOT+'/'+MONTH_TRADE_FILE_TEMPLATE%year_month

    if os.path.isfile(file_name) or not update_year_month or time_delta.days<settings.GEN_AMOUNT_FILE_MIN_DAYS:
        return {'error':'%s is already exist or must be ten days from last month at lest!'%file_name}

    start_date   = last_month_first_days - datetime.timedelta(7,0,0)

    users = User.objects.all()
    for user in users:
        report_status,state = MonthTradeReportStatus.objects.get_or_create\
                (seller_id=user.visitor_id,year=year,month=month)
        try:
            if not report_status.update_order:
                saveUserDuringOrders(user.visitor_id,update_from=start_date,update_to=dt)
                report_status.update_order = True

            if not report_status.update_purchase:
                interval_date = dt - start_date
                for i in range(0,interval_date.days/7+1):
                    dt_f = start_date + datetime.timedelta(i*7,0,0)
                    dt_t = start_date + datetime.timedelta((i+1)*7,0,0)
                    saveUserPurchaseOrderTask(user.visitor_id,update_from=dt_f,update_to=dt_t)
                report_status.update_purchase = True

            if not report_status.update_amount:
                updateOrdersAmountTask(user.visitor_id,update_from=last_month_first_days,update_to=dt)
                report_status.update_amount = True

            if not report_status.update_logistics:
                saveUserOrdersLogisticsTask(user.visitor_id,update_from=last_month_first_days,update_to=last_month_last_days)
                report_status.update_logistics = True

            if not report_status.update_refund:
                saveUserRefundOrderTask(user.visitor_id,update_from=start_date,update_to=last_month_last_days)
                report_status.update_refund = True

        except Exception,exc:
            report_status.save()
            logger.error('updateMonthTradeXlsFileTask excute error.',exc_info=True)
            return {'error':'%s'%exc}

        report_status.save()

    trade_file_builder = TradesToXLSFile()
    trade_file_builder.gen_report_file(last_month_first_days,last_month_last_days,file_name)

    return {'update_from':format_datetime(last_month_first_days),'update_to':format_datetime(last_month_last_days)}

