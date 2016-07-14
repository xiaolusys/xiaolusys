# coding: utf-8

import datetime
from django.core.management.base import BaseCommand

from flashsale.dinghuo.models import OrderList

import logging
logger = logging.getLogger(__name__)

UPDATE_START_DATE = datetime.datetime(2016, 4, 1)

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        from flashsale.forecast.models import ForecastInbound

        forecastinbounds = ForecastInbound.objects.all()
        logger.warn('update orderlist groupkey: forecast_count=%s'% forecastinbounds.count())
        for order in forecastinbounds:
            order.save()

        orderlist = OrderList.objects.filter(created__gte=UPDATE_START_DATE, order_group_key='')
        logger.warn('update orderlist groupkey: order_count=%s' % orderlist.count())
        for order in orderlist:
            order.save()

