# -*- coding:utf-8 -*-
import os
import json
import datetime
import hashlib
import urlparse
import random

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

from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer

from common.utils import get_admin_name
from core.options import log_action, ADDITION, CHANGE
from shopback.items.models import Product, ProductSku, ProductLocation
from supplychain.supplier.models import SaleProduct
from flashsale.dinghuo.models import OrderList, OrderDetail


from .models import StagingInBound,ForecastInbound,ForecastInboundDetail,RealInBound,RealInBoundDetail
from . import serializers
from . import constants

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
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
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
        from .models import uniq_staging_inbound_record

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
                    uniq_key=uniq_staging_inbound_record(supplier_id, product.ware_by, creator, sku_id),
                    creator=creator
                )
                staging_inbound.save()
        return Response('OK')


class InBoundViewSet(viewsets.ModelViewSet):
    queryset = RealInBound.objects.all()
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer,)

    def retrieve(self, request, pk=None):
        inbound = RealInBound.objects.get(id=pk)

        skus_dict = {}
        for inbounddetail in inbound.inbound_detail_manager.filter(status=RealInBoundDetail.NORMAL).order_by('id'):
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
            'status': dict(RealInBound.STATUS_CHOICES).get(inbound.status) or '待入库',
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
        real_inbound = RealInBound(
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
            real_inbound_detail = RealInBoundDetail(
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
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer,)

    template_name = 'forecast/forecast_manage.html'

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
                forecast_skus = forecast.normal_details().filter(product_id=pid)
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
                         'supplier': forecast_details and forecast_details[0]['supplier'] or {}})

    # def parse_forecast_data(self, data):


    @list_route(methods=['post'])
    def create_or_split_forecast(self, request, *args, **kwargs):

        content = request.POST
        datas = json.loads(content.get('forecast_data','{}'))
        forecast_ids  = set()
        forecast_data_list = []
        logger.debug('data:%s'% datas);
        for kstr, num in datas.iteritems():
            sku_id, product_id, forecast_id, k1,k2 = kstr.split('-')
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
            forecast_arrive_time = content.get('forecast_arrive_time',None)
            forecast_newobj = ForecastInbound(supplier=forecast_obj.supplier)
            forecast_objdict = model_to_dict(forecast_obj)
            for name ,value in forecast_objdict.iteritems():
                if name in ('id','supplier','relate_order_set'):continue
                setattr(forecast_newobj,name,value)
            forecast_newobj.forecast_arrive_time = forecast_arrive_time
            forecast_newobj.save()

            for inbound in origin_inbounds:
                forecast_newobj.relate_order_set.add(inbound)

            for obj in forecast_data_list:
                detail = ForecastInboundDetail.objects.filter(forecast_inbound_id=obj[2],
                                                            product_id=obj[1], sku_id=obj[0]).first()
                if not detail or detail.forecast_arrive_num < obj[3]:
                    raise exceptions.APIException('trans num bigger than forecast arrive num:%s'%(obj))
                if detail.forecast_arrive_num <= obj[3]:
                    detail.status = ForecastInboundDetail.DELETE
                detail.forecast_arrive_num = models.F('forecast_arrive_num') - obj[3]
                detail.save(update_fields=['forecast_arrive_num','status'])

                forecast_detail = ForecastInboundDetail()
                forecast_detail.forecast_inbound = forecast_newobj
                forecast_detail.product_id = obj[1]
                forecast_detail.sku_id = obj[0]
                forecast_detail.forecast_arrive_num = obj[3]
                forecast_detail.product_name = detail.product_name
                forecast_detail.product_img = detail.product_img
                forecast_detail.save()

        for forecast in forecast_qs:
            if forecast.total_detail_num == 0:
                forecast.unarrive_close()

        # serializer_data = self.get_serializer(forecast_newobj).data
        return Response({'redrect_url': reverse('admin:forecast_forecastinbound_changelist')+'?q=%s'%forecast_newobj.id})


from . import services

class PurchaseDashBoardAPIView(APIView):
    """
        订货单管理dashboard页面
    """
    authentication_classes = (authentication.TokenAuthentication,authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer)
    template_name = 'forecast/dashboard.html'

    def get(self, request, *args, **kwargs):
        """
        action: (all, 全部), (unarrived, 未准时到货), (unbilling, 到货等待结算), (unlogisticed, 未填写物流信息),
        """
        data = request.GET
        action = data.get('action', 'all')
        staff_name = data.get('staff_name','')

        purchase_orders = services.filter_pending_purchaseorder(**{'staff_name': staff_name})
        aggregate_forecast_obj = services.AggregateForcecastOrderAndInbound(purchase_orders)

        aggregate_list_dict = {
            'unlogisticed': [],
            'unarrived': [],
            'billingable': [],
        }
        aggregate_datas = aggregate_forecast_obj.aggregate_data()
        for aggregate  in aggregate_datas:
            if aggregate['is_unrecord_logistic']:
                aggregate_list_dict['unlogisticed'].append(aggregate)
            if aggregate['is_unarrive_intime']:
                aggregate_list_dict['unarrived'].append(aggregate)
            if aggregate['is_billingable']:
                aggregate_list_dict['billingable'].append(aggregate)

        is_handleable = action in ('unlogisticed', 'unarrived', 'billingable')
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
                         'billingable_num': len(aggregate_list_dict['billingable']),
                         'aggregate_num': is_handleable and len(aggregate_datas) or len(aggregate_record_list),
                         'action': action,
                         'staff_name':staff_name})

