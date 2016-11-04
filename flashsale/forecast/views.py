# -*- coding:utf-8 -*-
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
import django_filters

from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer

from common.utils import get_admin_name
from core.options import log_action, ADDITION, CHANGE
from core.utils import flatten
from shopback.items.models import Product, ProductSku, ProductLocation, SkuStock
from supplychain.supplier.models import SaleProduct

from .models import (
    StagingInBound,
    ForecastInbound,
    ForecastInboundDetail,
    RealInbound,
    RealInboundDetail,
    ForecastStats
)
from . import serializers
from shopback.warehouse import constants
from . import services

import logging
logger = logging.getLogger(__name__)


CACHE_VIEW_TIMEOUT = 30

def gen_uniq_staging_inbound_record_id(username, supplier_id, ware_house, sku_id):
    return '%s-%s-%s-%s'%(username, supplier_id, ware_house, sku_id)

class StagingInboundViewSet(viewsets.ModelViewSet):
    """
        预测到货单入仓操作
    """
    queryset = StagingInBound.objects.filter(status=StagingInBound.STAGING)

    serializer_class = serializers.StagingInBoundSerializer
    authentication_classes = (authentication.BasicAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer,)

    template_name = 'forecast/forecast_inbound.html'

    def get_main_queryset(self, request):
        return self.queryset.filter(creator=get_admin_name(request.user))

    def list(self, request, *args, **kwargs):
        data = request.REQUEST
        forecast_inbound_id = data.get('forecast_inbound_id')
        forecast_inbound = None

        forecast_inbound_data = {}
        aggregate_product_set = set()
        # aggregate forecast inbound product_ids
        if forecast_inbound_id and forecast_inbound_id.isdigit():
            forecast_inbound = ForecastInbound.objects.filter(id=forecast_inbound_id).first()
            record_product_ids = forecast_inbound.details_manager.values_list('product_id', flat=True)
            aggregate_product_set.update(record_product_ids)
        # aggregate staging inbound product_ids
        staging_inbounds = self.get_main_queryset(request)
        staging_product_ids = staging_inbounds.values_list('product_id', flat=True)
        aggregate_product_set.update(staging_product_ids)

        if forecast_inbound:
            forecast_inbound_data = serializers.SimpleForecastInboundSerializer(forecast_inbound).data

        aggregate_records = []
        for product_id in aggregate_product_set:
            product = Product.objects.filter(id=product_id).get()
            saleproduct = SaleProduct.objects.filter(id=product.sale_product).first()
            record_skus = []
            for sku in product.normal_skus:
                record_dict = {
                    'record_id':0,
                    'sku_id':sku.id,
                    'forecast_arrive_num': 0,
                    'sku_name':sku.name,
                    'barcode':sku.BARCODE,
                    'is_forecasted': False,
                    'is_record': False,
                    'creator': '',
                    'record_num': 0,
                }
                if forecast_inbound:
                    forecast_detail = forecast_inbound.details_manager.filter(
                        product_id=product_id, sku_id=sku.id).first()
                    if forecast_detail:
                        record_dict.update({
                            'forecast_arrive_num': forecast_detail.forecast_arrive_num,
                            'is_forecasted': True,
                        })
                record_inbound = staging_inbounds.filter(product_id=product_id, sku_id=sku.id).first()
                if record_inbound:
                    record_dict.update({
                        'record_id': record_inbound.id,
                        'record_num': record_inbound.record_num,
                        'is_record': True,
                        'creator': record_inbound.creator
                    })
                record_skus.append(record_dict)

            aggregate_records.append({
                'product_id': product.id,
                'ware_house': product.ware_by,
                'ware_house_name':product.get_ware_by_display(),
                'product_name': product.name,
                'product_img': product.PIC_PATH,
                'product_link': saleproduct and saleproduct.product_link or '',
                'sku_list': record_skus
            })
        return Response({'records': aggregate_records, 'forecast_inbound':forecast_inbound_data})

    @list_route(methods=['post'])
    def save_staging_records(self, request):
        from .models import gen_uniq_staging_inbound_record_id

        staging_records = json.loads(request.POST['staging_records'])
        forecast_inbound_id = request.POST['forecast_inbound_id']
        forecast_inbound = ForecastInbound.objects.get(id=forecast_inbound_id)
        supplier_id = forecast_inbound.supplier_id

        for staging_record in staging_records:
            record_id = staging_record['record_id']
            if record_id:
                record = StagingInBound.objects.get(id=record_id)
                record.record_num = staging_record['record_num']
                record.save()
            else:
                product_id = staging_record['product_id']
                sku_id = staging_record['sku_id']
                product = Product.objects.get(id=product_id)
                creator = get_admin_name(request.user)

                staging_inbound = StagingInBound(
                    forecast_inbound=forecast_inbound,
                    supplier_id=supplier_id,
                    ware_house=product.ware_by,
                    product_id=product_id,
                    sku_id=sku_id,
                    record_num=staging_record['record_num'],
                    uniq_key=gen_uniq_staging_inbound_record_id(supplier_id, product.ware_by, creator, sku_id),
                    creator=creator
                )
                staging_inbound.save()
        return Response('OK')


class InBoundViewSet(viewsets.ModelViewSet):
    queryset = RealInbound.objects.all()
    authentication_classes = (authentication.BasicAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer,)

    def retrieve(self, request, pk=None):
        inbound = RealInbound.objects.get(id=pk)

        skus_dict = {}
        for inbounddetail in inbound.inbound_detail_manager.filter(status=RealInboundDetail.NORMAL).order_by('id'):
            skus_dict[inbounddetail.sku_id] = {
                'arrival_quantity': inbounddetail.arrival_quantity,
                'inferior_quantity': inbounddetail.inferior_quantity
            }

        saleproduct_ids = set()
        products_dict = {}
        for sku in ProductSku.objects.select_related('product').filter(id__in=skus_dict.keys()):
            product = sku.product
            saleproduct_ids.add(product.sale_product)
            if product.id in products_dict:
                product_dict = products_dict[product.id]
            else:
                product_dict = {
                    'id': sku.product.id,
                    'saleproduct_id': sku.product.sale_product,
                    'name': product.name,
                    'outer_id': product.outer_id,
                    'pic_path': product.PIC_PATH,
                    'ware_by': product.ware_by,
                    'skus': {}
                }
                products_dict[product.id] = product_dict
            sku_dict = {
                'id': sku.id,
                'properties_name': sku.properties_name or sku.properties_alias,
                'barcode': sku.barcode,
                'districts': []
            }
            for product_location in ProductLocation.objects.select_related('district').filter(product_id=sku.product.id, sku_id=sku.id):
                sku_dict['districts'].append(str(product_location.district))
            sku_dict.update(skus_dict[sku.id])
            product_dict['skus'][sku.id] = sku_dict
        saleproducts_dict = {}
        for saleproduct in SaleProduct.objects.filter(id__in=list(saleproduct_ids)):
            saleproducts_dict[saleproduct.id] = saleproduct.product_link
        products = []
        for product_dict in sorted(products_dict.values(), key=lambda x: x['id']):
            product_dict['skus'] = sorted(product_dict['skus'].values(), key=lambda x: x['id'])
            product_dict['product_link'] = saleproducts_dict.get(product_dict['saleproduct_id']) or ''
            products.append(product_dict)

        if inbound.supplier:
            supplier = {
                'id': inbound.supplier.id,
                'name': inbound.supplier.supplier_name
            }
        else:
            supplier = {
                'id': 0,
                'name': '未知'
            }
        warehouses = [{'value': x, 'text': y} for x,y in constants.WARE_CHOICES]
        inbound = {
            'supplier': supplier,
            'express_no': inbound.express_no,
            'status': dict(RealInbound.STATUS_CHOICES).get(inbound.status) or '待入库',
            'created': inbound.created.strftime('%y年%m月%d %H:%M:%S'),
            'warehouse': dict(constants.WARE_CHOICES).get(inbound.ware_house) or '未选仓',
            'forecast_inbound_id': inbound.forecast_inbound.id if inbound.forecast_inbound else '',
            'creator': inbound.creator
        }
        result = {
            'products': products,
            'inbound': inbound,
            'warehouses': warehouses
        }
        return Response(result, template_name='forecast/real_inbound.html')


    def create(self, request):
        records = json.loads(request.REQUEST['records'])
        forecast_inbound_id = int(request.REQUEST['forecast_inbound_id'])

        forecast_inbound = ForecastInbound.objects.get(id=forecast_inbound_id)
        supplier_id = forecast_inbound.supplier_id
        real_inbound = RealInbound(
            forecast_inbound=forecast_inbound,
            ware_house=forecast_inbound.ware_house,
            supplier=forecast_inbound.supplier,
            creator=get_admin_name(request.user)
        )
        real_inbound.save()

        for record in records:
            record_id = record['record_id']
            record_num = record['record_num']
            sku_id = record['sku_id']
            product_id = record['product_id']

            if record_id:
                StagingInBound.objects.filter(id=record_id).update(record_num=record_num, status=StagingInBound.COMPLETED)
            if record_num <= 0:
                continue
            sku = ProductSku.objects.get(id=sku_id)
            barcode = sku.barcode
            product_name = sku.product.name
            product_img = sku.product.PIC_PATH
            real_inbound_detail = RealInboundDetail(
                inbound=real_inbound,
                product_id=product_id,
                sku_id=sku_id,
                barcode=barcode,
                product_name=product_name,
                product_img=product_img,
                arrival_quantity=record_num
            )
            real_inbound_detail.save()

        creator = get_admin_name(request.user)
        StagingInBound.objects.filter(forecast_inbound=forecast_inbound,
                                      creator=creator).update(status=StagingInBound.COMPLETED)
        return Response({'real_inbound_id': real_inbound.id})


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
        forecast_ids_str  = request.REQUEST.get('forecast_ids','')
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


class ForecastStatsFilter(filters.FilterSet):
    purchase_time_start = django_filters.DateTimeFilter(name="purchase_time", lookup_type='gte')
    purchase_time_end = django_filters.DateTimeFilter(name="purchase_time", lookup_type='lte')

    class Meta:
        model = ForecastStats
        fields = ['purchase_time_start', 'purchase_time_end']

class ForecastStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ForecastStats.objects.exclude(status=ForecastStats.CLOSED)
    authentication_classes = (authentication.BasicAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.ForecastStatsSerializer
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer, renderers.TemplateHTMLRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    # filter_fields = ('supplier', 'purchase_time', 'buyer_name', 'purchaser')
    # filter_class = ForecastStatsFilter
    template_name = 'forecast/report_stats.html'

    def list(self, request, format=None, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).select_related('supplier')
        start_time = request.GET.get('start_time')
        end_time   = request.GET.get('end_time')
        action = request.GET.get('action')
        if not start_time:
            start_time = datetime.datetime(2016, 6, 1)
        if not end_time:
            end_time = datetime.datetime.now()
        if action == 'arrival_time':
            queryset = queryset.filter(arrival_time__range=(start_time,end_time))
        elif action == 'forecast_time':
            queryset = queryset.filter(forecast_inbound__forecast_arrive_time__range=(start_time, end_time))
        else:
            action = 'purchase_time'
            queryset = queryset.filter(purchase_time__range=(start_time, end_time))

        stats_values = queryset.extra(
            tables=('forecast_inbound','forecast_stats'),
            where=('forecast_stats.forecast_inbound_id = forecast_inbound.id',),
            select = {
                'arrival_period': 'IFNULL(TIMESTAMPDIFF(DAY, forecast_stats.purchase_time, forecast_stats.arrival_time),TIMESTAMPDIFF(DAY, forecast_stats.purchase_time,NOW()))',
                'delivery_period': 'IFNULL(TIMESTAMPDIFF(DAY, forecast_stats.purchase_time, forecast_stats.delivery_time),TIMESTAMPDIFF(DAY, forecast_stats.purchase_time,NOW()))',
                'logistic_period': 'TIMESTAMPDIFF(DAY, forecast_stats.delivery_time, forecast_stats.arrival_time)',
                'forecast_arrive_time': 'IFNULL(DATE_FORMAT(forecast_inbound.forecast_arrive_time, "%%Y-%%m-%%d"),"-")',
                'purchase_time': 'IFNULL(DATE_FORMAT(forecast_stats.purchase_time, "%%Y-%%m-%%d"),"-")',
                'delivery_time': 'IFNULL(DATE_FORMAT(forecast_stats.delivery_time, "%%Y-%%m-%%d"),"-")',
                'arrival_time': 'IFNULL(DATE_FORMAT(forecast_stats.arrival_time, "%%Y-%%m-%%d"),"-")',
                'is_lack': 'forecast_stats.has_lack',
                'is_defact': 'forecast_stats.has_defact',
                'is_overhead': 'forecast_stats.has_overhead',
                'is_wrong': 'forecast_stats.has_wrong',
                'is_unrecord': 'forecast_stats.is_unrecordlogistic',
                'is_timeouted': 'forecast_stats.is_timeout',
                'is_close': 'forecast_stats.is_lackclose',
            }
        ).select_related('forecast_inbound').values(
            'id', 'forecast_inbound_id', 'supplier__supplier_name', 'buyer_name', 'purchaser', 'purchase_num',
            'inferior_num', 'lack_num', 'purchase_amount', 'arrival_period', 'delivery_period', 'logistic_period',
            'forecast_arrive_time', 'purchase_time', 'delivery_time', 'arrival_time',
            'is_lack', 'is_defact', 'is_overhead', 'is_wrong', 'is_unrecord', 'is_timeouted', 'is_close','status'
        )

        order_values_list = queryset.values_list('id', 'forecast_inbound__relate_order_set')
        order_values_dict = defaultdict(list)
        for id, order_id in order_values_list:
            order_values_dict[id].append(order_id)

        stats_values_list = []
        for stats in stats_values:
            stats['supplier_name'] = stats.pop('supplier__supplier_name')
            stats['relate_orders'] = ','.join([str(s) for s in order_values_dict.get(stats['id'])])
            stats_values_list.append(stats)

        if format == 'json':
            return Response({'results': stats_values_list,
                             'start_time':start_time,
                             'end_time':end_time,
                             'action': action})
        else:
            stats_values = list(stats_values)
            return Response({'results': stats_values_list,
                             'start_time':start_time,
                             'end_time':end_time,
                             'action': action})

