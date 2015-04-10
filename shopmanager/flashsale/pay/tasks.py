import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings

from shopback.users.models import User
from flashsale.pay.models import TradeCharge,SaleTrade,SaleOrder 
from .service import FlashSaleService
import logging

__author__ = 'meixqhi'

logger = logging.getLogger('celery.handler')


@task(max_retry=3)
def notifyTradePayTask(notify):

    try:
        order_no = notify['order_no']
        charge   = notify['charge']
        
        tcharge,state = TradeCharge.objects.get_or_create(order_no=order_no,charge=charge)
        
        if tcharge.paid:
            return 
            
        for k,v in notify.iteritems():
            if k in ('time_paid','time_expire'):
                v = v and datetime.datetime.fromtimestamp(v / 1e3)
            hasattr(tcharge,k) and setattr(tcharge,k,v)
            
        tcharge.save()
        
        strade = SaleTrade.objects.get(id=order_no)
        strade.status = SaleTrade.WAIT_SELLER_SEND_GOODS,
        strade.pay_time = tcharge.time_paid
        strade.save()
        
        saleservice = FlashSaleService(strade)
        saleservice.payTrade()
    
    except Exception,exc:
        logger.error('notifyTradePayTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            notifyTradePayTask.retry(exc=exc,countdown=2)
    

@task(max_retry=3)
def notifyTradeRefundTask(notify):

    pass
        




            
            
                       
                        

            
            
  
