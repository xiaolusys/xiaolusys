import os
import re
import time
import datetime
import calendar
from django.conf import settings
from celery.task.sets import subtask
from shopback.asynctask.tasks import AsyncOrderTask,TASK_SUCCESS,TASK_INVALID
from shopback.fenxiao.tasks import saveUserPurchaseOrderTask,saveUserIncrementPurchaseOrderTask
from shopback.refunds.tasks import saveUserRefundOrderTask
from shopback.logistics.tasks import saveUserOrdersLogisticsTask,saveUserUnfinishOrdersLogisticsTask
from shopback.amounts.tasks import updatePurchaseOrdersAmountTask,updateOrdersAmountTask
from shopapp.report.models import MonthTradeReportStatus
from shopback.asynctask.models import TaobaoAsyncTask
from shopapp.report.reportform import TradesToXLSFile
from auth.utils import format_time,parse_datetime,format_datetime,format_date,format_year_month
from shopback.users.models import User
from auth.apis import single_instance_task
import logging

logger = logging.getLogger('report.handler')

BLANK_CHAR = ''
MONTH_TRADE_FILE_TEMPLATE = 'trade-month-%s.xls'



@single_instance_task(24*60*60,prefix='shopapp.report.tasks.')
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

    if os.path.isfile(file_name) or (not update_year_month and time_delta.days<settings.GEN_AMOUNT_FILE_MIN_DAYS):
        return {'error':'%s is already exist or must be %d days from last month at lest!'
            %(file_name,settings.GEN_AMOUNT_FILE_MIN_DAYS)}

    logger.warn('updateMonthTradeXlsFileTask start at :%s'%str(dt))
    start_date   = last_month_first_days - datetime.timedelta(7,0,0)
    
    interval_date = dt - start_date
    users = User.objects.all()
    for user in users:
        report_status,state = MonthTradeReportStatus.objects.get_or_create\
                (seller_id=user.visitor_id,year=year,month=month)
        try:
            if not report_status.update_order:
                if report_status.order_task_id:
                    async_task = TaobaoAsyncTask.objects.get(task_id=report_status.order_task_id)
                    if async_task.status == TASK_INVALID:
                        task_id = subtask(AsyncOrderTask).delay(start_date,dt,user.visitor_id)
                        MonthTradeReportStatus.objects.filter(seller_id=user.visitor_id,year=year,month=month).update(order_task_id=task_id)
                        continue
                    elif async_task.status == TASK_SUCCESS:  
                        report_status.update_order = True
                    else:
                        continue  
                else:
                   task_id = subtask(AsyncOrderTask).delay(start_date,dt,user.visitor_id)
                   MonthTradeReportStatus.objects.filter(seller_id=user.visitor_id,year=year,month=month).update(order_task_id=task_id)
                   continue

            if not report_status.update_purchase:
                saveUserPurchaseOrderTask(user.visitor_id,update_from=start_date,update_to=dt)
                report_status.update_purchase = True

            if not report_status.update_amount:
                updateOrdersAmountTask(user.visitor_id,update_from=last_month_first_days,update_to=dt)
                report_status.update_amount = True
            
            if not report_status.update_purchase_amount:
                updatePurchaseOrdersAmountTask(user.visitor_id,update_from=last_month_first_days,update_to=dt)
                report_status.update_purchase_amount = True

            if not report_status.update_logistics:
                saveUserUnfinishOrdersLogisticsTask(user.visitor_id,update_from=last_month_first_days,update_to=last_month_last_days)
                report_status.update_logistics = True

            if not report_status.update_refund:
                saveUserRefundOrderTask(user.visitor_id,update_from=start_date,update_to=last_month_last_days)
                report_status.update_refund = True

        except Exception,exc:
            report_status.save()
            logger.error('updateMonthTradeXlsFileTask excute error',exc_info=True)
            return {'error':'%s'%exc}

        report_status.save()
    
    try:
        if report_status.update_order and report_status.update_purchase and report_status.update_amount \
            and report_status.update_purchase_amount and report_status.update_logistics and report_status.update_refund:
            trade_file_builder = TradesToXLSFile()
            trade_file_builder.gen_report_file(last_month_first_days,last_month_last_days,file_name)
    except Exception,exc:
        logger.error('gen report file error',exc_info=True)

    dt = datetime.datetime.now()
    logger.warn('updateMonthTradeXlsFileTask end at :%s'%str(dt))
    return {'update_from':format_datetime(last_month_first_days),'update_to':format_datetime(last_month_last_days)}

