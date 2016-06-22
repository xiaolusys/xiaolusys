# coding:utf-8
import datetime
from celery import task

from .models import (ForecastInbound,
                     ForecastInboundDetail,
                     RealInBound,
                     RealInBoundDetail,
                     )

import logging
logger = logging.getLogger(__name__)

@task()
def api_create_or_update_forecastinbound_by_orderlist(order_list):

    from shopback.items.models import Product, ProductSku
    supplier = order_list.supplier

    forecast_ib = ForecastInbound.objects.filter(relate_order_set__in=[order_list.id]).first()
    if forecast_ib:
        forecast_ib.express_code = forecast_ib.express_code or order_list.express_company
        forecast_ib.express_no = forecast_ib.express_no or order_list.express_no
        forecast_ib.save(update_fields=['express_code', 'express_no'])
        return

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
def api_create_or_update_realinbound_by_inbound(inbound_id):
    """ base on dinghuo inbound complete signal updates """
    from flashsale.dinghuo.models import InBound
    inbound = InBound.objects.get(id=inbound_id)

    real_wave_no = 'ref%s'% inbound_id
    inbound_order_set = set(inbound.orderlist_ids)
    real_inbound = RealInBound.objects.filter(wave_no=real_wave_no).first()
    if not real_inbound:
        real_inbound = RealInBound()
        real_inbound.wave_no = real_wave_no

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
        try:
            real_detail = RealInBoundDetail.objects.filter(inbound=real_inbound,
                                                           sku_id=detail.sku.id).first()
            if not real_detail:
                real_detail = RealInBoundDetail()

            real_detail.inbound = real_inbound
            real_detail.product_id = detail.product.id
            real_detail.sku_id = detail.sku.id
            real_detail.barcode = detail.sku.barcode
            real_detail.product_name = detail.product_name
            real_detail.product_img = detail.product.pic_path
            real_detail.arrival_quantity = detail.arrival_quantity + detail.inferior_quantity
            real_detail.inferior_quantity = detail.inferior_quantity
            real_detail.district = detail.district
            real_detail.save()
        except Exception,exc:
            logger.error('inbound error:%s'%exc.message, exc_info=True)
    if forecast_inbound:
        forecast_inbound.inbound_arrive_update_status()




