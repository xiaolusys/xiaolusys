import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime
from shopback.fenxiao.models import PurchaseOrder
from auth.apis.exceptions import RemoteConnectionException,AppCallLimitedException,UserFenxiaoUnuseException,\
    APIConnectionTimeOutException,ServiceRejectionException
from shopback.users.models import User
import logging
__author__ = 'meixqhi'

logger = logging.getLogger('fenxiao.handler')



@task(max_retry=3)
def saveUserPurchaseOrderTask(user_id,update_from=None,update_to=None):

    update_from = format_datetime(update_from)
    update_to   = format_datetime(update_to)

    has_next = True
    cur_page = 1
    error_times = 0

    while has_next:
        try:
            response_list = apis.taobao_fenxiao_orders_get(tb_user_id=user_id,page_no=cur_page,
                time_type='trade_time_type',page_size=settings.TAOBAO_PAGE_SIZE/2,start_created=update_from,end_created=update_to)

            orders_list = response_list['fenxiao_orders_get_response']
            if orders_list['total_results']>0:
                for o in orders_list['purchase_orders']['purchase_order']:

                    order,state = PurchaseOrder.objects.get_or_create(pk=o['fenxiao_id'])
                    order.save_order_through_dict(user_id,o)

            total_nums = orders_list['total_results']
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
        except UserFenxiaoUnuseException:
            logger.error('the seller is not the user of fenxiao plateform',exc_info=True)
            break
        except AppCallLimitedException,e:
            logger.error('update trade purchase order fail',exc_info=True)
            raise e





@task()
def updateAllUserPurchaseOrderTask(update_from=None,update_to=None):

    hander_update  = update_from and update_to
    if not hander_update:
        dt  = datetime.datetime.now()
        update_from = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(7,0,0)
        update_to   = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)-datetime.timedelta(1,0,0)

    users = User.objects.all()
    interval_date = update_to - update_from

    for user in users:
        if hander_update:
            for i in range(0,interval_date.days/7+1):
                dt_f = update_from + datetime.timedelta(i*7,0,0)
                dt_t = update_from + datetime.timedelta((i+1)*7,0,0)
                saveUserPurchaseOrderTask(user.visitor_id,update_from=dt_f,update_to=dt_t)
        else:
            subtask(saveUserPurchaseOrderTask).delay(user.visitor_id,update_from=update_from,update_to=update_to)

  