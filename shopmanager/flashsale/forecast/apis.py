# coding:utf-8
import datetime
from celery import task

from .models import ForecastInbound, ForecastInboundDetail

@task()
def create_forecastinbound_by_orderlist(order_list):

    supplier = order_list.supplier
    forecast_ib = ForecastInbound()

    forecast_ib.supplier = supplier
    forecast_ib.ware_house  = supplier.ware_by
    forecast_ib.purchaser  = order_list.buyer_name
    forecast_arrive_time = order_list.last_pay_date
    if not forecast_arrive_time:
        forecast_arrive_time = datetime.datetime.now()
    forecast_arrive_time += datetime.timedelta(days=supplier.get_delta_arrive_days())

    forecast_ib.forecast_arrive_time = forecast_arrive_time
    forecast_ib.status = ForecastInbound.ST_DRAFT
    forecast_ib.save()

    forecast_ib.relate_order_set.add(order_list)

    for order in order_list.order_list.all():
        forecast_detail = ForecastInboundDetail()
        forecast_detail.forecast_inbound = forecast_ib
        forecast_detail.product_id = order.product_id
        forecast_detail.sku_id = order.chichu_id
        forecast_detail.forecast_arrive_num = order.buy_quantity
        forecast_detail.save()
