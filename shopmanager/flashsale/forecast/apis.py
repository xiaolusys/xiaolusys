# coding:utf-8
import datetime
from celery import task

from .models import (ForecastInbound,
                     ForecastInboundDetail,
                     RealInBound,
                     RealInBoundDetail,
                     )

@task()
def api_create_forecastinbound_by_orderlist(order_list):

    from shopback.items.models import Product, ProductSku
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

        product = Product.objects.filter(id=order.product_id).first()
        product_sku = ProductSku.objects.filter(id=order.chichu_id).first()
        forecast_detail.product_name = '%s:%s'%(product.name, product_sku.name)
        forecast_detail.product_img = product.pic_path
        forecast_detail.forecast_arrive_num = order.buy_quantity
        forecast_detail.save()


@task()
def api_create_realinbound_by_inbound(inbound_id):
    """ base on dinghuo inbound complete signal updates """
    from flashsale.dinghuo.models import InBound
    inbound = InBound.objects.get(id=inbound_id)

    inbound_order_set = set(inbound.orderlist_ids)
    real_inbound = RealInBound()
    real_inbound.wave_no = inbound.id

    forecast_inbound = ForecastInbound.objects.filter(id=inbound.forecast_inbound_id).first()
    if inbound.orderlist_ids and not forecast_inbound:
        forecast_inbound = ForecastInbound.objects.filter(relate_order_set__in=inbound.orderlist_ids).first()
    real_inbound.forecast_inbound = forecast_inbound

    real_inbound.supplier = inbound.supplier
    real_inbound.express_no = inbound.express_no
    real_inbound.creator = inbound.creator.username
    real_inbound.memo = inbound.memo
    real_inbound.status = RealInBound.COMPLETED
    real_inbound.save()

    if forecast_inbound:
        for order_list in forecast_inbound.relate_order_set.all():
            inbound_order_set.add(order_list.id)

    for order_id in inbound_order_set:
        real_inbound.relate_order_set.add(order_id)

    for detail  in inbound.details.all():
        real_detail = RealInBoundDetail()
        real_detail.inbound = real_inbound
        real_inbound.product_id = detail.product.id
        real_inbound.sku_id = detail.sku.id
        real_inbound.barcode = detail.sku.barcode
        real_inbound.product_name = detail.product_name
        real_inbound.product_img = detail.product.pic_path
        real_inbound.arrival_quantity = detail.arrival_quantity
        real_inbound.inferior_quantity = detail.inferior_quantity
        real_inbound.district = detail.district
        real_inbound.save()





