# coding: utf-8
import datetime
import json
import re
import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from rest_framework import authentication, exceptions, generics, permissions
from rest_framework.compat import OrderedDict
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from shopback.base import log_action, ADDITION, CHANGE
from shopback.categorys.models import ProductCategory

from . import constants
from .models import SaleSupplier, SaleCategory, SaleProduct
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
    ordering = ('-modified', )
    paginate_by = 15
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    def get(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.queryset.order_by(*self.ordering))
        page = self.paginate_queryset(queryset)
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

        resp_data = self.get_serializer(page, many=True).data
        result_data = {'request_data': request.GET.dict(), 'supplier': supplier
                       , 'sale_category': sale_category, "results": resp_data}
        if hasattr(self,'get_paginated_response'):
            result_data.update(OrderedDict([
                            ('count', self.paginator.page.paginator.count),
                            ('next', self.paginator.get_next_link()),
                            ('previous', self.paginator.get_previous_link()),
                        ]))

        return Response(result_data)

    def post(self, request, *args, **kwargs):
        data = request.data
        supplier_id = data["supplier"]
        supplier = get_object_or_404(SaleSupplier, pk=supplier_id)
        if not supplier.is_active():
            return Response({'code':1,'error_response':'供应商已被淘汰，不能添加商品','request_data': request.GET.dict()})
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
        sproduct.status = sproduct.status or SaleProduct.SELECTED
        sproduct.platform = SaleProduct.MANUALINPUT
        sproduct.contactor = request.user
        sproduct.save()

        log_action(request.user.id, sproduct, ADDITION, u'创建品牌商品')
        return HttpResponseRedirect("/supplychain/supplier/product/?status=%s&sale_supplier=%s"%(sproduct.status,supplier_id))


class SaleProductAdd(generics.ListCreateAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSerializer
    filter_fields = ("status", "sale_supplier")
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "product_add.html"
    permission_classes = (permissions.IsAuthenticated,)
    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
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
        if not supplier.is_active():
            return Response({'code':1,'error_response':'供应商已被淘汰，不能添加商品','request_data': request.GET.dict()})
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
        sproduct.status = sproduct.status or SaleProduct.SELECTED
        sproduct.platform = SaleProduct.MANUALINPUT
        sproduct.contactor = request.user
        sproduct.save()

        log_action(request.user.id, sproduct, ADDITION, u'创建品牌商品')
        return HttpResponseRedirect("/supplychain/supplier/line_product/?status=%s&sale_supplier=%s"%(sproduct.status,supplier_id))


class SaleProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = SaleProductSampleSerializer
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if not instance.contactor:
            instance.contactor = self.request.user

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        index_map = {SaleProduct.SELECTED: 1,
                     SaleProduct.PURCHASE: 2,
                     SaleProduct.PASSED: 3,
                     SaleProduct.SCHEDULE: 4}

        update_field_labels = []
        for k,v in request.data.iteritems():
            if not hasattr(instance,k):continue
            update_field_labels.append('%s:%s'%(SaleProduct._meta.get_field(k).verbose_name.title(),v))

        status_label = (u'淘汰',
                        u'初选入围',
                        u'洽谈通过',
                        u'审核通过',
                        u'排期'
                        )[index_map.get(instance.status, 0)]
        log_action(request.user.id, instance, CHANGE,'%s(%s)'%(status_label,','.join(update_field_labels)))
        return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        sale_time = ''
        if instance.sale_time:
            sale_time = instance.sale_time.strftime('%Y-%m-%d')
        return Response({
            'pic_url': instance.pic_url,
            'sale_time': sale_time,
            'product_category': self.get_category_mapping().get(instance.sale_category_id) or {}
        })

    @classmethod
    def get_category_mapping(cls):
        cache_key = 'category_mapping'
        def _load():
            parent_product_categories = {}
            for product_category in ProductCategory.objects.filter(parent_cid=constants.XIAOLU_ROOT_CATEGORY_ID,
                                                                   is_parent=True, status='normal'):
                parent_product_categories[product_category.cid] = product_category

            product_categories = {}
            for product_category in ProductCategory.objects.filter(is_parent=False, status='normal'):
                parent_category = parent_product_categories.get(product_category.parent_cid)
                if not parent_category:
                    continue
                full_name = '%s/%s' % (parent_category.name, product_category.name)
                product_categories[full_name] = {
                    'level_3_id': product_category.cid,
                    'level_2_id': parent_category.cid,
                    'level_1_id': constants.XIAOLU_ROOT_CATEGORY_ID
                }
            for parent_id, parent_product_category in parent_product_categories.iteritems():
                product_categories[parent_product_category.name] = {
                    'level_3_id': 0,
                    'level_2_id': parent_product_category.cid,
                    'level_1_id': constants.XIAOLU_ROOT_CATEGORY_ID
                }

            parent_sale_categories = {}
            for sale_category in SaleCategory.objects.filter(parent_cid=0, is_parent=True, status='normal'):
                parent_sale_categories[sale_category.id] = sale_category

            sale_categories = {}
            for sale_category in SaleCategory.objects.filter(status='normal'):
                parent_category = parent_sale_categories.get(sale_category.parent_cid)
                if not parent_category:
                    full_name = sale_category.name
                else:
                    full_name = '%s/%s' % (parent_category.name, sale_category.name)
                sale_categories[sale_category.id] = product_categories.get(full_name) or {}
            return sale_categories
        data = cache.get(cache_key)
        if not data:
            data = _load()
            cache.set(cache_key, data, 3600)
        return data

from supplychain.basic.fetch_urls import getBeaSoupByCrawUrl


class FetchAndCreateProduct(APIView):
    # authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer,)
    template_name = "product_detail.html"

    def getItemPrice(self, soup):
        return 0

    def get_img_src(self,img):
        attr_map = dict(img.attrs)
        img_src = attr_map and attr_map.get('src') or attr_map.get('data-src')
        if img_src and img_src.split('?')[0].endswith('.jpg'):
            return img_src
        return ''

    def get_link_img_src(self, link):
        for img in link.findAll('img'):
            return self.get_img_src(img)
        return ''

    def getItemPic(self, soup):

        container = soup.findAll(attrs={'class':re.compile('^(container|florid-goods-page-container|m-item-grid)')})
        for c in container:
            for img in c.findAll('img'):
                img_src = self.get_img_src(img)
                print img,img_src
                if img_src:
                    return img_src

        alinks = soup.findAll('a')
        for a in alinks:
            img_src = self.get_link_img_src(a)
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
        if not supplier.is_active():
            return Response({'code':1,'error_response':'供应商已被淘汰，不能添加商品'})
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

        # sale_time如果是unicode需要转换成datetime
        if isinstance(sproduct.sale_time, basestring):
            sproduct.sale_time = datetime.datetime.strptime(sproduct.sale_time, '%Y-%m-%d %H:%M:%S')

        data = {'record': SaleProductSerializer(sproduct, context={'request': request}).data}
        log_action(request.user.id, sproduct, ADDITION, u'创建品牌商品')

        return Response(data)

from qiniu import Auth

class QiniuApi(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request):
        q = Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)
        token = q.upload_token("xiaolumm", expires=3600)
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


from django.shortcuts import get_object_or_404
from common.utils import update_model_fields


class SaleProductChange(APIView):
    queryset = SaleProduct.objects.all()
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        instance = get_object_or_404(SaleProduct, id=args[0]) if len(args) == 1 else 0
        if not instance.contactor:
            instance.contactor = self.request.user
        index_map = {SaleProduct.SELECTED: 1,
                     SaleProduct.PURCHASE: 2,
                     SaleProduct.PASSED: 3,
                     SaleProduct.SCHEDULE: 4}
        update_field_labels = []
        for k, v in request.data.iteritems():
            k = str(k)
            if not hasattr(instance, k): continue
            update_field_labels.append('%s:%s' % (SaleProduct._meta.get_field(k).verbose_name.title(), v))
            instance.__setattr__(k, v)
            update_model_fields(instance, update_fields=[k])
        status_label = (u'淘汰', u'初选入围', u'洽谈通过', u'审核通过', u'排期')[index_map.get(instance.status, 0)]
        log_action(request.user.id, instance, CHANGE, '%s(%s)' % (status_label, ','.join(update_field_labels)))
        return Response({"ok"})

class CategoryMappingView(APIView):
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        parent_product_categories = {}
        for product_category in ProductCategory.objects.filter(parent_cid=constants.XIAOLU_ROOT_CATEGORY_ID,
                                                               is_parent=True, status='normal'):
            parent_product_categories[product_category.cid] = product_category

        product_categories = {}
        for product_category in ProductCategory.objects.filter(is_parent=False, status='normal'):
            parent_category = parent_product_categories.get(product_category.parent_cid)
            if not parent_category:
                continue
            full_name = '%s/%s' % (parent_category.name, product_category.name)
            product_categories[full_name] = {
                'level_3_id': product_category.cid,
                'level_2_id': parent_category.cid,
                'level_1_id': constants.XIAOLU_ROOT_CATEGORY_ID
            }

        parent_sale_categories = {}
        for sale_category in SaleCategory.objects.filter(parent_cid=0, is_parent=True, status='normal'):
            parent_sale_categories[sale_category.id] = sale_category

        sale_categories = {}
        for sale_category in SaleCategory.objects.filter(is_parent=False, status='normal'):
            parent_category = parent_sale_categories.get(sale_category.parent_cid)
            if not parent_category:
                continue
            sale_categories[sale_category.id] = product_categories.get('%s/%s' % (parent_category.name, sale_category.name)) or {}
        return Response(sale_categories)
