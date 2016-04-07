#-*- coding:utf8 -*-
from django.db import models
from django.db.models import Q,Sum

from core.managers import BaseManager

class NormalSaleTradeManager(BaseManager):
    
    def get_query_set(self):
        _super = super(NormalSaleTradeManager,self)
        if hasattr(_super,'get_query_set'):
            queryset =  _super.get_query_set()
        else:
            queryset = _super.get_queryset()
        return queryset.filter(
                status__in=self.model.NORMAL_TRADE_STATUS
            ).order_by('-created')
    
    get_queryset = get_query_set


class NormalUserAddressManager(BaseManager):
    
    def get_query_set(self):
        queryset = super(NormalUserAddressManager,self).get_query_set()
        return queryset.filter(status=self.model.NORMAL).order_by('-created')
        
    get_queryset = get_query_set

from . import constants


class ShopProductCategoryManager(BaseManager):

    def child_query(self):
        """ 童装产品 """
        pro_category = constants.CHILD_CID_LIST
        return self.get_query_set().filter(pro_category__in=pro_category).order_by("-position")

    def female_query(self):
        """ 女装产品 """
        pro_category = constants.FEMALE_CID_LIST
        return self.get_query_set().filter(pro_category__in=pro_category).order_by("-position")
