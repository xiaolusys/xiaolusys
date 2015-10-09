# -*- encoding:utf8 -*-
import json
import time
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer

from shopback.base import log_action, ADDITION, CHANGE
from .models import SaleSupplier, SaleCategory, SaleProduct
from rest_framework.views import APIView

from .serializers import (
    SaleSupplierSerializer,
    SaleCategorySerializer,
    SaleProductSerializer,
    SaleProductSampleSerializer,
)


class SaleSupplierList(generics.ListCreateAPIView):
    queryset = SaleSupplier.objects.all()
    serializer_class = SaleSupplierSerializer
    template_name = "supplier_list.html"
    permission_classes = (permissions.IsAuthenticated,)


class SaleSupplierDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleSupplier.objects.all()
    serializer_class = SaleSupplierSerializer
    renderer_classes = (JSONRenderer,)
    # template_name = "supplier.html"
    permission_classes = (permissions.IsAuthenticated,)


def chargeSupplier(request, pk):
    result = {}
    charged = False
    employee = request.user
    try:
        supplier = SaleSupplier.objects.get(id=pk)
    except SaleSupplier.DoesNotExist:
        result = {'code': 1, 'error_response': u'供应商未找到'}
    else:
        charged = SaleSupplier.objects.charge(supplier, employee)
        if not charged:
            result = {'code': 1, 'error_response': ''}

    if charged:
        if supplier.platform == "manualinput":
            result = {'success': True,
                      'brand_links': '/supplychain/supplier/line_product/?status=wait&sale_supplier=%s' % pk}
        else:
            result = {'success': True,
                      'brand_links': '/supplychain/supplier/product/?status=wait&sale_supplier=%s' % pk}

        log_action(request.user.id, supplier, CHANGE, u'接管品牌')

    return HttpResponse(json.dumps(result), content_type='application/json')


class SaleCategoryList(generics.ListCreateAPIView):
    queryset = SaleCategory.objects.all()
    serializer_class = SaleCategorySerializer


class SaleCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleCategory.objects.all()
    serializer_class = SaleCategorySerializer
    permission_classes = (permissions.IsAuthenticated,)


class SaleProductList(generics.ListCreateAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSerializer
    filter_fields = ("status", "sale_supplier")
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "product_screen.html"
    permission_classes = (permissions.IsAuthenticated,)

    paginate_by = 100
    page_query_param = 'page_size'
    max_paginate_by = 100

    def get(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        resp_data = serializer.data

        supplier_id = request.GET.get('sale_supplier', '')
        supplier = None
        if supplier_id:
            supplier = get_object_or_404(SaleSupplier, pk=supplier_id)
            progress = request.GET.get('progress', '')
            if (progress and progress != supplier.progress and
                        progress in dict(SaleSupplier.PROGRESS_CHOICES).keys()):
                supplier.progress = progress
                supplier.save()
            supplier = SaleSupplierSerializer(supplier, context={'request': request}).data
        result_data = {'request_data': request.GET.dict(), 'supplier': supplier, "results": resp_data}
        return Response(result_data)


class SaleProductAdd(generics.ListCreateAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSerializer
    filter_fields = ("status", "sale_supplier")
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "product_add.html"
    permission_classes = (permissions.IsAuthenticated,)
    paginate_by = 100
    page_query_param = 'page_size'
    max_paginate_by = 100

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        resp_data = serializer.data
        sale_category = SaleCategory.objects.all()
        sale_category = SaleCategorySerializer(sale_category, many=True).data
        supplier_id = request.GET.get('sale_supplier', '')
        supplier = None
        if supplier_id:
            supplier = get_object_or_404(SaleSupplier, pk=supplier_id)
            progress = request.GET.get('progress', '')
            if (progress and progress != supplier.progress and
                        progress in dict(SaleSupplier.PROGRESS_CHOICES).keys()):
                supplier.progress = progress
                supplier.save()
            supplier = SaleSupplierSerializer(supplier, context={'request': request}).data
        result_data = {'request_data': request.GET.dict(), 'supplier': supplier, 'sale_category': sale_category,
                       "results": resp_data}
        return Response(result_data)

    def post(self, request, *args, **kwargs):
        data = request.data
        supplier_id = data["supplier"]
        supplier = get_object_or_404(SaleSupplier, pk=supplier_id)
        sproduct, state = SaleProduct.objects.get_or_create(
            outer_id='OO%d' % time.time(),
            platform=supplier.platform)

        for k, v in data.iteritems():
            if len(v) > 0 and len(k) > 0:
                if k == 'sale_category':
                    v = SaleCategory.objects.get(id=v)
                if k == 'title':
                    v = v + "-" + supplier.supplier_name
                hasattr(sproduct, k) and setattr(sproduct, k, v)

        sproduct.sale_supplier = supplier
        sproduct.status = SaleProduct.SELECTED
        sproduct.platform = SaleProduct.MANUALINPUT
        sproduct.contactor = request.user

        sproduct.save()

        log_action(request.user.id, sproduct, ADDITION, u'创建品牌商品')
        return HttpResponseRedirect("/supplychain/supplier/line_product/?sale_supplier=" + supplier_id)


class SaleProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSampleSerializer
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        print request.data
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if not instance.contactor:
            instance.contactor = self.request.user
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        print serializer
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        index_map = {SaleProduct.SELECTED: 1,
                     SaleProduct.PURCHASE: 2,
                     SaleProduct.PASSED: 3,
                     SaleProduct.SCHEDULE: 4}
        log_action(request.user.id, instance, CHANGE,
                   (u'淘汰',
                    u'初选入围',
                    u'洽谈通过',
                    u'审核通过',
                    u'排期'
                    )[index_map.get(instance.status, 0)])
        return Response(serializer.data)

from supplychain.basic.fetch_urls import getBeaSoupByCrawUrl


class FetchAndCreateProduct(APIView):
    # authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer,)
    template_name = "product_detail.html"

    def getItemPrice(self, soup):
        return 0

    def get_img_src(self, link):
        for img in link.findAll('img'):
            attr_map = dict(img.attrs)
            img_src = attr_map and attr_map.get('src') or attr_map.get('data-src')
            if img_src and img_src.split('?')[0].endswith('.jpg'):
                return img_src
        return ''

    def getItemPic(self, soup):

        container = soup.findAll(attrs={'class': 'container'})
        for c in container:
            for a in c.findAll('a'):
                img_src = self.get_img_src(a)
                if img_src:
                    return img_src

        alinks = soup.findAll('a')
        for a in alinks:
            img_src = self.get_img_src(a)
            if img_src:
                return img_src
        return ''

    def getItemTitle(self, soup):
        try:
            return soup.findAll('title')[0].text.strip()
        except:
            return ''

    def get(self, request, pk):

        fetch_url = request.REQUEST.get('fetch_url', '')
        status = request.REQUEST.get('status', '')
        if not fetch_url or not fetch_url.startswith(('http://', 'https://')):
            raise Exception(u'请输入合法的URL')

        supplier = get_object_or_404(SaleSupplier, pk=pk)
        tsoup, response = getBeaSoupByCrawUrl(fetch_url)
        categorys = SaleCategory.objects.all()
        sale_category = SaleCategorySerializer(categorys, many=True).data
        data = {
            'title': self.getItemTitle(tsoup),
            'pic_url': self.getItemPic(tsoup),
            'price': self.getItemPrice(tsoup),
            'fetch_url': fetch_url,
            'status': status,
            'categorys': sale_category,
            'supplier': SaleSupplierSerializer(supplier, context={'request': request}).data
        }
        return Response(data)

    def post(self, request, pk, format=None):

        content = request.REQUEST
        category_name = content.get('category_name', '')

        supplier = get_object_or_404(SaleSupplier, pk=pk)
        sproduct, state = SaleProduct.objects.get_or_create(
            outer_id='OO%d' % time.time(),
            platform=supplier.platform)

        for k, v in content.iteritems():
            if k == 'sale_category':
                v = SaleCategory.objects.get(id=v)
            hasattr(sproduct, k) and setattr(sproduct, k, v)

        sproduct.sale_supplier = supplier
        sproduct.status = sproduct.status or SaleProduct.SELECTED
        sproduct.platform = SaleProduct.MANUAL
        sproduct.contactor = request.user
        sproduct.save()

        data = {'record': SaleProductSerializer(sproduct, context={'request': request}).data}

        log_action(request.user.id, sproduct, ADDITION, u'创建品牌商品')

        return Response(data)


from qiniu import Auth

access_key = "M7M4hlQTLlz_wa5-rGKaQ2sh8zzTrdY8JNKNtvKN"
secret_key = "8MkzPO_X7KhYQjINrnxsJ2eq5bsxKU1XmE8oMi4x"
bucket_name = "xiaolumm"


class QiniuApi(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request):
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name, expires=3600)
        return Response({'uptoken': token})
    

import datetime


def change_Sale_Time(request):
    # sale_time 上架日期
    content = request.POST
    slae_product = content.get('slae_product')
    sale_time = content.get('sale_time')
    if sale_time:
        year, month, day = sale_time.split('-')
        date = datetime.date(int(year), int(month), int(day))
    else:
        return HttpResponse('false')
    pro = SaleProduct.objects.filter(id=slae_product)
    if pro.exists():
        p = pro[0]
        p.sale_time = date
        p.status = SaleProduct.SCHEDULE
        p.save()
        log_action(request.user.id, p, CHANGE, u'修改商品的上架日期和状态')
        return HttpResponse('OK')
    else:
        return HttpResponse('false')
