import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings

from shopback.users.models import User
from flashsale.pay.models import SaleTrade,SaleOrder 
from auth import apis
import logging

__author__ = 'meixqhi'

logger = logging.getLogger('django.request')


@task(max_retry=3)
def createPayTradeTask(user_id,update_from=None,update_to=None):

    pass
        




            
            
                       
                        

            
            
  
