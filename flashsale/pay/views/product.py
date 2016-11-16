# coding=utf-8
import json
import datetime
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.forms import model_to_dict
from collections import OrderedDict

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import filters

from shopback.items.models import Product, ProductSku
from flashsale.pay import serializers


class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.order_by('outer_id')
    serializer_class = serializers.ProductSerializer
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)

    template_name = "pay/mindex.html"
    # permission_classes = (permissions.IsAuthenticated,)
    paginate_by = 10

    filter_backends = (filters.DjangoFilterBackend,)

    filter_fields = (
        'category',
    )

    def myfilter_queryset(self, queryset, history, time_line):
        if history == 'none':
            return queryset

        today = datetime.date.today()
        if history:
            filter_date = today - datetime.timedelta(days=time_line)
            return queryset.filter(sale_time__gte=filter_date, sale_time__lt=today)

        return queryset.filter(sale_time=today)

    def list(self, request, *args, **kwargs):
        content = request.GET
        time_line = content.get('time_line', '0')
        history = content.get('history', '')
        category = content.get('category', '')
        if not time_line.isdigit() or int(time_line) < 0:
            time_line = 0

        if category != '11' and history == 'none':
            history = ''

        time_line = int(time_line)

        filter_qs = self.filter_queryset(self.get_queryset())
        filter_qs = filter_qs.filter(status=Product.NORMAL,
                                     shelf_status=Product.UP_SHELF)

        fliter_qs = self.myfilter_queryset(filter_qs, history, time_line)

        page = self.paginate_queryset(fliter_qs)
        if page is not None:
            if hasattr(self, 'get_paginated_response'):
                page_response = self.get_serializer(page, many=True)
                serializer = OrderedDict([
                    ('count', self.paginator.page.paginator.count),
                    ('next', self.paginator.get_next_link()),
                    ('previous', self.paginator.get_previous_link()),
                    ('results', page_response.data)
                ])
            else:
                serializer = self.get_pagination_serializer(page).data
        else:
            serializer = self.get_serializer(fliter_qs, many=True).data

        return Response({'products': serializer, 'category': category,
                         'history': history, 'time_line': time_line})


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = serializers.ProductDetailSerializer
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)

    template_name = "pay/mproduct.html"
    # permission_classes = (permissions.IsAuthenticated,)


def productsku_quantity_view(request):
    # request.POST
    content = request.GET
    product_id = content.get('product_id')
    sku_id = content.get('sku_id')
    num = int(content.get('num', ''))

    sku = get_object_or_404(ProductSku, pk=sku_id, product__id=product_id)

    lock_success = Product.objects.isQuantityLockable(sku, num)

    resp = {'success': lock_success}

    return HttpResponse(json.dumps(resp), content_type='application/json')


class ProductDetailView(APIView):
    renderer_classes = (TemplateHTMLRenderer,)
    template_name = "product/product_detail_img.html"

    # permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk, format=None):
        product = get_object_or_404(Product, id=pk)
        p_dict = model_to_dict(product)
        p_dict['detail'] = product.detail
        p_dict['product_model'] = product.product_model
        p_dict['normal_skus'] = product.normal_skus

        return Response({'product': p_dict, 'M_STATIC_URL': settings.M_STATIC_URL})
