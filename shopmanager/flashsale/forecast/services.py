# coding: utf-8

import datetime

from . import serializers
from .models import (
    ForecastInbound,
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
            'sys_status_display': order.get_sys_status_display()
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

                is_unarrive_intime |= is_unarrived
                is_unrecord_logistic += forecast.is_unrecord_logistic()

            aggregate_dict_list.append({
                'purchase_orders': aggregate_orders,
                'forecast_inbounds': aggregate_forecasts,
                'real_inbounds': aggregate_inbounds,
                'is_unarrive_intime': is_unarrive_intime,
                'is_unrecord_logistic': is_unrecord_logistic,
                'supplier': aggregate_orders[0]['supplier']
            })

        return aggregate_dict_list


    def aggregate_supplier_data(self):
        aggregate_datas = self.aggregate_data()
        aggregate_supplier_dict = {}

        for aggregate_order in aggregate_datas:
            supplier_id = aggregate_order['supplier']['id']
            if supplier_id in aggregate_supplier_dict:
                aggregate_supplier_dict[supplier_id]['purchase_orders'].append(aggregate_order)
            else:
                aggregate_supplier_dict[supplier_id] = {
                    'supplier': aggregate_order['supplier'],
                    'aggregate_orders': [aggregate_order]
                }

        aggregate_supplier_list = aggregate_supplier_dict.values()
        return aggregate_supplier_list














