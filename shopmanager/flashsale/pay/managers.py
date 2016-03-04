#-*- coding:utf8 -*-
from django.db import models
from django.db.models import Q,Sum

from core.managers import BaseManager

class NormalSaleTradeManager(BaseManager):
    
    def get_query_set(self):
        queryset = super(NormalSaleTradeManager,self).get_query_set()
        return queryset.filter(
                status__in=self.model.NORMAL_TRADE_STATUS
            ).order_by('-created')
    
    get_queryset = get_query_set


class NormalUserAddressManager(BaseManager):
    
    def get_query_set(self):
        queryset = super(NormalUserAddressManager,self).get_query_set()
        return queryset.filter(status=self.model.NORMAL).order_by('-created')
        
    get_queryset = get_query_set
import constants


class ShopProductCategoryManager(models.Manager):
    def get_query_set(self):
        queryset = super(ShopProductCategoryManager, self).get_query_set()
        return queryset

    def child_query(self):
        """ 童装产品 """
        pro_category = constants.CHILD_CID_LIST
        return self.get_query_set().filter(pro_category__in=pro_category).order_by("-position")

    def female_query(self):
        """ 女装产品 """
        pro_category = constants.FEMALE_CID_LIST
        return self.get_query_set().filter(pro_category__in=pro_category).order_by("-position")
