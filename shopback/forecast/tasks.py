# coding=utf-8
from __future__ import absolute_import, unicode_literals

import datetime
from django.conf import settings
from django.db.models import Max
from shopmanager import celery_app as app

from .models import ForecastInbound, ForecastInboundDetail, ForecastStats, RealInbound
from . import services

import logging
logger = logging.getLogger(__name__)

@app.task(max_retries=3, default_retry_delay=60)
def task_forecast_update_stats_data(finbound_id):
    try:
        forecast_inbound = ForecastInbound.objects.get(id=finbound_id)

        purchase_orders = forecast_inbound.relate_order_set.all()
        purchase_order  = purchase_orders.first()
        if not purchase_order:
            return

        stats = ForecastStats.objects.filter(forecast_inbound=forecast_inbound,
                              supplier=forecast_inbound.supplier).first()
        if not stats:
            stats = ForecastStats(forecast_inbound=forecast_inbound,
                              supplier=forecast_inbound.supplier)

        if forecast_inbound.supplier:
            buyer_name = forecast_inbound.supplier.buyer_name
            stats.buyer_name = buyer_name or 'nobody'

        realinbounds_qs = forecast_inbound.real_inbound_manager.filter(
            status__in=(RealInbound.STAGING, RealInbound.COMPLETED)
        )
        stats.purchase_num = forecast_inbound.total_forecast_num
        stats.inferior_num = sum(realinbounds_qs.values_list('total_inferior_num',flat=True))
        stats.lack_num = max(0, forecast_inbound.total_forecast_num - forecast_inbound.total_arrival_num)
        # TODO@meron , real lack maybe summary all details lacknum, not total num

        purchase_details = services.get_purchaseorder_detail_data(list(purchase_orders))
        purchase_details_dict = dict([(int(o['chichu_id']), o) for o in purchase_details])

        stats.purchaser = purchase_order.get_buyer_name()
        total_amount = 0
        for detail in forecast_inbound.normal_details:
            purchase_detail = purchase_details_dict.get(detail.sku_id, {})
            buy_unitprice = purchase_detail and purchase_detail['buy_unitprice'] or 0
            total_amount += detail.forecast_arrive_num * buy_unitprice

        aggregate_data = purchase_orders.aggregate(
            lastest_pay_time=Max('created'),
            lastest_received_time=Max('received_time'),
            lastest_completed_time=Max('completed_time'))
        stats.purchase_amount = total_amount
        stats.purchase_time = forecast_inbound.created #aggregate_data.get('lastest_pay_time')

        stats.delivery_time = forecast_inbound.delivery_time
        stats.arrival_time = forecast_inbound.arrival_time
        stats.billing_time = aggregate_data.get('lastest_received_time')
        stats.finished_time = aggregate_data.get('lastest_completed_time')

        stats.has_lack = forecast_inbound.has_lack
        stats.has_defact = forecast_inbound.has_defact
        stats.has_overhead = forecast_inbound.has_overhead
        stats.has_wrong = forecast_inbound.has_wrong
        stats.is_unrecordlogistic = forecast_inbound.is_unrecordlogistic
        # timeout stats
        if forecast_inbound.status == ForecastInbound.ST_TIMEOUT or(
            forecast_inbound.arrival_time and forecast_inbound.forecast_arrive_time and
            forecast_inbound.forecast_arrive_time.date() < forecast_inbound.arrival_time.date()
        ) :
            stats.status = ForecastStats.EXCEPT
            stats.is_timeout = True
        elif forecast_inbound.status == ForecastInbound.ST_CLOSED:
            stats.status = ForecastStats.EXCEPT
            stats.is_lackclose = True
        elif forecast_inbound.status == ForecastInbound.ST_CANCELED or forecast_inbound.total_forecast_num==0:
            stats.status = ForecastStats.CLOSED
        elif forecast_inbound.status == ForecastInbound.ST_APPROVED:
            stats.status = ForecastStats.STAGING
        elif forecast_inbound.status in (ForecastInbound.ST_ARRIVED, ForecastInbound.ST_FINISHED):
            stats.status = ForecastStats.ARRIVAL
        stats.save()
    except Exception,exc:
        raise task_forecast_update_stats_data.retry(exc=exc)



















