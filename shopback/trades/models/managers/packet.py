# -*- coding:utf-8 -*-
import datetime
from django.db import models, transaction
from django.db.models import Q, Sum, F, Manager
from django.db.models.signals import post_save
from django.conf import settings
from shopback.users.models import User
from shopback.items.models import Item, Product, ProductSku
from flashsale.pay.models import SaleOrder, SaleTrade
from shopback.logistics.models import Logistics, LogisticsCompany
from flashsale.pay.models import SaleTrade
from shopback.items.models import SkuStock
from flashsale import pay
import logging
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_THIRD, WARE_CHOICES
from shopback.trades.constants import PSI_STATUS, SYS_ORDER_STATUS, IN_EFFECT, PO_STATUS
from shopback import paramconfig as pcfg
from models import TRADE_TYPE, TAOBAO_TRADE_STATUS
from core.managers import BaseManager
logger = logging.getLogger('django.request')


class PackageSkuItemManager():
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()

    get_queryset = get_query_set