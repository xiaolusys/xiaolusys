# coding:utf-8
"""
    补单进货
"""
import re
import json
from django.db.models import *
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, renderers, viewsets
from flashsale.dinghuo.models import OrderList
from rest_framework.response import Response
from flashsale.dinghuo.models import OrderDraft
from shopback.items.models import Product, ProductSku, SkuStock
from django.template.context import RequestContext
from django.forms import model_to_dict
from django.shortcuts import render_to_response
from rest_framework.decorators import detail_route, list_route


class RePurchaseViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer, renderers.BrowsableAPIRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = OrderList.objects.filter(created_by=OrderList.CREATED_BY_REPURCHASE)

    @detail_route(methods=['get'])
    def begin(self, request, pk=None):
        product_ids = request.GET.get('product_ids', '')
        skus_dict = json.loads(request.GET.get('skus', '{}')) or {}
        sku_ids = skus_dict.keys()
        user = request.user
        orderDrAll = OrderDraft.objects.all().filter(buyer_name=user)
        if sku_ids:
            skus = ProductSku.objects.filter(id__in=sku_ids).select_related('product')
        elif product_ids:
            skus = ProductSku.objects.filter(product_id__in=product_ids).select_related('product')
        else:
            skus = []
        product_dicts = {}
        for sku in skus:
            if sku.product_id in product_dicts:
                product_dict = product_dicts.get(sku.product_id)
            else:
                product_dict = model_to_dict(sku.product)
                product_dict['prod_skus'] = []
                product_dicts[sku.product_id] = product_dict
            sku_dict = model_to_dict(sku)
            sku_dict['name'] = sku.name
            sku_dict['need_order'] = skus_dict.get(str(sku.id), 1)
            sku_dict['wait_post_num'] = SkuStock.get_by_sku(sku.id).wait_post_num
            product_dict['prod_skus'].append(sku_dict)
        productres = product_dicts.values()
        return render_to_response('dinghuo/purchase/purchase.html',
                                  {"productRestult": productres,
                                   "drafts": orderDrAll},
                                  context_instance=RequestContext(request))

    def create(self, request, pk=None):
        result = {}
        return Response(result, template_name='dinghuo/inbound.html')

    def list(self, request, *args, **kwargs):
        return Response({'a':1}, template_name='dinghuo/inbound.html')