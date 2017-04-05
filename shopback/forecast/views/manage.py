# coding: utf8
from __future__ import absolute_import, unicode_literals

import os
import json
import datetime
from collections import  defaultdict

from django.db import models
from django.db import transaction
from django.core.urlresolvers import reverse
from django.forms import model_to_dict

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from rest_framework import filters
from rest_framework.parsers import JSONParser
from rest_framework.decorators import parser_classes

from core.utils import flatten
from shopback.items.models import Product, ProductSku, ProductLocation, SkuStock


from ..models import (
    StagingInBound,
    ForecastInbound,
    ForecastInboundDetail,
    RealInbound,
    RealInboundDetail,
    ForecastStats
)
from .. import serializers
from .. import services

import logging
logger = logging.getLogger(__name__)


CACHE_VIEW_TIMEOUT = 30

class ForecastManageViewSet(viewsets.ModelViewSet):
    """
        预测到货单管理后台
    """
    queryset = ForecastInbound.objects.all()
    serializer_class = serializers.ForecastInboundSerializer
    authentication_classes = (authentication.BasicAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer,)

    def get_main_queryset(self, request):
        user_name = request.user.username
        return self.queryset.filter(creator=user_name)

    def get_img_display_url(self, img_url):
        return img_url + '?imageMogr2/strip/format/jpg/quality/90/interlace/1/thumbnail/80/'

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        forecast_ids_str  = request.GET.get('forecast_ids','')
        forecast_ids = [s for s in forecast_ids_str.split(',') if s.isdigit()]
        if len(forecast_ids) > 0:
            queryset = queryset.filter(id__in=forecast_ids)
        else:
            queryset = queryset.none()

        forecast_details = []
        for forecast in queryset:
            forecast_data = serializers.SimpleForecastInboundSerializer(forecast).data
            detail_products = []
            product_ids = forecast.details_manager.filter(status=ForecastInboundDetail.NORMAL)\
                .values_list('product_id',flat=True).distinct()
            for pid in product_ids:
                product = Product.objects.get(id=pid)
                product_num = 0
                detail_skus = []
                forecast_skus = forecast.normal_details.filter(product_id=pid)
                for forecast_sku in forecast_skus:
                    product_sku = ProductSku.objects.get( id=forecast_sku.sku_id)
                    product_num += forecast_sku.forecast_arrive_num
                    detail_skus.append({
                        'sku_id': product_sku.id,
                        'sku_name': product_sku.name,
                        'forecast_arrive_num':forecast_sku.forecast_arrive_num
                    })
                product_data = {
                    'product_id': product.id,
                    'product_code': product.outer_id,
                    'product_name': product.name,
                    'product_img': self.get_img_display_url(product.pic_path),
                    'product_num': product_num,
                    'detail_skus': detail_skus
                }
                detail_products.append(product_data)

            forecast_data['detail_products'] = detail_products
            forecast_details.append(forecast_data)

        return Response({'forecast_inbounds':forecast_details,
                         'supplier': forecast_details and forecast_details[0]['supplier'] or {}
                         },template_name='forecast/forecast_manage.html')

    @list_route(methods=['post'])
    def create_or_split_forecast(self, request, *args, **kwargs):

        content = request.POST
        datas = json.loads(content.get('forecast_data', '{}'))
        forecast_ids = set()
        forecast_data_list = []
        logger.debug('data:%s' % datas)
        for kstr, num in datas.iteritems():
            sku_id, product_id, forecast_id, k1, k2 = kstr.split('-')
            forecast_ids.add(int(forecast_id))
            forecast_data_list.append([int(sku_id), int(product_id), int(forecast_id), int(num)])

        forecast_qs = ForecastInbound.objects.filter(id__in=(forecast_ids))
        forecast_obj = forecast_qs.first()
        origin_inbounds = set()
        for forecast in forecast_qs:
            if forecast.supplier != forecast_obj.supplier:
                raise exceptions.APIException('multi supplier found')
            for inbound in forecast.relate_order_set.all():
                origin_inbounds.add(inbound)
        if not forecast_obj:
            raise exceptions.APIException('no forecast inbound found')

        with transaction.atomic():
            forecast_arrive_time = content.get('forecast_arrive_time', None)
            forecast_newobj = ForecastInbound(supplier=forecast_obj.supplier)
            forecast_objdict = model_to_dict(forecast_obj)
            for name, value in forecast_objdict.iteritems():
                if name not in ('purchaser', 'ware_house'): continue
                setattr(forecast_newobj, name, value)
            forecast_newobj.supplier = forecast_obj.supplier
            forecast_newobj.forecast_arrive_time = forecast_arrive_time
            forecast_newobj.save()

            for inbound in origin_inbounds:
                forecast_newobj.relate_order_set.add(inbound)

            for obj in forecast_data_list:
                detail = ForecastInboundDetail.objects.filter(forecast_inbound_id=obj[2],
                                                              product_id=obj[1], sku_id=obj[0]).first()
                if not detail or detail.forecast_arrive_num < obj[3]:
                    raise exceptions.APIException('trans num bigger than forecast arrive num:%s' % (obj))
                if detail.forecast_arrive_num <= obj[3]:
                    detail.status = ForecastInboundDetail.DELETE
                detail.forecast_arrive_num = models.F('forecast_arrive_num') - obj[3]
                detail.save(update_fields=['forecast_arrive_num', 'status'])

                forecast_detail = ForecastInboundDetail.objects.filter(forecast_inbound=forecast_newobj,
                                                        sku_id=obj[0]).first()
                if not forecast_detail:
                    forecast_detail = ForecastInboundDetail(forecast_inbound=forecast_newobj, sku_id=obj[0])
                forecast_detail.product_id = obj[1]
                forecast_detail.forecast_arrive_num = forecast_detail.forecast_arrive_num + obj[3]
                forecast_detail.product_name = detail.product_name
                forecast_detail.product_img = detail.product_img
                forecast_detail.save()
            forecast_newobj.save()

        for forecast in forecast_qs:
            if forecast.total_detail_num == 0:
                forecast.unarrive_close_update_status()
            forecast.save()

        # serializer_data = self.get_serializer(forecast_newobj).data
        return Response({'redirect_url': reverse(
            'admin:forecast_forecastinbound_changelist') + '?supplier_id=%s' % forecast_newobj.supplier_id})


    @list_route(methods=['post'])
    @parser_classes(JSONParser)
    def create_or_split_multiforecast(self, request, *args, **kwargs):

        datas = request.data
        orderlist_ids = [int(s) for s in datas.get('order_group_key').split('-') if s.isdigit()]
        forecast_data_list = datas.get('forecast_orders')
        for data in forecast_data_list:
            for k,v in data.iteritems():
                data[k] = int(v)

        forecast_inbounds = ForecastInbound.objects.filter(relate_order_set__in=orderlist_ids)
        forecast_inbounds_orderlist = forecast_inbounds.values_list('id', 'relate_order_set')
        forecast_obj = forecast_inbounds.first()
        if not forecast_obj:
            raise exceptions.APIException('no forecast inbound found')

        if not forecast_data_list:
            return Response({'redirect_url': reverse(
                'admin:forecast_forecastinbound_changelist') + '?supplier_id=%s' %forecast_obj.supplier_id})

        forecast_order_skuids = set([o['sku_id'] for o in forecast_data_list])
        forecast_detail_values= ForecastInboundDetail.objects.filter(forecast_inbound__in=forecast_inbounds,
                                             sku_id__in=forecast_order_skuids,
                                             forecast_inbound__status__in=(ForecastInbound.ST_ARRIVED,ForecastInbound.ST_FINISHED),
                                             status=ForecastInboundDetail.NORMAL)\
                            .values('sku_id', 'product_name', 'product_img', 'forecast_inbound_id', 'forecast_arrive_num')
        forecast_details_dict = defaultdict(list)
        for forecast_detail in forecast_detail_values:
            forecast_details_dict[forecast_detail['sku_id']].append(forecast_detail)
        forecast_ids = set([fo['forecast_inbound_id'] for fo in flatten(forecast_details_dict.values())])

        with transaction.atomic():
            forecast_arrive_time = datetime.datetime.now() + datetime.timedelta(days=3)
            forecast_newobj = ForecastInbound(supplier=forecast_obj.supplier)
            forecast_objdict = model_to_dict(forecast_obj)
            for name ,value in forecast_objdict.iteritems():
                if name not in ('purchaser', 'ware_house'):continue
                setattr(forecast_newobj,name,value)
            forecast_newobj.supplier = forecast_obj.supplier
            forecast_newobj.forecast_arrive_time = forecast_arrive_time
            forecast_newobj.save()

            relate_orderlist_ids = set([s[1] for s in forecast_inbounds_orderlist if s[0] in forecast_ids])
            for orderlist_id in relate_orderlist_ids:
                forecast_newobj.relate_order_set.add(orderlist_id)

            # TODO@meron
            for obj in forecast_data_list:
                forecast_details_list = forecast_details_dict.get(obj['sku_id'], [])
                total_forecast_num = sum([s['forecast_arrive_num'] for s in forecast_details_list])
                if total_forecast_num < obj['num']:
                    raise exceptions.APIException(u'新建数量不能大于总预测数量')
                detail = forecast_details_list[0]
                forecast_detail = ForecastInboundDetail()
                forecast_detail.forecast_inbound = forecast_newobj
                forecast_detail.product_id = obj['product_id']
                forecast_detail.sku_id = obj['sku_id']
                forecast_detail.forecast_arrive_num = obj['num']
                forecast_detail.product_name = detail['product_name']
                forecast_detail.product_img = detail['product_img']
                forecast_detail.save()
            forecast_newobj.save()

        # serializer_data = self.get_serializer(forecast_newobj).data
        return Response({'redirect_url': reverse('admin:forecast_forecastinbound_changelist')+'?supplier_id=%s'%forecast_newobj.supplier_id})

    @list_route(methods=['get'])
    def dashboard(self, request, *args, **kwargs):
        """
        action: (all, 全部), (unarrived, 未准时到货), (unbilling, 到货等待结算), (unlogisticed, 未填写物流信息),
        """
        data = request.GET
        action = data.get('action', 'all')
        staff_name = data.get('staff_name', '')

        logger.info('forecast aggregate start:%s' % datetime.datetime.now())
        purchase_orders = services.filter_pending_purchaseorder(**{'staff_name': staff_name})
        logger.info('forecast aggregate middle:%s' % datetime.datetime.now())
        aggregate_forecast_obj = services.AggregateForcecastOrderAndInbound(purchase_orders)
        logger.info('forecast aggregate end:%s' % datetime.datetime.now())
        aggregate_list_dict = {
            'unlogisticed': [],
            'unarrived': [],
            'arrivalexcept': [],
            'billingable': [],
        }
        aggregate_datas = aggregate_forecast_obj.aggregate_data()
        for aggregate in aggregate_datas:
            if aggregate['is_unrecord_logistic']:
                aggregate_list_dict['unlogisticed'].append(aggregate)
            if aggregate['is_unarrive_intime']:
                aggregate_list_dict['unarrived'].append(aggregate)
            if aggregate['is_arrivalexcept']:
                aggregate_list_dict['arrivalexcept'].append(aggregate)
            if aggregate['is_billingable']:
                aggregate_list_dict['billingable'].append(aggregate)

        is_handleable = action in ('unlogisticed', 'unarrived', 'billingable', 'arrivalexcept')
        if is_handleable:
            aggregate_record_list = aggregate_list_dict[action]
        else:
            supplier_id = data.get('supplier_id')
            if supplier_id and supplier_id.isdigit():
                aggregate_record_list = aggregate_forecast_obj.aggregate_supplier_data(supplier_id=supplier_id)
            else:
                aggregate_record_list = aggregate_forecast_obj.aggregate_supplier_data()

        return Response({'aggregate_list': aggregate_record_list,
                         'unlogistics_num': len(aggregate_list_dict['unlogisticed']),
                         'unarrived_num': len(aggregate_list_dict['unarrived']),
                         'arrivalexcept_num': len(aggregate_list_dict['arrivalexcept']),
                         'billingable_num': len(aggregate_list_dict['billingable']),
                         'aggregate_num': is_handleable and len(aggregate_datas) or len(aggregate_record_list),
                         'action': action,
                         'staff_name': staff_name},
                        template_name='forecast/dashboard.html')

    @list_route(methods=['get'])
    def calcstats(self, request, *args, **kwargs):
        """ 采购单与入库单聚合结算 """

        order_group_key = request.GET.get('order_group_key', '')
        purchase_orderid_list = [int(i) for i in order_group_key.split('-') if i]

        orderdetail_values = services.get_purchaseorders_data(purchase_orderid_list)
        inbounddetail_values = services.get_realinbounds_data(purchase_orderid_list)
        order_sku_map_keys = services.get_purchaseorders_sku_map_keys(purchase_orderid_list)

        order_details_dict = {}
        for od in orderdetail_values:
            sku_id = int(od['chichu_id'])
            order_details_dict[sku_id] = od

        inbound_details_dict = {}
        for ib_detail in inbounddetail_values:
            order_details_dict.setdefault(ib_detail['sku_id'],{
                'chichu_id': str(ib_detail['sku_id']),
                'buy_quantity': 0,
                'total_price': 0,
            })
            inbound_details_dict.setdefault(ib_detail['sku_id'], ib_detail)

        sku_id_set = set(order_details_dict.keys())
        sku_id_set.update(inbound_details_dict.keys())
        sku_values = []
        productsku_values = ProductSku.objects.filter(id__in=sku_id_set).select_related('product').values(
            'id', 'product_id', 'product__outer_id', 'product__name',
            'properties_name', 'properties_alias', 'product__pic_path'
        )
        # sku_stats_values = SkuStock.objects.filter(sku__in=sku_id_set).extra(
        #     select={'excess_num': "history_quantity + inbound_quantity + return_quantity "
        #                           + "+ sold_num - post_num - rg_quantity - post_num"}
        # ).values_list('id','excess_num')
        # sku_stats_dict = dict(sku_stats_values)
        for sku_val in productsku_values:
            sku_values.append({
                'sku_id': sku_val['id'],
                'outer_id': sku_val['product__outer_id'],
                'product_id': sku_val['product_id'],
                'product_name': sku_val['product__name'],
                'sku_name': sku_val['properties_name'] or sku_val['properties_alias'],
                'product_img': sku_val['product__pic_path'],
            })
        product_details_dict = dict([(s['sku_id'], s) for s in sku_values])

        supplier_ids = set([s['orderlist__supplier_id'] for s in orderdetail_values])
        min_datetime = orderdetail_values and orderdetail_values[0]['min_created'] or datetime.datetime.now()
        returngood_details = services.get_returngoods_data(supplier_ids, min_datetime)
        returngood_details_dict = dict([(rg['skuid'], rg) for rg in returngood_details])
        aggregate_details_list = []
        for sku_id, odetail in order_details_dict.iteritems():
            sku_detail = product_details_dict.get(sku_id, {})
            inbound_detail = inbound_details_dict.get(sku_id, {})
            rg_detail = returngood_details_dict.get(sku_id, {})
            arrived_num = inbound_detail and inbound_detail['arrival_quantity'] or 0
            return_num = rg_detail and (rg_detail['return_num'] + rg_detail['inferior_num']) or 0
            per_price  = odetail['buy_quantity'] and \
                        round(float(odetail['total_price']) / odetail['buy_quantity'], 2) or 0
            unwork_num = odetail['buy_quantity'] - arrived_num + return_num
            inferior_num = inbound_detail and inbound_detail['inferior_quantity'] or 0
            unarrival_num = max(0, odetail['buy_quantity'] + inferior_num - arrived_num)
            excess_num  = abs(min(0, odetail['buy_quantity'] - arrived_num + inferior_num))
            # 如果到货超出预订，则计算未到货数量时需考虑次品
            sku_detail.update({
                'buy_num': odetail['buy_quantity'],
                'total_price': odetail['total_price'],
                'delta_num': unarrival_num,
                'excess_num': excess_num,
                'real_payment': odetail['total_price'],
                'arrival_num': inbound_detail and inbound_detail['arrival_quantity'] or 0,
                'inferior_num': inferior_num,
                'return_num': return_num,
                'return_inferior_num': rg_detail and rg_detail['inferior_num'] or 0,
                'return_amount': max(unwork_num * per_price, 0),
                'orderlist_ids': order_sku_map_keys.get(sku_id)
            })
            aggregate_details_list.append(sku_detail)

        # TODO 付款单金额统计
        bill_list = services.get_bills_list(purchase_orderid_list)
        total_in_amount = bill_list and sum([br['in_amount'] for br in bill_list]) or 0
        total_out_amount = bill_list and sum([br['out_amount'] for br in bill_list]) or 0
        return Response(
            {'aggregate_details': aggregate_details_list,
             'order_group_key': order_group_key,
             'bill_data': {
                 'bills': bill_list,
                 'total_in_amount': total_in_amount,
                 'total_out_amount': total_out_amount
             }},
            template_name='forecast/aggregate_billing_detail.html'
        )

