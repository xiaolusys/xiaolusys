# coding: utf-8
import datetime
import json
import urllib

from rest_framework import generics, permissions, renderers, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions, authentication
from django.shortcuts import get_object_or_404
from pms.supplier.serializers import ScheduleManageSerializer
from pms.supplier.models import SaleProductManage
from flashsale.pay.models import ModelProduct
from flashsale.pay.serializers import ModelProductScheduleSerializer


class ScheduleManageViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleManageSerializer
    queryset = SaleProductManage.objects.all()
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permissions_classes = (permissions.IsAuthenticated,)

    @list_route(methods=['get'])
    def modelproducts(self, request):
        schedule_id = request.GET.get('schedule_id')
        sale_supplier_id = request.GET.get('sale_supplier')
        name = request.GET.get('product_name')
        condition = { 'product_type': 0, 'status': 'normal'}
        if name:
            condition['name__contains'] = name
        spm = get_object_or_404(SaleProductManage, id=schedule_id)
        if sale_supplier_id:
            queryset = ModelProduct.get_by_suppliers(sale_supplier_id.split(','))
        else:
            sale_supplier_ids = [ss.id for ss in spm.sale_suppliers.all()]
            if sale_supplier_ids:
                queryset = ModelProduct.get_by_suppliers(sale_supplier_ids)
            else:
                # 搜索填写了供应商的所有ModelProduct
                from shopback.items.models import Product
                q = Product.objects.filter(sale_product__gt=0, status='normal', type=0).values_list('model_id', flat=True)
                queryset = ModelProduct.objects.filter(id__in=q)
        queryset = queryset.filter(**condition)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ModelProductScheduleSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = ModelProductScheduleSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)