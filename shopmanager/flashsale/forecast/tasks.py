# coding:utf-8
import datetime
from django.conf import settings
from django.db.models import Max
from celery.task import task
from celery.task.sets import subtask

from .models import ForecastInbound, ForecastInboundDetail, ForecastStats, RealInBound
from . import services

@task()
def task_forecast_update_stats_data(finbound_id):
    forecast_inbound = ForecastInbound.objects.get(id=finbound_id)

    stats = ForecastStats.objects.filter(forecast_inbound=forecast_inbound,
                          supplier=forecast_inbound.supplier).first()
    if not stats:
        stats = ForecastStats(forecast_inbound=forecast_inbound,
                          supplier=forecast_inbound.supplier)

    if forecast_inbound.supplier:
        buyer = forecast_inbound.supplier.buyer
        stats.buyer_name = buyer and buyer.username or 'nobody'

    # timeout stats
    if forecast_inbound.status == ForecastInbound.ST_TIMEOUT:
        stats.is_timeout = True
        stats.save()
        return

    realinbounds_qs = forecast_inbound.real_inbound_manager.filter(
        status__in=(RealInBound.STAGING, RealInBound.COMPLETED)
    )
    stats.purchase_num = forecast_inbound.total_forecast_num
    stats.inferior_num = sum(realinbounds_qs.values_list('total_inferior_num',flat=True))
    stats.lack_num = min(0, forecast_inbound.total_forecast_num - forecast_inbound.total_arrival_num)
    # TODO@meron , real lack maybe summary all details lacknum, not total num

    purchase_orders = forecast_inbound.relate_order_set.all()
    purchase_details = services.get_purchaseorder_detail_data(purchase_orders)
    purchase_details_dict = dict([(o['chichu_id'], o) for o in purchase_details])

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
    stats.purchase_time = aggregate_data.get('lastest_pay_time')

    # lackgoods stats
    if forecast_inbound.status == ForecastInbound.ST_CLOSE:
        stats.is_lackclose = True
        stats.save()
        return

    stats.delivery_time = forecast_inbound.delivery_time
    stats.arrival_time = forecast_inbound.arrival_time
    stats.billing_time = aggregate_data.get('lastest_received_time')
    stats.finished_time = aggregate_data.get('lastest_completed_time')

    stats.has_lack = forecast_inbound.has_lack
    stats.has_defact = forecast_inbound.has_defact
    stats.has_overhead = forecast_inbound.has_overhead
    stats.has_wrong = forecast_inbound.has_wrong
    stats.is_unrecordlogistic = forecast_inbound.is_unrecordlogistic
    stats.save()



















