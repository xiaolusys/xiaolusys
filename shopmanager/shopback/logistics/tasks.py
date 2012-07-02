import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime
from shopback.logistics.models import Logistics
from auth.apis.exceptions import RemoteConnectionException,AppCallLimitedException,UserFenxiaoUnuseException,\
    APIConnectionTimeOutException,ServiceRejectionException
from shopback.users.models import User
import logging
__author__ = 'meixqhi'

logger = logging.getLogger('logistics.handler')



@task(max_retry=3)
def saveUserOrdersLogisticsTask(user_id,days=0,update_from=None,update_to=None):

    if not(update_from and update_to):
        dt = datetime.datetime.now()
        update_from = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(days,0,0))
        update_to   = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0))


    has_next = True
    cur_page = 1
    error_times = 0

    while has_next:
        try:
            response_list = apis.taobao_logistics_orders_detail_get(tb_user_id=user_id,page_no=cur_page
                 ,page_size=settings.TAOBAO_PAGE_SIZE,start_created=update_from,end_created=update_to)

            logistics_list = response_list['logistics_orders_detail_get_response']
            if logistics_list['total_results']>0:
                for t in logistics_list['shippings']['shipping']:

                    logistics,state = Logistics.objects.get_or_create(pk=t['tid'])
                    logistics.save_logistics_through_dict(user_id,t)

            total_nums = logistics_list['total_results']
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums<total_nums
            cur_page += 1
            error_times = 0
            time.sleep(settings.API_REQUEST_INTERVAL_TIME)

        except RemoteConnectionException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
        except APIConnectionTimeOutException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
            time.sleep(settings.API_TIME_OUT_SLEEP)
        except ServiceRejectionException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
            time.sleep(settings.API_OVER_LIMIT_SLEEP)
        except AppCallLimitedException,e:
            logger.error('update trade logistics fail',exc_info=True)
            raise e




@task()
def updateAllUserOrdersLogisticsTask(days=0,update_from=None,update_to=None):

    hander_update  = update_from and update_to
    if hander_update:
        update_from = format_datetime(update_from)
        update_to   = format_datetime(update_to)

    users = User.objects.all()

    for user in users:
        if hander_update:
            saveUserOrdersLogisticsTask(user.visitor_id,update_from=update_from,update_to=update_to)
        else:
            subtask(saveUserOrdersLogisticsTask).delay(user.visitor_id,days=days)

