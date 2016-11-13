# coding:utf-8
from __future__ import absolute_import, unicode_literals
from celery import shared_task as task

import datetime
from .models import (
    ForecastInbound,
    ForecastInboundDetail,
    RealInbound,
    RealInboundDetail,
)
from . import  constants

import logging
logger = logging.getLogger(__name__)

def orderlist_change_forecastinbound(order_list):
    logger.info('orderlist_change_forecastinbound start: %s'% order_list)
    from shopback.items.models import Product, ProductSku
    supplier = order_list.supplier
    orderlist_id = order_list.id
    first_create = True
    try:
        forecast_ib = ForecastInbound.objects.get(supplier=supplier,
                                                  relate_order_set__in=[orderlist_id])
        first_create = False
    except ForecastInbound.DoesNotExist:
        forecast_ib = ForecastInbound(supplier=supplier)
    except Exception, exc:
        logger.error('forecastinbound: orderlist=%s ,refresh error: %s'% (order_list, exc.message), exc_info=True)
        return

    forecast_ib.ware_house = supplier.ware_by
    forecast_ib.purchaser = order_list.buyer and order_list.buyer.username or order_list.buyer_name
    forecast_arrive_time = order_list.last_pay_date
    if not forecast_arrive_time:
        forecast_arrive_time = datetime.datetime.now()
    forecast_arrive_time += datetime.timedelta(days=supplier.get_delta_arrive_days())
    forecast_ib.forecast_arrive_time = forecast_arrive_time
    forecast_ib.save()

    if first_create:
        forecast_ib.relate_order_set.add(order_list)

    for order in order_list.order_list.all():
        forecast_detail = ForecastInboundDetail.objects.filter(forecast_inbound=forecast_ib,
                                                               sku_id=order.chichu_id).first()
        if not forecast_detail:
            forecast_detail = ForecastInboundDetail(forecast_inbound=forecast_ib,
                                                    sku_id=order.chichu_id)
        forecast_detail.forecast_inbound = forecast_ib
        forecast_detail.product_id = order.product_id
        forecast_detail.sku_id = order.chichu_id

        product = Product.objects.filter(id=order.product_id).first()
        product_sku = ProductSku.objects.filter(id=order.chichu_id).first()
        forecast_detail.product_name = '%s:%s' % (product.name, product_sku.name)
        forecast_detail.product_img = product.pic_path
        forecast_detail.forecast_arrive_num = order.buy_quantity
        if order.buy_quantity <= 0:
            forecast_detail.status = ForecastInboundDetail.DELETE
        forecast_detail.save()

    forecast_ib.save()
    logger.info('orderlist_change_forecastinbound end: %s' % order_list)


@task(max_retries=3, default_retry_delay=60)
def api_create_or_update_forecastinbound_by_orderlist(order_list, force_update=False):
    logger.info('api_create_or_update_forecastinbound start: %s'% order_list)
    from flashsale.dinghuo.models import OrderList
    try:
        orderlist_id = order_list.id
        forecast_ibs = ForecastInbound.objects.filter(relate_order_set__in=[orderlist_id])
        if forecast_ibs.exists():
            for forecast_ib in forecast_ibs:
                order_status_list = set(forecast_ib.relate_order_set.values_list('sys_status',flat=True))
                if len(order_status_list) == 1 and list(order_status_list)[0] == OrderList.STAGE_DELETED:
                    forecast_ib.status = ForecastInbound.ST_CANCELED
                elif len(order_status_list) == 1 and list(order_status_list)[0] in (
                    OrderList.STAGE_STATE, OrderList.STAGE_COMPLETED):
                    forecast_ib.status = ForecastInbound.ST_FINISHED
                forecast_ib.express_code = forecast_ib.express_code or order_list.express_company
                forecast_ib.express_no = forecast_ib.express_no or order_list.express_no
                forecast_ib.save()
            if not force_update:
                logger.info('api_create_or_update_forecastinbound update: %s' % order_list)
                return
        # if delete or account or complete not create forecast
        if order_list.stage in (OrderList.STAGE_DELETED, OrderList.STAGE_COMPLETED, OrderList.STAGE_STATE):
            logger.info('api_create_or_update_forecastinbound exit: %s, %s' % (order_list, order_list.stage))
            return

        orderlist_change_forecastinbound(order_list)
    except Exception, exc:
        raise api_create_or_update_forecastinbound_by_orderlist.retry(exc=exc)

    logger.info('api_create_or_update_forecastinbound end: %s' % order_list)


@task(max_retries=3, default_retry_delay=60)
def api_create_or_update_realinbound_by_inbound(inbound_id):
    """ base on dinghuo inbound complete signal updates """
    logger.info('api_create_or_update_realinbound: %s' % inbound_id)
    try:
        from flashsale.dinghuo.models import InBound
        from shopback.items.models import ProductSku
        inbound = InBound.objects.get(id=inbound_id)
        if not inbound.details.exists():
            logger.error('inbound detail empty: inbound_id=%s'% inbound_id)
            return
        real_wave_no = 'ref%s'% inbound_id
        inbound_order_set = set([int(bid) for bid in inbound.orderlist_ids])
        real_inbound = RealInbound.objects.filter(wave_no=real_wave_no).first()
        if not real_inbound:
            real_inbound = RealInbound()
            real_inbound.wave_no = real_wave_no

        forecast_inbound = ForecastInbound.objects.filter(id=inbound.forecast_inbound_id).first()
        if inbound.orderlist_ids and not forecast_inbound:
            forecast_inbound = ForecastInbound.objects.filter(relate_order_set__in=inbound.orderlist_ids).first()
        real_inbound.forecast_inbound = forecast_inbound

        real_inbound.supplier = inbound.supplier
        real_inbound.express_no = inbound.express_no
        real_inbound.creator = inbound.creator.username
        real_inbound.memo = inbound.memo
        if inbound.is_invalid():
            real_inbound.status = RealInbound.CANCELED
        else:
            real_inbound.status = RealInbound.COMPLETED
        real_inbound.save()

        if forecast_inbound:
            for order_list in forecast_inbound.relate_order_set.all():
                inbound_order_set.add(order_list.id)

        real_inbound.relate_order_set.clear()
        for order_id in inbound_order_set:
            real_inbound.relate_order_set.add(order_id)

        inbound_sku_dict = {}
        for detail  in inbound.details.all():
            try:
                if not detail.product or not detail.sku:
                    product_id, sku_id = constants.UNRECORD_PRODUCTID_TUPLE
                else:
                    product_id, sku_id = detail.product.id , detail.sku.id
                sku = ProductSku.objects.filter(id=sku_id).first()
                product = sku and sku.product
                real_detail = RealInboundDetail.objects.filter(inbound=real_inbound,
                                                               sku_id=sku_id).first()
                if not real_detail:
                    real_detail = RealInboundDetail()

                real_detail.inbound = real_inbound
                real_detail.product_id = product_id
                real_detail.sku_id  = sku_id
                real_detail.barcode = sku and sku.BARCODE
                real_detail.product_name = product and product.name
                real_detail.product_img =  product and product.pic_path
                real_detail.arrival_quantity = detail.arrival_quantity + detail.inferior_quantity
                real_detail.inferior_quantity = detail.inferior_quantity
                real_detail.district = detail.district
                real_detail.save()

                inbound_sku_dict[real_detail.sku_id] = {
                    'arrival_quantity': real_detail.arrival_quantity,
                    'inferior_quantity': real_detail.inferior_quantity
                }
            except Exception,exc:
                logger.error('inbound error:%s'%exc.message, exc_info=True)

        if forecast_inbound:
            forecast_inbound.inbound_arrive_update_status(arrival_time=inbound.created)
            for detail in forecast_inbound.normal_details:
                ib_detail = inbound_sku_dict.pop(detail.sku_id, None)
                if not ib_detail:
                    forecast_inbound.has_lack |= True
                    continue

                if detail.forecast_arrive_num > ib_detail['arrival_quantity']:
                    forecast_inbound.has_lack |= True
                elif detail.forecast_arrive_num < ib_detail['arrival_quantity']:
                    forecast_inbound.has_overhead |= True
                if ib_detail['inferior_quantity'] > 0:
                    forecast_inbound.has_defact |= True
            if inbound_sku_dict:
                forecast_inbound.has_wrong = True
            forecast_inbound.save()
        # 更新orderlist order_group_key
        from flashsale.dinghuo.tasks import task_update_order_group_key
        task_update_order_group_key.delay(inbound_order_set)
    except Exception, exc:
        raise api_create_or_update_realinbound_by_inbound.retry(exc=exc)





