# coding: utf-8

import datetime
from django.db import transaction

from . import serializers
from .models import (
    ForecastInbound,
    default_forecast_inbound_no,
    ForecastInboundDetail,
    RealInBound,
    RealInBoundDetail
)

class AggregateDataException(BaseException):
    pass


def filter_pending_purchaseorder(staff_name=None,  **kwargs):
    """ 通过采购员名称获取订货单 """
    from flashsale.dinghuo.models import OrderList, OrderDetail
    order_list = OrderList.objects.filter(
        buyer__username=staff_name,
        sys_status__in=[OrderList.ST_APPROVAL, OrderList.ST_BILLING]
    )

    order_dict_list = []
    for order in order_list:
        order_details = order.order_list.all()
        detail_dict_list = []
        for detail in order_details:
            detail_dict = {
                'id': detail.id,
                'product_id': detail.product_id,
                'sku_id': detail.chichu_id,
                'product_name':detail.product_name,
                'sku_name':detail.product_chicun,
                'purchase_num':detail.buy_quantity
            }
            detail_dict_list.append(detail_dict)

        pt = order.last_pay_date
        if pt:
            pt = datetime.datetime(pt.year, pt.month, pt.day)

        order_dict_list.append({
            'id': order.id,
            'supplier': serializers.SupplierSerializer(order.supplier).data,
            'purchaser':order.buyer_name,
            'post_district': order.p_district,
            'receiver': order.receiver,
            'created': order.created,
            'purchase_time': pt ,
            'sys_status': order.sys_status,
            'sys_status_name': order.status_name,
            'total_detail_num': order.total_detail_num
        })

    return order_dict_list


def get_normal_forecast_inbound_by_orderid(purchase_orderid_list):
    forecast_inbounds = ForecastInbound.objects.filter(relate_order_set__in=purchase_orderid_list)\
        .exclude(status=ForecastInbound.ST_CANCELED)
    return forecast_inbounds


def get_normal_realinbound_by_forecastid(forecastid_list):
    real_inbounds = RealInBound.objects.filter(forecast_inbound_id__in=forecastid_list,
                                               status__in=(RealInBound.STAGING,RealInBound.COMPLETED))
    return real_inbounds


@transaction.atomic
def strip_forecast_inbound(forecast_inbound_id):

    forecast_inbound = ForecastInbound.objects.get(id=forecast_inbound_id)
    update_fields = ['supplier', 'ware_house', 'express_code', 'express_no', 'purchaser']
    new_forecast = ForecastInbound()
    new_forecast.forecast_no = default_forecast_inbound_no('sub'+forecast_inbound.id)
    for k in update_fields:
        if hasattr(forecast_inbound, k):
            setattr(forecast_inbound, k, getattr(forecast_inbound, k))
    new_forecast.save()

    for order in forecast_inbound.relate_order_set.all():
        new_forecast.relate_order_set.add(order)

    # TODO 如果有多个到货单关联一个预测单，需要聚合计算
    real_inbound_details_qs = RealInBoundDetail.objects.filter(inbound__forecast_inbound=forecast_inbound,
                                                               status=RealInBoundDetail.NORMAL)
    real_inbound_qs_values = real_inbound_details_qs.values('sku_id', 'arrival_quantity', 'inferior_quantity')
    real_inbound_detail_dict = dict([(d['sku_id'], d) for d in real_inbound_qs_values])
    for detail in forecast_inbound.normal_details():
        real_detail = real_inbound_detail_dict.get(detail.sku_id,None)
        delta_arrive_num = detail.forecast_arrive_num > real_detail['arrival_quantity']
        if delta_arrive_num > 0:
            forecast_detail = ForecastInboundDetail()
            forecast_detail.forecast_inbound = new_forecast
            forecast_detail.forecast_arrive_num = delta_arrive_num
            forecast_detail.product_id = detail.product_id
            forecast_detail.sku_id = detail.sku_id
            forecast_detail.product_name = detail.product_name
            forecast_detail.product_img = detail.product_img
            forecast_detail.save()


class AggregateForcecastOrderAndInbound(object):

    def __init__(self, purchase_orders):
        self.aggregate_orders_dict = {}

        for order_dict in purchase_orders:
            self.aggregate_orders_dict[order_dict['id']] = order_dict

        self.aggregate_set  = set()

    def recursive_aggragate_order(self, order_id, aggregate_id_set):

        if order_id in self.aggregate_set:
            return

        aggregate_id_set.add(order_id)
        self.aggregate_set.add(order_id)

        forecast_inbounds = get_normal_forecast_inbound_by_orderid([order_id])
        order_ids = forecast_inbounds.values_list('relate_order_set',flat=True)
        for order_id in order_ids:
            self.recursive_aggragate_order(order_id, aggregate_id_set)

    def aggregate_order_set(self):
        """ aggregate order id to set and return set list """
        aggregate_set_list = []
        for order_id in self.aggregate_orders_dict.keys():
            if order_id in self.aggregate_set:
                continue
            aggregate_id_set = set()
            self.recursive_aggragate_order(order_id, aggregate_id_set)
            aggregate_set_list.append(aggregate_id_set)
        return aggregate_set_list

    def aggregate_data(self):
        """根据供应商的订货单分组
        １，　入仓的订货单根据预测单继续聚合分组；
        ２，　未入仓订货单则单独统一分组；　
        """
        aggregate_dict_list = []
        aggregate_set_list = self.aggregate_order_set()

        for aggregate_id_set in aggregate_set_list:
            aggregate_orders = []
            for order_id in aggregate_id_set:
                forecast_inbounds = get_normal_forecast_inbound_by_orderid([order_id])
                order_dict = self.aggregate_orders_dict[order_id]
                order_dict['relate_forecasts'] = forecast_inbounds.values_list('id', flat=True)
                aggregate_orders.append(order_dict)

            aggregate_forecasts = []
            aggregate_inbounds = []

            is_unarrive_intime = False
            is_unrecord_logistic = False
            forecast_inbound_qs = get_normal_forecast_inbound_by_orderid(aggregate_id_set)
            for forecast in forecast_inbound_qs:
                forecast_data = serializers.SimpleForecastInboundSerializer(forecast).data
                real_inbound_qs = get_normal_realinbound_by_forecastid([forecast.id])

                forecast_data['relate_inbounds'] = real_inbound_qs.values_list('id', flat=True)
                aggregate_forecasts.append(forecast_data)

                inbound_data = serializers.SimpleRealInBoundSerializer(real_inbound_qs, many=True).data
                aggregate_inbounds.extend(inbound_data)

                is_unarrived = len(inbound_data) == 0 and \
                               (not forecast.forecast_arrive_time
                                or forecast.forecast_arrive_time <= datetime.datetime.now())
                forecast_data['is_unarrive_intime'] = is_unarrived
                forecast_data['is_unrecord_logistic'] = forecast.is_unrecord_logistic()
                is_unarrive_intime |= is_unarrived
                is_unrecord_logistic += forecast_data['is_unrecord_logistic']

            aggregate_dict_list.append({
                'purchase_orders': aggregate_orders,
                'forecast_inbounds': aggregate_forecasts,
                'real_inbounds': aggregate_inbounds,
                'is_unarrive_intime': is_unarrive_intime,
                'is_unrecord_logistic': is_unrecord_logistic,
                'supplier': aggregate_orders[0]['supplier']
            })

        return aggregate_dict_list


    def aggregate_supplier_data(self, supplier_id=None):
        aggregate_datas = self.aggregate_data()
        aggregate_supplier_dict = {}

        for aggregate_order in aggregate_datas:
            order_supplier_id = aggregate_order['supplier']['id']
            if order_supplier_id in aggregate_supplier_dict:
                aggregate_supplier_dict[order_supplier_id]['purchase_orders'].append(aggregate_order)
            else:
                aggregate_supplier_dict[order_supplier_id] = {
                    'supplier': aggregate_order['supplier'],
                    'aggregate_orders': [aggregate_order],
                }

        if supplier_id:
            supplier_id = int(supplier_id)
            aggregate_supplier_list = [aggregate_supplier_dict.get(supplier_id)]
        else:
            aggregate_supplier_list = aggregate_supplier_dict.values()

        return aggregate_supplier_list














