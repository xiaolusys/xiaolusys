from __future__ import division
# -*- encoding:utf8 -*-
import datetime

from celery.task import task

from flashsale.pay.models_refund import SaleRefund


import logging

from flashsale.dinghuo.models_stats import DailySupplyChainStatsOrder
from supplychain.supplier.models import SaleProduct, SaleSupplier, SupplierCharge

logger = logging.getLogger('celery.handler')


@task(max_retry=1, default_retry_delay=5)
def task_record_kefu_performance(trade_id, user_id):
    """记录客服操作"""
    try:
        print ""
    except Exception, exc:
        raise task_record_kefu_performance.retry(exc=exc)
    return ""

