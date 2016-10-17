# -*- coding:utf8 -*-
import logging
from core.managers import BaseManager, CacheManager
from common.modelutils import update_model_fields
from flashsale.pay.signals import signal_saletrade_refund_post


logger = logging.getLogger(__name__)


class NormalSaleTradeManager(BaseManager):
    def get_queryset(self):
        _super = super(NormalSaleTradeManager, self)
        queryset = _super.get_queryset()
        return queryset.filter(
            status__in=self.model.NORMAL_TRADE_STATUS
        ).order_by('-created')


class NormalUserAddressManager(BaseManager):
    def get_queryset(self):
        queryset = super(NormalUserAddressManager, self).get_queryset()
        return queryset.filter(status=self.model.NORMAL).order_by('-created')


from . import constants


class ShopProductCategoryManager(BaseManager):
    def child_query(self):
        """ 童装产品 """
        pro_category = constants.CHILD_CID_LIST
        return self.get_queryset().filter(pro_category__in=pro_category).order_by("-position")

    def female_query(self):
        """ 女装产品 """
        pro_category = constants.FEMALE_CID_LIST
        return self.get_queryset().filter(pro_category__in=pro_category).order_by("-position")


class CustomerManager(CacheManager):

    @property
    def normal_customer(self):
        queryset = super(CustomerManager, self).get_queryset()
        return queryset.filter(status=self.model.NORMAL).order_by('-created')

