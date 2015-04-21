#-*- coding:utf8 -*-
import os
import datetime
from django.conf import settings
from django.db.models import Q

from .handler import BaseHandler
from shopback import paramconfig as pcfg
from shopback.base import log_action,User, ADDITION, CHANGE
from common.modelutils import  update_model_fields


class RegularSaleHandler(BaseHandler):
    
    def handleable(self,merge_trade,*args,**kwargs):
        
        if not kwargs.get('first_pay_load',None) or merge_trade.type != pcfg.WX_TYPE:
            return False
        #秒杀订单 取消定时
        if merge_trade.user.visitor_id.lower().endswith('miaosha'):
            return False
        
        orders = merge_trade.inuse_orders.extra(where=["CHAR_LENGTH(outer_id)>=9"])\
            .filter(Q(outer_id__startswith="9")|Q(outer_id__startswith="1")|Q(outer_id__startswith="8"))
        
        return  orders.count() > 0
                
            
    def process(self,merge_trade,*args,**kwargs):
        
        if settings.DEBUG:
            print 'DEBUG REGULARSALE:',merge_trade
        
        if merge_trade.sys_status == pcfg.ON_THE_FLY_STATUS:
            return 
        
        remind_time = datetime.datetime.now() + datetime.timedelta(days=settings.REGULAR_DAYS)
        merge_trade.sys_status = pcfg.REGULAR_REMAIN_STATUS
        
        merge_trade.remind_time = remind_time
        merge_trade.sys_memo += u'特卖订单，到货再发'
        
        update_model_fields(merge_trade,update_fields=['sys_memo','remind_time','sys_status'])
        
        log_action(merge_trade.user.user.id,merge_trade,CHANGE, u'定时(%s)提醒'%remind_time)
        
        