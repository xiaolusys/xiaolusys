# coding: utf8
from __future__ import absolute_import, unicode_literals


from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication

from core.utils import flatten
from shopback.items.models import Product, ProductSku

from ..models import (
    StagingInBound,
    ForecastInbound,
    ForecastInboundDetail,
)
from .. import serializers
from .. import services

import logging
logger = logging.getLogger(__name__)


CACHE_VIEW_TIMEOUT = 30

class OutwareManageViewSet(viewsets.ViewSet):
    """
        外仓入仓管理viewset
    """
    queryset = ForecastInbound.objects.all()
    # serializer_class = serializers.ForecastInboundSerializer
    authentication_classes = (authentication.BasicAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer,)

    def get_forecast_data(self, forecast_inbound):
        supplier = forecast_inbound.supplier
        warehouse = forecast_inbound.get_warehouse_object()

        params = {
            'store_code': warehouse.store_code,
            'order_code': forecast_inbound.forecast_no,
            'vendor_code': supplier.vendor_code,
            'vendor_name': supplier.supplier_name,
            'tms_order_code': forecast_inbound.express_no,
            'receiver_info': {
                'warehouse_name': warehouse.ware_name,
                'receiver_province': warehouse.province,
                'receiver_city': warehouse.city,
                'receiver_area': warehouse.district,
                'receiver_address': warehouse.address,
                'receiver_name': warehouse.manager,
                'receiver_mobile': warehouse.mobile,
                'receiver_phone': warehouse.phone,
                'object': 'WareAddress',
            },
            'order_items': [],
            'object': 'OutwareInboundOrder',
        }

        normal_details = forecast_inbound.normal_details
        normal_sku_ids = list(normal_details.values_list('sku_id', flat=True))
        po_order = forecast_inbound.relate_order_set.first()
        productsku = dict(ProductSku.objects.in_bulk(normal_sku_ids))
        for detail in normal_details:
            sku = productsku[detail.sku_id]
            saleproduct = sku.product.sale_product
            params['order_items'].append({
                'sku_id': productsku[detail.sku_id].outer_id,
                'sku_name': detail.product_name,
                'sku_img': productsku[detail.sku_id].outer_id,
                'quantity': detail.forecast_arrive_num,
                'batch_code': po_order.batch_no,
                'is_batch_mgt': saleproduct.is_batch_mgt_on,
                'is_expire_mgt': saleproduct.is_expire_mgt_on,
                'is_vendor_mgt': saleproduct.is_vendor_mgt_on,
                'shelf_life': saleproduct.shelf_life_days,
                'object': 'OutwareInboundSku',
            })

        return params

    def get_wareinbound_data(self, ware_inbound):
        return {}

    def list(self, request, *args, **kwargs):
        forecast_id = request.GET.get('forecast_id')
        forecast_inbound = self.queryset.get(id=forecast_id)


        return Response(params, template_name='forecast/push_outware.html')