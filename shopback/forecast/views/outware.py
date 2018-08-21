# coding: utf8
from __future__ import absolute_import, unicode_literals

from collections import defaultdict

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication

from core.utils import flatten
from shopback.items.models import Product, ProductSku
from pms.supplier.models import SaleProduct

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

        from shopback.outware.models import OutwareSku
        supplier = forecast_inbound.supplier
        warehouse = forecast_inbound.get_warehouse_object()

        params = {
            'is_received': False,
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
            saleproduct = SaleProduct.objects.filter(id=sku.product.sale_product).first()
            ow_sku = OutwareSku.objects.filter(outware_supplier__vendor_code=supplier.vendor_code,
                                               sku_code=sku.outer_id).first()
            params['order_items'].append({
                'sku_id': sku.outer_id,
                'sku_name': detail.product_name,
                'bar_code': sku.supplier_skucode,
                'sku_img': sku.product.pic_path,
                'quantity': detail.forecast_arrive_num,
                'batch_code': po_order.batch_no,
                'is_batch_mgt': saleproduct.is_batch_mgt_on,
                'is_expire_mgt': saleproduct.is_expire_mgt_on,
                'is_vendor_mgt': saleproduct.is_vendor_mgt_on,
                'shelf_life': saleproduct.shelf_life_days,
                'is_pushed_ok': ow_sku and ow_sku.is_pushed_ok or False,
                'is_unioned': ow_sku and ow_sku.is_unioned or False,
                'object': 'OutwareInboundSku',
            })

        return params

    def get_wareinbound_data(self, forecast_no):
        from shopback.outware.adapter.mall.pull.search import get_outware_inbound_by_code
        return get_outware_inbound_by_code(forecast_no)

    def list(self, request, *args, **kwargs):
        forecast_id = request.GET.get('forecast_id')
        forecast_inbound = self.queryset.get(id=forecast_id)
        ow_inbound_data = self.get_wareinbound_data(forecast_inbound.forecast_no)
        if not ow_inbound_data:
            ow_inbound_data = self.get_forecast_data(forecast_inbound)

        return Response(ow_inbound_data, template_name='forecast/push_outware.html')

    @detail_route(methods=['post'])
    def confirm_push(self, request, pk=None, *args, **kwargs):
        from shopback.outware.adapter.mall.push import supplier, inbound, product
        from shopback.outware.models import OutwareSku, OutwareSupplier, OutwareInboundOrder
        forecast_inbound = ForecastInbound.objects.get(forecast_no=pk)
        # 检查入仓单状态
        forecast_no = forecast_inbound.forecast_no
        ow_inbound = OutwareInboundOrder.objects.filter(inbound_code=forecast_no,
                                                        order_type=OutwareInboundOrder.ORDER_PURCHASE).first()
        if ow_inbound and ow_inbound.is_pushed_ok:
            return Response({'code': 1, 'info': '入仓单已推送成功，如需修改请先取消'})
        try:
            #　first,检查供应商是否创建成功
            mall_supplier = forecast_inbound.supplier
            ow_supplier = OutwareSupplier.objects.filter(vendor_code=mall_supplier.vendor_code).first()
            if not ow_supplier or not ow_supplier.is_pushed_ok:
                resp = supplier.push_ware_supplier_by_mall_supplier(mall_supplier)
                if not resp.get('success'):
                    return Response({'code': 2, 'info': 'step1错误: %s'%resp.get('message')})

            normal_details = forecast_inbound.normal_details
            sku_salep_list = ProductSku.objects.filter(id__in=list(normal_details.values_list('sku_id', flat=True)))\
                .values_list('id', 'product__sale_product', 'outer_id')
            sku_saledict = defaultdict(list)
            sku_codes = set()
            for sku_tuple in sku_salep_list:
                sku_saledict[sku_tuple[1]].append(sku_tuple[0])
                sku_codes.add(sku_tuple[2])

            sale_products = SaleProduct.objects.filter(id__in=sku_saledict.keys())
            #  second, 检查商品是否创建成功
            # 　third, 检查商品与供应商是否关联
            for sale_product in sale_products:
                success_skucode_list = product.push_ware_sku_by_saleproduct(sale_product, sku_codes=list(sku_codes))
                good_skucodes = ProductSku.objects.filter(id__in=sku_saledict.get(sale_product.id))\
                    .values_list('outer_id', flat=True)
                delta_skucodes = set(good_skucodes) - set(success_skucode_list)
                if len(delta_skucodes) > 0:
                    return Response({'code':3, 'info': 'step2规格未更新成功: %s'% ','.join(delta_skucodes)})

            # fourth, 创建入仓单
            resp = inbound.push_outware_inbound_by_forecast_order(forecast_inbound)
            if not resp.get('success'):
                return Response({'code': 3, 'info': 'step3错误: %s'%resp.get('message')})
        except Exception, exc:
            logger.error(str(exc), exc_info=True)
            return Response({'code': 4, 'info': '未知错误: %s'%str(exc)})

        forecast_inbound.push_fengchao_update_status_approved()
        forecast_inbound.save(update_fields=['status'])

        return Response({'code': 0, 'info': '推送成功'})

    @detail_route(methods=['post'])
    def cancel_pushed(self, request, pk=None, *args, **kwargs):
        from shopback.outware.adapter.mall.push import supplier, inbound, product
        try:
            forecast_inbound = ForecastInbound.objects.get(forecast_no=pk)
            resp = inbound.cancel_outware_inbound_by_forecast(forecast_inbound)
            if not resp.get('success'):
                return Response({'code': 1, 'info': '%s' % resp.get('message')})

            forecast_inbound.cancel_fengchao_update_status_draft()
            forecast_inbound.save(update_fields=['status'])

        except Exception, exc:
            logger.error(str(exc), exc_info=True)
            return Response({'code': 4, 'info': '未知错误: %s'%str(exc)})

        return Response({'code': 0, 'info': '推送成功'})

    @list_route(methods=['post'])
    def push_product_sku(self, request, *args, **kwargs):
        """
        :param sku_codes: 123,456:
        """
        # TODO@meron 未完成
        from shopback.outware.adapter.mall.push import supplier, inbound, product
        data = request.POST.dict()
        sku_code_set = set(data.get('sku_codes').split(','))
        product_skus = ProductSku.objects.filter(outer_id__in=sku_code_set )
        sale_product_ids = list(product_skus.values('product__sale_product',flat=True))
        sale_products = SaleProduct.objects.filter(id__in=sale_product_ids)
        success_skucode_set = set()
        for sale_product in sale_products.iterator():
            success_skucode_list = product.push_ware_sku_by_saleproduct(sale_product, sku_codes=list(sku_code_set))
            success_skucode_set.update(success_skucode_list)

        if sku_code_set - success_skucode_set:
            return Response({'code': 1, 'info': '未更新成功: %s'% ','.join(sku_code_set - success_skucode_set)})

        return Response({'code': 0, 'info': '更新成功'})

