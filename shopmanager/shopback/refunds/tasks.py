import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime
from shopback.refunds.models import Refund
from shopback.users.models import User
from auth import apis
import logging
__author__ = 'meixqhi'

logger = logging.getLogger('refunds.handler')



@task(max_retry=3)
def saveUserRefundOrderTask(user_id,update_from=None,update_to=None):

    update_from = format_datetime(update_from)
    update_to   = format_datetime(update_to)

    has_next = True
    cur_page = 1

    while has_next:

        response_list = apis.taobao_refunds_receive_get(tb_user_id=user_id,page_no=cur_page,
             page_size=settings.TAOBAO_PAGE_SIZE,start_modified=update_from,end_modified=update_to)

        refund_list = response_list['refunds_receive_get_response']
        if refund_list['total_results']>0:
            for r in refund_list['refunds']['refund']:

                refund,state = Refund.objects.get_or_create(pk=r['refund_id'])
                refund.save_refund_through_dict(user_id,r)

        total_nums = refund_list['total_results']
        cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
        has_next = cur_nums<total_nums
        cur_page += 1
        




@task()
def updateAllUserRefundOrderTask(days=0,update_from=None,update_to=None):

    hander_update  = update_from and update_to
    if not hander_update:
        dt  = datetime.datetime.now()
        update_from = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(days,0,0)
        update_to   = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)-datetime.timedelta(1,0,0)

    users = User.objects.all()
    for user in users:
        if hander_update:
            saveUserRefundOrderTask(user.visitor_id,update_from=update_from,update_to=update_to)
        else:
            subtask(saveUserRefundOrderTask).delay(user.visitor_id,update_from=update_from,update_to=update_to)
            
            
                       
                        

            
            
  