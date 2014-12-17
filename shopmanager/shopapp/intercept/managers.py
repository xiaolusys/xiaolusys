#-*- coding:utf-8 -*-
import random
import datetime
from django.db import models
from django.db.models import Q,Sum
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction

from shopback import paramconfig as pcfg
from shopback.trades.models import MergeTrade
        
class InterceptTradeManager(models.Manager):
    
    def get_queryset(self):
        
        super_tm = super(InterceptTradeManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set()
        
        return super_tm.get_queryset()
    
    def getTradeByInterceptInfo(self,nick,mobile,serial_no):
        
        handle      = False
        trades      = None
        filter_dict = {}
        if nick:
            filter_dict.update(buyer_nick=nick)
            
        if mobile:
            filter_dict.update(receiver_mobile=mobile)
            
        if serial_no:
            filter_dict.update(tid=serial_no)
            
        if len(filter_dict.keys()) == 1:
            trades = MergeTrade.objects.filter(**filter_dict)\
                                  .exclude(sys_status__in=(pcfg.FINISHED_STATUS,
                                                           pcfg.INVALID_STATUS,
                                                           pcfg.EMPTY_STATUS))
        
        if len(filter_dict.keys()) > 1:
            
            tfilter = None
            for k,v in filter_dict.iteritems():
                if tfilter:
                    tfilter = tfilter|Q(**{k:v})
                    continue
                tfilter = Q(**{k:v})
                
            trades = MergeTrade.objects.filter(tfilter)\
                                  .exclude(sys_status__in=(pcfg.FINISHED_STATUS,
                                                           pcfg.INVALID_STATUS))
        
        return trades
    
    def getInterceptTradeByBuyerInfo(self,buyer_nick,buyer_mobile,serial_no):
        
        tfilter = Q(serial_no=serial_no)
        if buyer_nick:
            tfilter = tfilter|Q(buyer_nick=buyer_nick)
            
        if buyer_mobile:
            tfilter = tfilter|Q(buyer_mobile=buyer_mobile)
        
        return self.filter(tfilter,status=self.model.UNCOMPLETE)
        
    
