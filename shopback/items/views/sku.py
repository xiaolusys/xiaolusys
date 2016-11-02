# coding: utf-8
__author__ = 'yan.huang'
from shopback.items.models import Product, ProductSku
from rest_framework.response import Response
from rest_framework import viewsets, permissions, authentication
from django.db.models import Q
from ..serializer import ProductSkuSerializers
import logging
from shopback import paramconfig as pcfg

logger = logging.getLogger(__name__)


class ProductSkuViewSet(viewsets.ModelViewSet):
    queryset = ProductSku.objects.all()
    serializer_class = ProductSkuSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def list(self, request):
        q = request.GET.get('q')
        if not q:
            raise Exception(u'必须提供查询参数')
        skus = ProductSku.objects.filter(Q(id=q) | Q(outer_id=q) | Q(product__id=q) | Q(product__outer_id=q) |
                                         Q(product__name__contains=q), status__in=(pcfg.NORMAL, pcfg.REMAIN))
        if skus.first():
            cache_sku_dict = {sku.id: sku for sku in skus.order_by('-created')}
            sku_product_ids = [(i['id'], i['product_id']) for i in skus.values('id', 'product_id')]
            cache_product_dict = {}
            for sku_id, prod_id in sku_product_ids:
                if prod_id not in cache_product_dict:
                    cache_product_dict[prod_id] = []
                cache_product_dict[prod_id].append(cache_sku_dict.get(sku_id))
            products = Product.objects.filter(id__in=[prod_id for _sku_id, prod_id in sku_product_ids])
            prod_list = [(prod.outer_id,
                          prod.pic_path,
                          prod.name,
                          prod.cost,
                          prod.collect_num,
                          prod.created,
                          [(sku.outer_id, sku.name, sku.quantity)
                           for sku in cache_product_dict.get(prod.id)])
                         for prod in products]
            return Response(prod_list)
        return Response([])

    def list_by_q(self):
        return
