# coding: utf-8

import datetime
from django.db import transaction
from django.forms import model_to_dict
from django.db.models import Sum, Avg, Min
from django.core.cache import cache

from . import serializers
from .models import (
    ForecastInbound,
    default_forecast_inbound_no,
    ForecastInboundDetail,
    RealInbound,
    RealInboundDetail
)

class AggregateDataException(BaseException):
    pass


def get_purchaseorder_data(order_id):

    from flashsale.dinghuo.models import OrderList
    cache_key = '%s_orderlist_id_for_forecast_inbound'% order_id
    order_data = cache.get(cache_key)
    if order_data:
        return order_data

    order = OrderList.objects.get(id=order_id)
    order_details = order.order_list.all()
    detail_dict_list = []
    for detail in order_details:
        detail_dict = {
            'id': detail.id,
            'product_id': detail.product_id,
            'sku_id': detail.chichu_id,
            'product_name': detail.product_name,
            'sku_name': detail.product_chicun,
            'purchase_num': detail.buy_quantity
        }
        detail_dict_list.append(detail_dict)
    pt = order.last_pay_date
    pt = pt and datetime.datetime(pt.year, pt.month, pt.day)
    order_data = {
        'id': order.id,
        'supplier': serializers.SupplierSerializer(order.supplier).data,
        'purchaser': order.buyer_name,
        'post_district': order.p_district,
        'receiver': order.receiver,
        'created': order.created,
        'purchase_time': pt,
        'memo': order.note,
        'sys_status': order.sys_status,
        'sys_status_name': order.status_name,
        'total_detail_num': order.total_detail_num
    }
    cache.set(cache_key, order_data, 60)
    return order_data

def get_purchaseorder_detail_data(orderid_list):

    from flashsale.dinghuo.models import OrderDetail
    details = OrderDetail.objects.filter(
        orderlist__in=orderid_list
    )
    return details.values('id','chichu_id', 'product_id', 'buy_unitprice', 'buy_quantity')


def filter_pending_purchaseorder(staff_name=None,  **kwargs):
    """ 通过采购员名称获取订货单 """
    from flashsale.dinghuo.models import OrderList, OrderDetail
    order_list = OrderList.objects.filter(
        sys_status__in=[OrderList.ST_APPROVAL, OrderList.ST_BILLING]
    )
    if staff_name and staff_name.strip():
        order_list = order_list.filter(buyer__username=staff_name)

    order_ids = order_list.values_list('id', flat=True)
    order_dict_list = []
    for order_id in order_ids:
        order_dict = get_purchaseorder_data(order_id)
        order_dict_list.append(order_dict)

    return order_dict_list


def get_normal_forecast_inbound_by_orderid(purchase_orderid_list):
    # TODO : caution many to many manager filter will not include other object related
    forecast_ids = ForecastInbound.objects.filter(relate_order_set__in=purchase_orderid_list)\
        .exclude(status=ForecastInbound.ST_CANCELED).values_list('id',flat=True)
    return ForecastInbound.objects.filter(id__in=forecast_ids)


def get_normal_realinbound_by_orderid(purchase_orderid_list):
    # TODO : caution many to many manager filter will not include other object related
    rb_ids = RealInbound.objects.filter(relate_order_set__in=purchase_orderid_list,
                                               status__in=(RealInbound.STAGING,RealInbound.COMPLETED))
    return RealInbound.objects.filter(id__in=rb_ids)


def get_normal_realinbound_by_forecastid(forecastid_list):
    # TODO : caution many to many manager filter will not include other object related
    rb_ids = RealInbound.objects.filter(forecast_inbound_id__in=forecastid_list,
                                               status__in=(RealInbound.STAGING,RealInbound.COMPLETED))
    return RealInbound.objects.filter(id__in=rb_ids)

def get_purchaseorders_data(purchase_orderid_list):
    from flashsale.dinghuo.models import OrderList, OrderDetail
    orderdetail_qs = OrderDetail.objects.filter(orderlist__in=purchase_orderid_list)
    orderdetail_values = orderdetail_qs.values('chichu_id','orderlist__supplier_id').annotate(
        buy_quantity=Sum('buy_quantity'),
        total_price=Sum('total_price'),
        min_created=Min('created'),
    )
    return orderdetail_values

def get_realinbounds_data(purchase_orderid_list):
    inbound_qs = get_normal_realinbound_by_orderid(purchase_orderid_list)
    inbound_details_qs = RealInboundDetail.objects.filter(inbound__in=inbound_qs,
                                                          status=RealInboundDetail.NORMAL)
    real_inbound_values = inbound_details_qs.values('sku_id').annotate(
            arrival_quantity=Sum('arrival_quantity'),
            inferior_quantity=Sum('inferior_quantity')
        )
    return real_inbound_values

def get_returngoods_data(supplier_ids, start_from):
    from flashsale.dinghuo.models import RGDetail, ReturnGoods
    rgdetail_qs = RGDetail.objects.filter(return_goods__supplier_id__in=supplier_ids,
                                          created__gt=start_from)
    rgdetail_values = rgdetail_qs.values('skuid').annotate(
            return_num=Sum('num'),
            inferior_num=Sum('inferior_num'),
            price=Avg('price')
        )
    return rgdetail_values

def get_bills_list(purchase_orderids):
    from flashsale.finance.models import BillRelation, Bill
    from django.contrib.contenttypes.models import ContentType
    orderlist_contenttype = ContentType.objects.filter(app_label="dinghuo", model="OrderList").first()
    bill_relates = BillRelation.objects.filter(object_id__in=purchase_orderids,
                                              content_type=orderlist_contenttype).select_related('bill')
    bill_list = []
    for br in bill_relates:
        br_dict = model_to_dict(br.bill)
        br_dict['out_amount'] = 0
        br_dict['in_amount']  = 0
        br_dict['type_name'] = br.get_type_display()
        br_dict['status_name'] = br.get_status_display()
        br_dict['pay_method_name'] = br.get_pay_method_display()
        if br_dict['type'] == Bill.PAY:
            br_dict['out_amount'] = br_dict['plan_amount']
        elif br_dict['type'] == Bill.RECEIVE:
            br_dict['in_amount'] = br_dict['plan_amount']
        bill_list.append(br_dict)
    return bill_list

@transaction.atomic
def strip_forecast_inbound(forecast_inbound_id):

    forecast_inbound = ForecastInbound.objects.get(id=forecast_inbound_id)

    # 如果有多个到货单关联一个预测单，需要聚合计算
    real_inbound_details_qs = RealInboundDetail.objects.filter(inbound__forecast_inbound=forecast_inbound,
                                                               status=RealInboundDetail.NORMAL)
    real_inbound_qs_values = real_inbound_details_qs.values('sku_id')\
        .annotate(total_arrival_num=Sum('arrival_quantity'),total_inferior_num=Sum('inferior_quantity'))
    real_inbound_detail_dict = dict([(d['sku_id'], d) for d in real_inbound_qs_values])

    sku_delta_dict = {}
    for detail in forecast_inbound.normal_details:
        real_detail = real_inbound_detail_dict.get(detail.sku_id, None)
        real_arrive_num = real_detail and real_detail.get('total_arrival_num', 0) or 0
        delta_arrive_num = detail.forecast_arrive_num - real_arrive_num
        if delta_arrive_num > 0:
            sku_delta_dict[detail.sku_id] = delta_arrive_num

    if sku_delta_dict:
        update_fields = ['supplier_id', 'ware_house', 'express_code', 'express_no']
        new_forecast = ForecastInbound()
        new_forecast.forecast_no = default_forecast_inbound_no('sub%d' % forecast_inbound.id)
        for k in update_fields:
            if hasattr(forecast_inbound, k):
                setattr(new_forecast, k, getattr(forecast_inbound, k))
        new_forecast.save()

        for order in forecast_inbound.relate_order_set.all():
            new_forecast.relate_order_set.add(order)

        for detail in forecast_inbound.normal_details:
            delta_arrive_num = sku_delta_dict.get(detail.sku_id, 0)
            if delta_arrive_num > 0:
                forecast_detail = ForecastInboundDetail()
                forecast_detail.forecast_inbound = new_forecast
                forecast_detail.forecast_arrive_num = delta_arrive_num
                forecast_detail.product_id = detail.product_id
                forecast_detail.sku_id = detail.sku_id
                forecast_detail.product_name = detail.product_name
                forecast_detail.product_img = detail.product_img
                forecast_detail.save()
        return new_forecast
    return None


class AggregateForcecastOrderAndInbound(object):

    def __init__(self, purchase_orders):
        self.aggregate_orders_dict = {}
        for order_dict in purchase_orders:
            self.aggregate_orders_dict[order_dict['id']] = order_dict
        self.aggregate_set  = set()
        self.supplier_unarrival_dict = {}

    def recursive_aggragate_order(self, order_id, aggregate_id_set):

        if order_id in self.aggregate_set:
            return
        self.aggregate_set.add(order_id)

        # aggregate order from forecast inbound
        forecast_inbounds = get_normal_forecast_inbound_by_orderid([order_id])
        order_ids = forecast_inbounds.values_list('relate_order_set',flat=True)
        for fi_order_id in order_ids:
            self.recursive_aggragate_order(fi_order_id, aggregate_id_set)
        # aggregate order from real inbound
        real_inbounds = get_normal_realinbound_by_orderid([order_id])
        order_ids = real_inbounds.values_list('relate_order_set', flat=True)
        for ri_order_id in order_ids:
            self.recursive_aggragate_order(ri_order_id, aggregate_id_set)
        # aggregate all inbound unarrival together
        if real_inbounds.exists():
            aggregate_id_set.add(order_id)
        else:
            order_data = get_purchaseorder_data(order_id)
            supplier_id = order_data['supplier']['id']
            if supplier_id in self.supplier_unarrival_dict:
                self.supplier_unarrival_dict[supplier_id].add(order_id)
            else:
                self.supplier_unarrival_dict[supplier_id] = set([order_id])


    def aggregate_order_set(self):
        """ aggregate order id to set and return set list """
        aggregate_set_list = []
        for order_id in self.aggregate_orders_dict.keys():
            if order_id in self.aggregate_set:
                continue
            aggregate_id_set = set()
            self.recursive_aggragate_order(order_id, aggregate_id_set)
            if aggregate_id_set:
                aggregate_set_list.append(aggregate_id_set)

        aggregate_set_list.extend(self.supplier_unarrival_dict.values())
        return aggregate_set_list

    def aggregate_data(self):
        """根据供应商的订货单分组
        １，　入仓的订货单根据预测单继续聚合分组；
        ２，　未入仓订货单则单独统一分组；　
        """
        if hasattr(self, '_aggregate_data_'):
            return self._aggregate_data_

        import time
        start_time = time.time()
        aggregate_dict_list = []
        aggregate_set_list = self.aggregate_order_set()

        print 'time1:', time.time() - start_time
        start_time = time.time()
        for aggregate_id_set in aggregate_set_list:
            aggregate_orders = []
            for order_id in aggregate_id_set:
                forecast_inbounds = get_normal_forecast_inbound_by_orderid([order_id])
                if order_id in self.aggregate_orders_dict:
                    order_dict = self.aggregate_orders_dict[order_id]
                else:
                    order_dict = get_purchaseorder_data(order_id)
                order_dict['relate_forecasts'] = forecast_inbounds.values_list('id', flat=True)
                aggregate_orders.append(order_dict)

            aggregate_forecasts = []
            is_unarrive_intime = False
            is_unrecord_logistic = False
            is_billingable = True
            is_arrivalexcept = False

            real_inbound_qs = get_normal_realinbound_by_orderid(aggregate_id_set)
            inbounds_data = serializers.SimpleRealInboundSerializer(real_inbound_qs, many=True).data
            aggregate_inbounds_dict = dict([(ib['id'], ib) for ib in inbounds_data])

            forecast_inbound_qs = get_normal_forecast_inbound_by_orderid(aggregate_id_set)
            for forecast in forecast_inbound_qs:
                forecast_data = serializers.SimpleForecastInboundSerializer(forecast).data

                real_inbound_qs = get_normal_realinbound_by_forecastid([forecast.id])
                inbounds_data = serializers.SimpleRealInboundSerializer(real_inbound_qs, many=True).data

                forecast_data['relate_inbounds']  = real_inbound_qs.values_list('id', flat=True)
                forecast_data['is_unarrive_intime']   = forecast.is_arrival_timeout()
                forecast_data['is_unrecord_logistic'] = forecast.is_unrecord_logistic()
                is_unarrive_intime |= forecast_data['is_unarrive_intime']
                is_unrecord_logistic |= forecast_data['is_unrecord_logistic']
                is_billingable &= not forecast.is_inthedelivery()
                is_arrivalexcept |= forecast.is_arrival_except()

                aggregate_forecasts.append(forecast_data)
                for ib in inbounds_data:
                    if ib['id'] not in aggregate_inbounds_dict:
                        aggregate_inbounds_dict.update({ib['id']:ib})

            aggregate_dict_list.append({
                'purchase_orders': aggregate_orders,
                'forecast_inbounds': aggregate_forecasts,
                'real_inbounds': aggregate_inbounds_dict.values(),
                'is_unarrive_intime': is_unarrive_intime,
                'is_unrecord_logistic': is_unrecord_logistic,
                'is_billingable': is_billingable,
                'is_arrivalexcept': is_arrivalexcept,
                'supplier': aggregate_orders[0]['supplier']
            })

        print 'time2:', time.time() - start_time
        self._aggregate_data_ = aggregate_dict_list
        return self._aggregate_data_


    def aggregate_supplier_data(self, supplier_id=None):
        aggregate_datas = self.aggregate_data()
        aggregate_supplier_dict = {}
        for aggregate_order in aggregate_datas:
            order_supplier_id = aggregate_order['supplier']['id']
            if order_supplier_id in aggregate_supplier_dict:
                aggregate_supplier_dict[order_supplier_id]['aggregate_orders'].append(aggregate_order)
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














