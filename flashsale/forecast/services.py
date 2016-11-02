# coding: utf-8

import datetime
from collections import defaultdict
from django.db import transaction
from django.forms import model_to_dict
from django.db.models import Sum, Avg, Min
from django.core.cache import cache

from . import serializers
from .models import (
    ForecastInbound,
    gen_subforecast_inbound_no,
    ForecastInboundDetail,
    RealInbound,
    RealInboundDetail
)
from supplychain.supplier.models import SaleSupplier
from core.utils import flatten

import logging
logger = logging.getLogger(__name__)

class AggregateDataException(BaseException):
    pass

def gen_order_group_key(order_ids):
    from flashsale.dinghuo.models import OrderList
    return OrderList.gen_group_key(order_ids)

def get_purchaseorder_data(order_id):

    from flashsale.dinghuo.models import OrderList
    cache_key = '%s_orderlist_id_for_forecast_inbound'% order_id
    order_data = cache.get(cache_key)
    if order_data:
        return order_data

    order = OrderList.objects.get(id=order_id)
    order_data = model_to_dict(order, fields=[
        'id', 'buyer_name', 'receiver', 'sys_status','stage',
        'last_pay_date', 'purchase_total_num', 'order_group_key'
    ])
    order_data['supplier_id'] = order.supplier_id
    order_data['created'] = order.created
    order_data['note'] = order.note
    orderlist_status_map = dict(OrderList.STAGE_CHOICES)
    order_data['sys_status_name'] = orderlist_status_map.get(order_data['stage'])
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
        stage__in=OrderList.STAGING_STAGES
    )
    if staff_name and staff_name.strip():
        order_list = order_list.filter(buyer__username=staff_name)

    order_dict_list = order_list.values(
        'id', 'supplier_id', 'buyer_name', 'receiver', 'created', 'sys_status',
        'last_pay_date', 'note', 'purchase_total_num', 'order_group_key', 'stage'
    )
    orderlist_status_map = dict(OrderList.STAGE_CHOICES)
    for order_data in order_dict_list:
        order_data['sys_status_name'] = orderlist_status_map.get(order_data['stage'])
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

def get_purchaseorders_sku_map_keys(purchase_orderid_list):
    from flashsale.dinghuo.models import OrderList, OrderDetail
    orderdetail_qs = OrderDetail.objects.filter(orderlist__in=purchase_orderid_list)
    orderdetail_values_list = orderdetail_qs.values_list('chichu_id','orderlist__id')
    sku_map_keys = defaultdict(list)
    for sku_id, order_id in orderdetail_values_list:
        sku_map_keys[int(sku_id)].append(order_id)
    return sku_map_keys

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
        bill = br.bill
        br_dict = model_to_dict(bill)
        br_dict['out_amount'] = 0
        br_dict['in_amount']  = 0
        br_dict['type_name'] = bill.get_type_display()
        br_dict['status_name'] = bill.get_status_display()
        br_dict['pay_method_name'] = bill.get_pay_method_display()
        if br_dict['type'] == Bill.PAY:
            br_dict['out_amount'] = br_dict['plan_amount']
        elif br_dict['type'] == Bill.RECEIVE:
            br_dict['in_amount'] = br_dict['plan_amount']
        bill_list.append(br_dict)
    return bill_list

@transaction.atomic
def strip_forecast_inbound(forecast_inbound_id):
    """ 将预测到货单商未到货的商品剥离出来 """
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
        new_forecast.forecast_no = gen_subforecast_inbound_no(forecast_inbound.forecast_no)
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

        new_forecast.save()
        return new_forecast
    return None


def recursive_aggragate_orders(order_ids, aggregate_set):
    """ recursive aggregate orderlist """
    unorder_ids = []
    for order_id in order_ids:
        if order_id in aggregate_set:
            continue
        aggregate_set.add(order_id)
        unorder_ids.append(order_id)

    if not unorder_ids:
        return

    forecast_inbounds = get_normal_forecast_inbound_by_orderid(unorder_ids)
    order_ids = forecast_inbounds.values_list('relate_order_set', flat=True)
    recursive_aggragate_orders(order_ids, aggregate_set)

    # aggregate order from real inbound
    real_inbounds = get_normal_realinbound_by_orderid(unorder_ids)
    order_ids = real_inbounds.values_list('relate_order_set', flat=True)
    recursive_aggragate_orders(order_ids, aggregate_set)


class AggregateForcecastOrderAndInbound(object):

    def __init__(self, purchase_orders):
        self.aggregate_orders_dict = {}
        for order_dict in purchase_orders:
            self.aggregate_orders_dict[order_dict['id']] = order_dict
        self.aggregate_set  = set()
        self.supplier_unarrival_dict = {}

    ##################################### discart #####################################
    def recursive_aggragate_order(self, order_id, aggregate_id_set):
        """ discard """
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
            supplier_id = order_data.get('supplier') and order_data['supplier']['id'] or ''
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

    ##################################### status tag #####################################
    def is_arrival_timeout(self, forecast_data):
        tnow = datetime.datetime.now()
        if forecast_data['status'] in (ForecastInbound.ST_APPROVED, ForecastInbound.ST_DRAFT) and \
                (not forecast_data['forecast_arrive_time'] or forecast_data['forecast_arrive_time'] < tnow):
            return True
        if forecast_data['status'] == ForecastInbound.ST_TIMEOUT:
            return True
        return False

    def is_unrecord_logistic(self, forecast_data):
        return forecast_data['status'] in (ForecastInbound.ST_DRAFT, ForecastInbound.ST_APPROVED) \
               and forecast_data['express_code'] == '' and forecast_data['express_no'] == ''

    def is_inthedelivery(self, forecast_data):
        return forecast_data['status'] in (ForecastInbound.ST_DRAFT, ForecastInbound.ST_APPROVED)

    def is_arrival_except(self, forecast_data):
        return forecast_data['has_lack'] or forecast_data['has_defact'] or \
               forecast_data['has_overhead'] or forecast_data['has_wrong']

    ##################################### extras func #####################################

    def get_group_keyset(self):
        return set([ol['order_group_key'] for ol in self.aggregate_orders_dict.values()])

    def flatten_group_keyset(self, group_keyset):
        key_set = flatten([key.strip('-').split('-') for key in group_keyset if key.strip('-')])
        return [int(key) for key in key_set]

    ##################################### core section #####################################

    def aggregate_data(self):
        """根据供应商的订货单分组
        １，　入仓的订货单根据预测单继续聚合分组；
        ２，　未入仓订货单则单独统一分组；　
        """
        if hasattr(self, '_aggregate_data_'):
            return self._aggregate_data_

        aggregate_dict_list = []
        order_group_keyset = self.get_group_keyset()
        order_keylist = self.flatten_group_keyset(order_group_keyset)
        order_keyset  = set(order_keylist)

        supplier_ids = [order['supplier_id'] for order in self.aggregate_orders_dict.values()]
        supplier_values = SaleSupplier.objects.filter(id__in=supplier_ids).values(
            'id', 'supplier_name', 'supplier_code')
        supplier_dict_data = dict([(s['id'], s) for s in supplier_values])

        logger.info('aggregate key len: list=%s, set=%s'%(len(order_keylist), len(order_keyset)))
        forecast_inbounds = ForecastInbound.objects.filter(relate_order_set__in=order_keyset)\
            .exclude(status__in=(ForecastInbound.ST_CANCELED,ForecastInbound.ST_TIMEOUT))
        forecast_values = forecast_inbounds.values(
            'id', 'relate_order_set','supplier_id', 'express_code', 'express_no', 'forecast_arrive_time',
            'total_forecast_num', 'total_arrival_num', 'purchaser', 'status',
            'memo', 'has_lack', 'has_defact', 'has_overhead', 'has_wrong'
        )
        forecast_status_map = dict(ForecastInbound.STATUS_CHOICES)
        aggregate_forecast_dict = defaultdict(list)
        for value in forecast_values:
            value['status_name'] = forecast_status_map.get(value['status'])
            aggregate_forecast_dict[value['relate_order_set']].append(value)

        real_inbounds = RealInbound.objects.filter(relate_order_set__in=order_keyset)\
            .exclude(status=RealInbound.CANCELED)
        realinbound_values = real_inbounds.values(
            'id', 'relate_order_set','supplier_id', 'wave_no', 'ware_house', 'express_code', 'express_no',
            'creator', 'inspector', 'total_inbound_num', 'total_inferior_num', 'created', 'memo', 'status'
        )
        realinbound_status_map = dict(RealInbound.STATUS_CHOICES)
        aggregate_realinbound_dict = defaultdict(list)
        for value in realinbound_values:
            value['status_name'] = realinbound_status_map.get(value['status'])
            aggregate_realinbound_dict[value['relate_order_set']].append(value)

        # TODO value list出所有的预测单及到货单
        for group_key in order_group_keyset:
            aggregate_id_set = self.flatten_group_keyset([group_key])
            if not aggregate_id_set:
                continue
            aggregate_orders = []
            for order_id in aggregate_id_set:
                if order_id in self.aggregate_orders_dict:
                    order_dict = self.aggregate_orders_dict[order_id]
                else:
                    order_dict = get_purchaseorder_data(order_id)
                aggregate_orders.append(order_dict)

            is_unarrive_intime = False
            is_unrecord_logistic = False
            is_billingable = True
            is_arrivalexcept = False
            forecast_orders = flatten([aggregate_forecast_dict.get(key) for key in aggregate_id_set
                                       if aggregate_forecast_dict.has_key(key)])
            distinct_forecast_orders = dict([(fo['id'], fo) for fo in forecast_orders]).values()
            for forecast_data in distinct_forecast_orders:
                forecast_data['is_unarrive_intime']   = self.is_arrival_timeout(forecast_data)
                forecast_data['is_unrecord_logistic'] = self.is_unrecord_logistic(forecast_data)
                is_unarrive_intime |= forecast_data['is_unarrive_intime']
                is_unrecord_logistic |= forecast_data['is_unrecord_logistic']
                is_billingable &= not self.is_inthedelivery(forecast_data)
                is_arrivalexcept |= self.is_arrival_except(forecast_data)

            realinbound_orders = flatten([aggregate_realinbound_dict.get(key) for key in aggregate_id_set
                                          if aggregate_realinbound_dict.has_key(key)])
            distinct_realinbound_orders = dict([(fo['id'], fo) for fo in realinbound_orders]).values()

            aggregate_dict_list.append({
                'order_group_key': group_key,
                'purchase_orders': aggregate_orders,
                'forecast_inbounds': distinct_forecast_orders,
                'real_inbounds': distinct_realinbound_orders,
                'is_unarrive_intime': is_unarrive_intime,
                'is_unrecord_logistic': is_unrecord_logistic,
                'is_billingable': is_billingable,
                'is_arrivalexcept': is_arrivalexcept,
                'supplier': supplier_dict_data.get(aggregate_orders[0]['supplier_id'])
            })
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














