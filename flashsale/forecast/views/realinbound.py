# coding: utf8
from __future__ import absolute_import, unicode_literals

# -*- coding:utf-8 -*-
import os
import json

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication


from common.utils import get_admin_name
from shopback.items.models import Product, ProductSku, ProductLocation, SkuStock
from supplychain.supplier.models import SaleProduct

from ..models import (
    StagingInBound,
    ForecastInbound,
    ForecastInboundDetail,
    RealInbound,
    RealInboundDetail,
    ForecastStats
)
from .. import serializers
from shopback.warehouse import constants


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
        data = request.GET
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
        from ..models import gen_uniq_staging_inbound_record_id

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
        content = request.POST
        records = json.loads(content['records'])
        forecast_inbound_id = int(content['forecast_inbound_id'])

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
