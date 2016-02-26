#-*- coding:utf8 -*-
from django.db import models
from django.db.models import Q,Sum

from core.ormcache.managers import CacheManager

class NormalSaleTradeManager(models.Manager):
    
    def get_query_set(self):
        queryset = super(NormalSaleTradeManager,self).get_query_set()
        return queryset.filter(
            status__in=self.model.NORMAL_TRADE_STATUS
        ).order_by('-created')
    
    get_queryset = get_query_set


class NormalUserAddressManager(models.Manager):
    
    def get_query_set(self):
        queryset = super(NormalUserAddressManager,self).get_query_set()
        return queryset.filter(status=self.model.NORMAL).order_by('-created')
        
    
    get_queryset = get_query_set
    
    

    