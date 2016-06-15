# -*- coding:utf-8 -*-
import os
import json
import datetime
import hashlib
import urlparse
import random

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.forms import model_to_dict

from rest_framework import generics
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from rest_framework_extensions.cache.decorators import cache_response

from common.utils import get_admin_name
from core.options import log_action, ADDITION, CHANGE
from shopback.items.models import Product, ProductSku
from supplychain.supplier.models import SaleProduct

from .models import StagingInBound,ForecastInbound,ForecastInboundDetail,RealInBound,RealInBoundDetail
from . import serializers



CACHE_VIEW_TIMEOUT = 30

def gen_uniq_staging_inbound_record_id(username, supplier_id, ware_house, sku_id):
    return '%s-%s-%s-%s'%(username, supplier_id, ware_house, sku_id)

class StagingInboundViewSet(viewsets.ReadOnlyModelViewSet):
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

class ForecastManageViewSet(viewsets.ReadOnlyModelViewSet):
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

    def list(self, request, *args, **kwargs):
        return Response({})
