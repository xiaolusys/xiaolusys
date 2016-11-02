# coding: utf-8
import copy
from cStringIO import StringIO
import datetime
import json
import re
import time
import urllib
import urlparse
import xlsxwriter

from django.conf import settings
from django.core.cache import cache
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import View

from rest_framework import authentication, exceptions, generics, permissions
from rest_framework.compat import OrderedDict
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from flashsale.dinghuo.models import OrderDetail, OrderList
from flashsale.pay.models import ModelProduct, Productdetail, SaleOrder
from core.options import log_action, ADDITION, CHANGE

from shopback import paramconfig as pcfg
from shopback.categorys.models import ProductCategory
from shopback.items.models import Product, ProductSku
from shopback.trades.models import (MergeOrder, TRADE_TYPE, SYS_TRADE_STATUS)

from supplychain.supplier import constants, forms
from supplychain.supplier.models import (
    SaleSupplier,
    SaleCategory,
    SaleProduct,
    SaleProductManage,
    SaleProductManageDetail
)
from supplychain.supplier import serializers


class SaleSupplierList(generics.ListCreateAPIView):
    queryset = SaleSupplier.objects.all()
    serializer_class = serializers.SaleSupplierSerializer
    template_name = "supplier_list.html"
    permission_classes = (permissions.IsAuthenticated,)


class SaleSupplierDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleSupplier.objects.all()
    serializer_class = serializers.SaleSupplierSerializer
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
                  'brand_links':
                  '/supplychain/supplier/product/?status=wait&sale_supplier=%s'
                  % pk}

        log_action(request.user.id, supplier, CHANGE, u'接管品牌')

    return HttpResponse(json.dumps(result), content_type='application/json')


class SaleCategoryList(generics.ListCreateAPIView):
    queryset = SaleCategory.objects.all()
    serializer_class = serializers.SaleCategorySerializer


class SaleCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleCategory.objects.all()
    serializer_class = serializers.SaleCategorySerializer
    permission_classes = (permissions.IsAuthenticated,)


class SaleProductList(generics.ListCreateAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = serializers.SaleProductSerializer
    filter_fields = ("status", "sale_supplier")
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "product_screen.html"
    permission_classes = (permissions.IsAuthenticated,)
    ordering = ('-modified',)
    paginate_by = 15
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    def get(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.queryset.order_by(*self.ordering))
        sale_category = SaleCategory.objects.all().order_by('cid')
        sale_category = serializers.SaleCategorySerializer(sale_category, many=True).data

        supplier_id = request.GET.get('sale_supplier', '')
        supplier = None
        if supplier_id:
            supplier = get_object_or_404(SaleSupplier, pk=supplier_id)
            progress = request.GET.get('progress', '')
            status = request.GET.get('status', '')
            if (progress and progress != supplier.progress and
                    progress in dict(SaleSupplier.PROGRESS_CHOICES).keys()):
                supplier.progress = progress
                supplier.save()
            supplier = serializers.SaleSupplierSerializer(supplier,
                                              context={'request': request}).data
            queryset = queryset.filter(sale_supplier_id=supplier_id)
            if status:
                queryset = queryset.filter(status=status)
        page = self.paginate_queryset(queryset)
        resp_data = self.get_serializer(page, many=True).data
        result_data = {'request_data': request.GET.dict(),
                       'supplier': supplier,
                       'sale_category': sale_category,
                       "results": resp_data}
        if hasattr(self, 'get_paginated_response'):
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

        print 'data:', data
        if not supplier.is_active():
            return Response({'code': 1,
                             'error_response': '供应商已被淘汰，不能添加商品',
                             'request_data': request.GET.dict()})
        sproduct, state = SaleProduct.objects.get_or_create(
            outer_id='OO%d' % time.time(),
            platform=supplier.platform)

        sproduct.orderlist_show_memo = False
        for k, v in data.iteritems():
            if len(v) > 0 and len(k) > 0:
                if k == 'sale_category':
                    v = SaleCategory.objects.get(id=v)
                if k == 'title':
                    v = v + "-" + supplier.supplier_name
                if k == 'orderlist_show_memo':
                    v = v.lower() in ('on', 'true')
                hasattr(sproduct, k) and setattr(sproduct, k, v)
        sproduct.sale_supplier = supplier
        sproduct.status = sproduct.status or SaleProduct.SELECTED
        sproduct.platform = SaleProduct.MANUALINPUT
        sproduct.contactor = request.user
        sproduct.save()

        log_action(request.user.id, sproduct, ADDITION, u'创建品牌商品')
        return HttpResponseRedirect(
            "/supplychain/supplier/product/?status=%s&sale_supplier=%s" %
            (sproduct.status, supplier_id))


class SaleProductAdd(generics.ListCreateAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = serializers.SaleProductSerializer
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
        sale_category = serializers.SaleCategorySerializer(sale_category, many=True).data
        supplier_id = request.GET.get('sale_supplier', '')
        supplier = None
        if supplier_id:
            supplier = get_object_or_404(SaleSupplier, pk=supplier_id)
            progress = request.GET.get('progress', '')
            if (progress and progress != supplier.progress and
                    progress in dict(SaleSupplier.PROGRESS_CHOICES).keys()):
                supplier.progress = progress
                supplier.save()
            supplier = serializers.SaleSupplierSerializer(supplier,
                                              context={'request': request}).data
        result_data = {'request_data': request.GET.dict(),
                       'supplier': supplier,
                       'sale_category': sale_category,
                       "results": resp_data}
        return Response(result_data)

    def post(self, request, *args, **kwargs):
        data = request.data
        supplier_id = data["supplier"]
        supplier = get_object_or_404(SaleSupplier, pk=supplier_id)
        if not supplier.is_active():
            return Response({'code': 1,
                             'error_response': '供应商已被淘汰，不能添加商品',
                             'request_data': request.GET.dict()})
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
        return HttpResponseRedirect(
            "/supplychain/supplier/line_product/?status=%s&sale_supplier=%s" %
            (sproduct.status, supplier_id))


class SaleProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SaleProduct.objects.all()
    serializer_class = serializers.SaleProductUpdateSerializer
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if not instance.contactor:
            instance.contactor = self.request.user

        serializer = self.get_serializer(instance,
                                         data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        index_map = {SaleProduct.SELECTED: 1,
                     SaleProduct.PURCHASE: 2,
                     SaleProduct.PASSED: 3,
                     SaleProduct.SCHEDULE: 4}

        instance.orderlist_show_memo = False
        update_field_labels = []
        for k, v in request.data.iteritems():
            if not hasattr(instance, k):
                continue
            if k == 'orderlist_show_memo':
                instance.orderlist_show_memo = v.lower() in ('on', 'true')
                instance.save(update_fields=['orderlist_show_memo'])
            update_field_labels.append('%s:%s' % (
                SaleProduct._meta.get_field(k).verbose_name.title(), v))

        status_label = (u'淘汰', u'初选入围', u'洽谈通过', u'审核通过',
                        u'排期')[index_map.get(instance.status, 0)]
        log_action(request.user.id, instance, CHANGE,
                   '%s(%s)' % (status_label, ','.join(update_field_labels)))
        return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        sale_time = ''
        if instance.sale_time:
            sale_time = instance.sale_time.strftime('%Y-%m-%d')
        return Response({
            'pic_url': instance.pic_url,
            'sale_time': sale_time,
            'product_category': self.get_category_mapping().get(
                str(instance.sale_category_id)) or {},
            'on_sale_price': instance.on_sale_price or '',
            'std_sale_price': instance.std_sale_price or '',
            'sale_price': instance.sale_price or '',
            'supplier_sku': instance.supplier_sku,
            'remain_num': instance.remain_num or 10
        })

    @classmethod
    def get_category_mapping(cls):
        cache_key = '%s.get_category_mapping'%__name__

        def _load():
            parent_product_categories = {}
            for product_category in ProductCategory.objects.filter(
                    parent_cid=constants.XIAOLU_ROOT_CATEGORY_ID,
                    is_parent=True,
                    status='normal'):
                parent_product_categories[product_category.cid] = product_category

            product_categories = {}
            for product_category in ProductCategory.objects.filter(
                    is_parent=False,
                    status='normal'):
                parent_category = parent_product_categories.get(
                    product_category.parent_cid)
                if not parent_category:
                    continue
                full_name = '%s/%s' % (parent_category.name,
                                       product_category.name)
                product_categories[full_name] = {
                    'level_3_id': product_category.cid,
                    'level_2_id': parent_category.cid,
                    'level_1_id': constants.XIAOLU_ROOT_CATEGORY_ID
                }
            for parent_id, parent_product_category in parent_product_categories.iteritems(
            ):
                product_categories[parent_product_category.name] = {
                    'level_3_id': 0,
                    'level_2_id': parent_product_category.cid,
                    'level_1_id': constants.XIAOLU_ROOT_CATEGORY_ID
                }
            parent_sale_categories = {}
            for sale_category in SaleCategory.objects.filter(parent_cid=0,
                                                             is_parent=True,
                                                             status='normal'):
                parent_sale_categories[str(sale_category.id)] = sale_category
            sale_categories = {}
            for sale_category in SaleCategory.objects.filter(status='normal'):
                parent_category = parent_sale_categories.get(
                    sale_category.parent_cid)
                if not parent_category:
                    full_name = sale_category.name
                else:
                    full_name = '%s/%s' % (parent_category.name,
                                           sale_category.name)
                sale_categories[str(sale_category.id)] = product_categories.get(
                    full_name) or {}
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

    SUPPLIER_SKU_PATTERN = re.compile(r'^[\w\-_#]*$')

    def getItemPrice(self, soup):
        return 0

    def get_img_src(self, img):
        attr_map = dict(img.attrs)
        img_src = attr_map and attr_map.get('src') or attr_map.get('data-src')
        if img_src and img_src.split('?')[0].endswith('.jpg'):
            return img_src
        return ''

    def get_link_img_src(self, link):
        for img in link.findAll('img'):
            return self.get_img_src(img)
        return ''

    def getItemPic(self, fetch_url, soup):
        pic_path_pattern = re.compile(r'(.+\.jpg)_.+')
        container = soup.findAll(attrs={'class': re.compile(
            '^(deteilpic|zoomPad|SPSX_bian3|goods-detail-pic|container|florid-goods-page-container|m-item-grid|jqzoom|cloud-zoom)')
                                        })

        for c in container:
            for img in c.findAll('img'):
                img_src = self.get_img_src(img)
                if img_src:
                    image_url_components = urlparse.urlparse(img_src)
                    if not image_url_components.netloc:
                        fetch_url_components = urlparse.urlparse(fetch_url)
                        return '%s://%s%s' % (fetch_url_components.scheme,
                                           fetch_url_components.netloc,
                                           image_url_components.path)
                    return img_src

        alinks = soup.findAll('a')
        for a in alinks:
            img_src = self.get_link_img_src(a)
            m = pic_path_pattern.match(img_src)
            if m:
                return m.group(1)
            if img_src:
                image_url_components = urlparse.urlparse(img_src)
                if not image_url_components.netloc:
                    fetch_url_components = urlparse.urlparse(fetch_url)
                    return '%s://%s%s' % (fetch_url_components.scheme,
                                       fetch_url_components.netloc,
                                       image_url_components.path)
                return img_src
        return ''

    def getItemTitle(self, soup):
        try:
            return soup.findAll('title')[0].text.strip()
        except:
            return ''

    def getSupplierSku(self, fetch_url, soup):
        fetch_url_components = urlparse.urlparse(fetch_url)
        host_name = fetch_url_components.netloc

        def _is_1688():
            return '1688' in host_name.split('.')

        def _is_tmall():
            return 'tmall' in host_name.split('.')

        def _is_gongxiao():
            return 'gongxiao' in host_name.split('.')

        def _get_1688():
            sku_tag = None
            for tag in soup.findAll('td', attrs={'class': re.compile('de-feature')}):
                if tag.text == u'货号':
                    sku_tag = tag.findNextSibling('td', attrs={'class': re.compile('de-value')})
            if sku_tag:
                return sku_tag.text.strip()

        if _is_1688():
            return _get_1688()
        return ''

    def get(self, request, pk):
        import core.upload

        fetch_url = request.REQUEST.get('fetch_url', '').strip()
        status = request.REQUEST.get('status', '')
        if not fetch_url or not fetch_url.startswith(('http://', 'https://')):
            raise Exception(u'请输入合法的URL')

        supplier = get_object_or_404(SaleSupplier, pk=pk)
        tsoup, response = getBeaSoupByCrawUrl(fetch_url)
        categorys = SaleCategory.get_normal_categorys().filter(is_parent=False).order_by('parent_cid')
        sale_category = serializers.SaleCategorySerializer(categorys, many=True).data

        data = {
            'title': self.getItemTitle(tsoup),
            'pic_url': self.getItemPic(fetch_url, tsoup),
            'price': self.getItemPrice(tsoup),
            'fetch_url': fetch_url,
            'supplier_sku': self.getSupplierSku(fetch_url, tsoup),
            'status': status,
            'categorys': sale_category,
            'supplier': serializers.SaleSupplierSerializer(
                supplier,
                context={'request': request}).data
        }
        return Response(data)

    def post(self, request, pk, format=None):
        content = request.REQUEST
        category_name = content.get('category_name', '')

        supplier = get_object_or_404(SaleSupplier, pk=pk)
        if not supplier.is_active():
            return Response({'code': 1, 'error_response': '供应商已被淘汰，不能添加商品'})

        is_exists = 0
        sproduct = None
        supplier_sku = content.get('supplier_sku')
        if supplier_sku:
            sproducts = SaleProduct.objects.filter(sale_supplier_id=pk, supplier_sku=supplier_sku)
            if sproducts:
                is_exists = 1
                sproduct = sproducts[0]
                return Response({'code': 2, 'error_response': '该选品已存在, 不能重复添加'})
            """
            m = self.SUPPLIER_SKU_PATTERN.match(supplier_sku)
            if not m:
                return Response({'code': 2, 'error_response': '供应商货号只能包含字母, 数字, 下划线(_), 横杠(-), 井号(#)'})
            """

        if not sproduct:
            sproduct, state = SaleProduct.objects.get_or_create(
                outer_id='OO%d' % time.time(),
                platform=supplier.platform)
            sproduct.sale_supplier = supplier
            sproduct.platform = SaleProduct.MANUAL
            sproduct.contactor = request.user


        for k, v in content.iteritems():
            if k == 'sale_category':
                v = SaleCategory.objects.get(id=v)
            if k == 'sale_time' and not v:
                continue
            if k == 'orderlist_show_memo':
                v = v.lower() in ('on', 'true')
            hasattr(sproduct, k) and setattr(sproduct, k, v)
        if supplier_sku:
            sproduct.supplier_sku = supplier_sku.strip()
        sproduct.status = sproduct.status or SaleProduct.SELECTED
        sproduct.save()

        # sale_time如果是unicode需要转换成datetime
        if isinstance(sproduct.sale_time, basestring):
            sproduct.sale_time = datetime.datetime.strptime(sproduct.sale_time,
                                                            '%Y-%m-%d %H:%M:%S')

        data = {'record':
                serializers.SaleProductSerializer(sproduct,
                                      context={'request': request}).data, 'is_exists': is_exists}
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
        instance = get_object_or_404(SaleProduct,
                                     id=args[0]) if len(args) == 1 else 0
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
            update_field_labels.append('%s:%s' % (
                SaleProduct._meta.get_field(k).verbose_name.title(), v))
            instance.__setattr__(k, v)
            update_model_fields(instance, update_fields=[k])
        status_label = (u'淘汰', u'初选入围', u'洽谈通过', u'审核通过',
                        u'排期')[index_map.get(instance.status, 0)]
        log_action(request.user.id, instance, CHANGE,
                   '%s(%s)' % (status_label, ','.join(update_field_labels)))
        return Response({"ok"})


class CategoryMappingView(APIView):
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        parent_product_categories = {}
        for product_category in ProductCategory.objects.filter(
                parent_cid=constants.XIAOLU_ROOT_CATEGORY_ID,
                is_parent=True,
                status='normal'):
            parent_product_categories[product_category.cid] = product_category

        product_categories = {}
        for product_category in ProductCategory.objects.filter(is_parent=False,
                                                               status='normal'):
            parent_category = parent_product_categories.get(
                product_category.parent_cid)
            if not parent_category:
                continue
            full_name = '%s/%s' % (parent_category.name, product_category.name)
            product_categories[full_name] = {
                'level_3_id': product_category.cid,
                'level_2_id': parent_category.cid,
                'level_1_id': constants.XIAOLU_ROOT_CATEGORY_ID
            }

        parent_sale_categories = {}
        for sale_category in SaleCategory.objects.filter(parent_cid=0,
                                                         is_parent=True,
                                                         status='normal'):
            parent_sale_categories[sale_category.id] = sale_category

        sale_categories = {}
        for sale_category in SaleCategory.objects.filter(is_parent=False,
                                                         status='normal'):
            parent_category = parent_sale_categories.get(
                sale_category.parent_cid)
            if not parent_category:
                continue
            sale_categories[sale_category.id] = product_categories.get(
                '%s/%s' % (parent_category.name, sale_category.name)) or {}
        return Response(sale_categories)


class ScheduleDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer,)
    template_name = "scheduledetail.html"

    def get(self, request):
        schedule_id = int(request.GET.get('schedule_id') or 0)

        schedule = SaleProductManage.objects.get(id=schedule_id)
        sale_time = schedule.sale_time

        saleproduct_ids = set()
        for schedule_detail in schedule.manage_schedule.filter(today_use_status=SaleProductManageDetail.NORMAL):
            saleproduct_ids.add(schedule_detail.sale_product_id)

        scheduled_product_ids = []
        for product in Product.objects.filter(sale_product__in=list(saleproduct_ids), status=Product.NORMAL):
            scheduled_product_ids.append(product.id)

        product_ids = []
        for product in Product.objects.filter(sale_time=sale_time, status=Product.NORMAL):
            product_ids.append(product.id)

        diff_product_ids1 = set(product_ids) - set(scheduled_product_ids)
        diff_product_ids2 = set(scheduled_product_ids) - set(product_ids)

        total_n = len(product_ids)
        scheduled_n = len(scheduled_product_ids)

        return Response({
            'total_n': total_n,
            'scheduled_n': scheduled_n,
            'q1': ','.join(map(str, diff_product_ids1)),
            'q2': ','.join(map(str, diff_product_ids2))
        })


class ScheduleDetailAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        schedule_id = int(request.GET.get('schedule_id') or 0)
        if not schedule_id:
            return Response({'data': []})
        schedule_manage = SaleProductManage.objects.filter(pk=schedule_id)
        if not schedule_manage:
            return Response({'data': []})
        schedule_details = {}
        for detail in schedule_manage[0].manage_schedule.filter(
                today_use_status=u'normal'):
            schedule_details[detail.sale_product_id] = (detail.id,
                                                        detail.is_approved)

        sale_products = {}
        for sale_product in SaleProduct.objects.select_related(
                'sale_supplier',
                'contactor').filter(pk__in=schedule_details.keys()):
            contactor_name = '%s%s' % (sale_product.contactor.last_name,
                                       sale_product.contactor.first_name)
            contactor_name = contactor_name or sale_product.contactor.username
            level_1_category_name, level_2_category_name = SaleCategory.get_category_names(
                sale_product.sale_category_id)
            schedule_detail_id, is_approved = schedule_details[sale_product.id]
            sale_products[sale_product.id] = {
                'sale_product_id': sale_product.id,
                'schedule_detail_id': schedule_detail_id,
                'supplier_sku': sale_product.supplier_sku or '未知',
                'name': sale_product.title,
                'sale_product_category_id': sale_product.sale_category_id,
                'level_1_category_name': level_1_category_name,
                'level_2_category_name': level_2_category_name,
                'pic_path': '%s?imageView2/0/w/120' % sale_product.pic_url,
                'supplier_id': sale_product.sale_supplier.id,
                'supplier_name': sale_product.sale_supplier.supplier_name,
                'contactor_name': contactor_name,
                'product_link': sale_product.product_link,
                'has_product': 0,
                'sale_price': sale_product.sale_price,
                'std_sale_price': sale_product.std_sale_price,
                'on_sale_price': sale_product.on_sale_price,
                'remain_num': sale_product.remain_num,
                'is_approved': '是' if is_approved else '否',
                'collect_num': 0,
                'order_weight': 0,
                'model_id': 0,
                'preview_url': '',
                'outer_id': '',
                'is_verify': True,
                'note': ''
            }

        product_outer_ids = []
        skus_dict = {}
        skus_dict2 = {}
        for product in Product.objects.filter(
                sale_product__in=sale_products.keys(),
                status=u'normal').only('pic_path', 'outer_id'):
            product_outer_ids.append(product.outer_id)
            sale_product = sale_products.get(product.sale_product)
            sale_product['is_verify'] = sale_product['is_verify'] and product.is_verify
            if product.outer_id and not sale_product.get('outer_id'):
                sale_product['outer_id'] = product.outer_id[:-1]
            if product.outer_id and product.outer_id[-1] == '1':
                sale_product['model_id'] = product.model_id
                sale_product['outer_id'] = product.outer_id[:-1]
                if hasattr(product, 'details'):
                    sale_product['note'] = product.details.note
                if product.model_id:
                    try:
                        model_product = ModelProduct.objects.get(
                            pk=product.model_id)
                        sale_product['name'] = model_product.name
                        sale_product['preview_url'] = '/static/wap/tongkuan-preview.html?id=%d' % model_product.id
                    except:
                        pass

                sale_product['has_product'] = 1
                sale_product[
                    'pic_path'] = '%s?imageView2/0/w/120' % product.pic_path.strip(
                    )
                product_detail, _ = Productdetail.objects.get_or_create(
                    product=product)
                sale_product['order_weight'] = product_detail.order_weight
                # It's dirty
                product_detail.save()

            collect_num = 0
            remain_nums = []
            for sku in product.prod_skus.filter(status='normal'):
                collect_num += sku.quantity
                remain_nums.append(sku.remain_num or 0)
                sku_dict = {
                    'id': sku.id,
                    'num': sku.quantity,
                    'remain_num': sku.remain_num,
                    'sale_num': 0,
                    'buy_num': 0
                }
                skus_dict['%s-%s' % (product.outer_id, sku.outer_id)] = sku_dict
                skus_dict2['%d-%d' % (product.id, sku.id)] = sku_dict
                sale_product.setdefault('sku_keys', []).append('%d-%d' % (product.id, sku.id))
            sale_product.setdefault('collect_nums', []).append(collect_num)
            sale_product.setdefault('remain_nums', []).extend(remain_nums)

        sale_stats = MergeOrder.objects.select_related('merge_trade').filter(
            merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                                   pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
            merge_trade__sys_status__in=
            [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
             pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
             pcfg.REGULAR_REMAIN_STATUS],
            sys_status=pcfg.IN_EFFECT, outer_id__in=product_outer_ids).values(
                'outer_id', 'outer_sku_id').annotate(sale_num=Sum('num'))
        for s in sale_stats:
            sku_dict = skus_dict.get('%s-%s' % (s['outer_id'], s['outer_sku_id']))
            if sku_dict:
                sku_dict['sale_num'] = s['sale_num']

        dinghuo_stats = OrderDetail.objects \
          .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
          .filter(chichu_id__in=map(lambda x: str(x['id']), skus_dict.values())) \
          .values('product_id', 'chichu_id') \
          .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                        inferior_quantity=Sum('inferior_quantity'))
        for s in dinghuo_stats:
            skus_dict2['%s-%s' % (s['product_id'], s['chichu_id'])]['buy_num'] = s['buy_quantity'] - \
              min(s['buy_quantity'], s['arrival_quantity']) - s['inferior_quantity']


        items = []
        for k in sorted(sale_products.keys(), reverse=True):
            item = sale_products[k]
            item['remain_num'] = min(item.get('remain_nums') or [0])
            item['collect_num'] = sum(item.get('collect_nums') or [])
            is_sync_stock = bool(item.get('sku_keys'))
            for sku_key in item.get('sku_keys') or []:
                sku_dict = skus_dict2[sku_key]
                left_num = sku_dict['num'] + sku_dict['buy_num'] - sku_dict['sale_num']
                if left_num != sku_dict['remain_num']:
                    is_sync_stock = False
                    break
            item['is_sync_stock'] = is_sync_stock
            item.pop('collect_nums', False)
            item.pop('sku_keys', False)
            item.pop('remain_nums', False)
            items.append(item)
        return Response({'data': items})

    def post(self, request):
        m = None
        pattern = re.compile(r'data\[(\w+)\]\[(\w+)\]')
        for k in request.data:
            m = pattern.match(k)
            if m:
                break
        if not m:
            return Response({'error': u'参数错误'})
        typed_value = None
        _id, field = m.group(1, 2)

        value = request.data.get(k) or ''
        _id = int(_id)
        schedule_detail = SaleProductManageDetail.objects.get(pk=_id)
        _id = schedule_detail.sale_product_id

        if field == 'name':
            typed_value = value
            if typed_value:
                model_id = 0
                for product in Product.objects.filter(sale_product=_id,
                                                      status='normal'):
                    if product.outer_id and product.outer_id[-1] == '1':
                        model_id = product.model_id
                    parts = product.name.rsplit('/', 1)
                    if len(parts) > 1:
                        _, color = parts[:2]
                    else:
                        color = ''
                    if color:
                        product.name = '%s/%s' % (typed_value, color)
                    else:
                        product.name = typed_value
                    product.save()
                    log_action(request.user.id, product, CHANGE, u'修改名称: %s' % product.name)

                if model_id:
                    ModelProduct.objects.filter(pk=model_id).update(
                        name=typed_value)

        elif field == 'remain_num':
            try:
                typed_value = int(value)
                SaleProduct.objects.filter(pk=_id).update(
                    remain_num=typed_value)
                for product in Product.objects.filter(sale_product=_id,
                                                      status='normal'):
                    product.remain_num = typed_value
                    product.save()
                    log_action(request.user.id, product, CHANGE, u'修改预留数: %d' % product.remain_num)
                    ProductSku.objects.filter(product_id=product.id,
                                              status='normal').update(
                                                  remain_num=typed_value)
                    for sku in product.prod_skus.filter(status='normal'):
                        log_action(request.user.id, sku, CHANGE, u'修改预留数: %d' % sku.remain_num)

            except:
                typed_value = None
        elif field == 'order_weight':
            try:
                typed_value = int(value)
                if typed_value < 0 or typed_value > 100:
                    return Response({'error': '参数错误'})
                else:
                    schedule_detail.order_weight = typed_value
                    schedule_detail.save(update_fields=['order_weight'])
                    log_action(request.user.id, schedule_detail, CHANGE, u'修改权重: %d' % typed_value)
                    for product in Product.objects.filter(sale_product=_id,
                                                          status='normal'):
                        product_detail, _ = Productdetail.objects.get_or_create(
                            product=product)
                        product_detail.order_weight = typed_value
                        product_detail.save()
                        log_action(request.user.id, product, CHANGE, u'修改权重: %d' % typed_value)

            except:
                typed_value = None

        elif field in ['sale_price', 'on_sale_price', 'std_sale_price']:
            try:
                typed_value = float(value)
                if field == 'sale_price':
                    SaleProduct.objects.filter(pk=_id).update(
                        sale_price=typed_value)
                    for product in Product.objects.filter(sale_product=_id,
                                                          status='normal'):
                        product.cost = typed_value
                        product.save()
                        log_action(request.user.id, product, CHANGE, u'修改采购价: %.2f' % product.cost)
                        ProductSku.objects.filter(product_id=product.id,
                                                  status='normal').update(
                                                      cost=typed_value)
                        for sku in product.prod_skus.filter(status='normal'):
                            log_action(request.user.id, sku, CHANGE, u'修改采购价: %.2f' % sku.cost)

                elif field == 'std_sale_price':
                    SaleProduct.objects.filter(pk=_id).update(
                        std_sale_price=typed_value)
                    for product in Product.objects.filter(sale_product=_id,
                                                          status='normal'):
                        product.std_sale_price = typed_value
                        product.save()
                        log_action(request.user.id, product, CHANGE, u'修改吊牌价: %.2f' % product.std_sale_price)
                        ProductSku.objects.filter(
                            product_id=product.id,
                            status='normal').update(std_sale_price=typed_value)
                        for sku in product.prod_skus.filter(status='normal'):
                            log_action(request.user.id, sku, CHANGE, u'修改吊牌价: %.2f' % sku.std_sale_price)
                elif field == 'on_sale_price':
                    SaleProduct.objects.filter(pk=_id).update(
                        on_sale_price=typed_value)
                    for product in Product.objects.filter(sale_product=_id,
                                                          status='normal'):
                        product.agent_price = typed_value
                        product.save()
                        log_action(request.user.id, product, CHANGE, u'修改售价: %.2f' % product.agent_price)
                        ProductSku.objects.filter(product_id=product.id,
                                                  status='normal').update(
                                                      agent_price=typed_value)
                        for sku in product.prod_skus.filter(status='normal'):
                            log_action(request.user.id, sku, CHANGE, u'修改售价: %.2f' % sku.agent_price)
            except:
                typed_value = None

        if typed_value == None:
            return Response({'error': u'参数错误'})
        # 重新获取sku
        sale_product = SaleProduct.objects.select_related(
            'sale_supplier', 'contactor').get(pk=_id)
        contactor_name = '%s%s' % (sale_product.contactor.last_name,
                                   sale_product.contactor.first_name)
        contactor_name = contactor_name or sale_product.contactor.username
        level_1_category_name, level_2_category_name = SaleCategory.get_category_names(
            sale_product.sale_category_id)
        item = {
            'sale_product_id': _id,
            'schedule_detail_id': schedule_detail.id,
            'supplier_sku': sale_product.supplier_sku,
            'name': sale_product.title,
            'sale_product_category_id': sale_product.sale_category_id,
            'level_1_category_name': level_1_category_name,
            'level_2_category_name': level_2_category_name,
            'pic_path': '%s?imageView2/0/w/120' % sale_product.pic_url,
            'supplier_id': sale_product.sale_supplier.id,
            'supplier_name': sale_product.sale_supplier.supplier_name,
            'contactor_name': contactor_name,
            'product_link': sale_product.product_link,
            'has_productc': 0,
            'sale_price': sale_product.sale_price,
            'std_sale_price': sale_product.std_sale_price,
            'on_sale_price': sale_product.on_sale_price,
            'remain_num': sale_product.remain_num,
            'is_approved': '是' if schedule_detail.is_approved else '否',
            'collect_num': 0,
            'order_weight': 0,
            'model_id': 0,
            'is_verify': True
        }

        collect_num = 0
        is_sync_stock = True
        remain_nums = []

        product_outer_ids = []
        skus_dict = {}
        skus_dict2 = {}
        for product in Product.objects.filter(sale_product=_id,
                                              status='normal').only('pic_path',
                                                                    'outer_id'):
            product_outer_ids.append(product.outer_id)
            item['is_verify'] = item['is_verify'] and product.is_verify
            if product.outer_id and not item.get('outer_id'):
                item['outer_id'] = product.outer_id
            if product.outer_id and product.outer_id[-1] == '1':
                item['model_id'] = product.model_id
                item['outer_id'] = product.outer_id[:-1]
                if product.model_id:
                    try:
                        model_product = ModelProduct.objects.get(
                            pk=product.model_id)
                        item['name'] = model_product.name
                        item['preview_url'] = '/static/wap/tongkuan-preview.html?id=%d' % model_product.id
                    except:
                        pass
                item['has_product'] = 1
                item[
                    'pic_path'] = '%s?imageView2/0/w/120' % product.pic_path.strip(
                    )
                product_detail, _ = Productdetail.objects.get_or_create(
                    product=product)
                item['order_weight'] = product_detail.order_weight
                item['note'] = product_detail.note

            for sku in product.prod_skus.filter(status='normal'):
                collect_num += (sku.quantity or 0)
                remain_nums.append(sku.remain_num or 0)
                sku_dict = {
                    'id': sku.id,
                    'num': sku.quantity,
                    'remain_num': sku.remain_num,
                    'sale_num': 0,
                    'buy_num': 0
                }
                skus_dict['%s-%s' % (product.outer_id, sku.outer_id)] = sku_dict
                skus_dict2['%d-%d' % (product.id, sku.id)] = sku_dict

        sale_stats = MergeOrder.objects.select_related('merge_trade').filter(
            merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                                   pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
            merge_trade__sys_status__in=
            [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
             pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
             pcfg.REGULAR_REMAIN_STATUS],
            sys_status=pcfg.IN_EFFECT, outer_id__in=product_outer_ids).values(
                'outer_id', 'outer_sku_id').annotate(sale_num=Sum('num'))
        for s in sale_stats:
            sku_dict = skus_dict.get('%s-%s' % (s['outer_id'], s['outer_sku_id']))
            if sku_dict:
                sku_dict['sale_num'] = s['sale_num']

        dinghuo_stats = OrderDetail.objects \
          .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
          .filter(chichu_id__in=map(lambda x: str(x['id']), skus_dict.values())) \
          .values('product_id', 'chichu_id') \
          .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                        inferior_quantity=Sum('inferior_quantity'))
        for s in dinghuo_stats:
            skus_dict2['%s-%s' % (s['product_id'], s['chichu_id'])]['buy_num'] = s['buy_quantity'] - \
              min(s['buy_quantity'], s['arrival_quantity']) - s['inferior_quantity']

        is_sync_stock = bool(skus_dict.values())
        for sku_dict in skus_dict.values():
            left_num = sku_dict['num'] + sku_dict['buy_num'] - sku_dict['sale_num']
            if left_num != sku_dict['remain_num']:
                is_sync_stock = False
                break
        item['is_sync_stock'] = is_sync_stock
        item['remain_num'] = min(remain_nums or [0])
        item['collect_num'] = collect_num
        return Response({'data': [item]})


class CollectNumAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        sale_product_id = int(request.GET.get('sale_product_id') or 0)
        products = {}
        for product in Product.objects.filter(sale_product=sale_product_id,
                                              status='normal'):
            parts = product.name.rsplit('/', 1)
            if len(parts) > 1:
                name, color = parts[:2]
            elif len(parts) == 1:
                name, color = parts[0], u'未知'
            else:
                name, color = (u'未知',) * 2
            products[product.id] = {
                'product_id': product.id,
                'name': name,
                'color': color
            }

        for sku in ProductSku.objects.filter(product_id__in=products.keys(),
                                             status='normal'):
            product = products[sku.product_id]
            skus = product.setdefault('skus', [])
            skus.append({
                'sku_id': sku.id,
                'properties_name': sku.properties_name,
                'quantity': sku.quantity
            })
        items = []
        for k in sorted(products.keys(), reverse=True):
            product = products[k]
            for sku in product.get('skus', []):
                item = copy.copy(product)
                item.pop('skus', False)
                item.update(sku)
                items.append(item)
        return Response({'data': items})


class RemainNumAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        sale_product_id = int(request.GET.get('sale_product_id') or 0)
        products_dict = {}
        for product in Product.objects.filter(sale_product=sale_product_id,
                                              status='normal'):
            parts = product.name.rsplit('/', 1)
            if len(parts) > 1:
                name, color = parts[:2]
            elif len(parts) == 1:
                name, color = parts[0], u'未知'
            else:
                name, color = (u'未知',) * 2
            products_dict[product.id] = {
                'product_id': product.id,
                'name': name,
                'color': color,
                'outer_id': product.outer_id
            }

        skus_dict = {}
        skus_dict2 = {}
        for sku in ProductSku.objects.filter(product_id__in=products_dict.keys(),
                                             status='normal'):
            product = products_dict[sku.product_id]
            sku_dict = {
                'sku_id': sku.id,
                'properties_name': sku.properties_name,
                'remain_num': sku.remain_num,
                'sale_num': 0,
                'buy_num': 0,
                'num': sku.quantity
            }
            skus_dict['%s-%s' % (product['outer_id'], sku.outer_id)] = sku_dict
            skus_dict2['%d-%d' % (product['product_id'], sku.id)] = sku_dict
            product.setdefault('skus', []).append(sku_dict)

        sale_stats = MergeOrder.objects.select_related('merge_trade').filter(
            merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                                   pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
            merge_trade__sys_status__in=
            [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
             pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
             pcfg.REGULAR_REMAIN_STATUS],
            sys_status=pcfg.IN_EFFECT, outer_id__in=map(lambda x: x['outer_id'], products_dict.values())).values(
                'outer_id', 'outer_sku_id').annotate(sale_num=Sum('num'))
        for s in sale_stats:
            sku_dict = skus_dict.get('%s-%s' % (s['outer_id'], s['outer_sku_id']))
            if sku_dict:
                sku_dict['sale_num'] = s['sale_num']


        dinghuo_stats = OrderDetail.objects \
          .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
          .filter(chichu_id__in=map(lambda x: str(x['sku_id']), skus_dict.values())) \
          .values('product_id', 'chichu_id') \
          .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                        inferior_quantity=Sum('inferior_quantity'))
        for s in dinghuo_stats:
            skus_dict2['%s-%s' % (s['product_id'], s['chichu_id'])]['buy_num'] = s['buy_quantity'] - \
              min(s['buy_quantity'], s['arrival_quantity'] + s['inferior_quantity'])

        items = []
        for k in sorted(products_dict.keys(), reverse=True):
            product = products_dict[k]
            for sku in product.get('skus', []):
                item = copy.copy(product)
                item.pop('skus', False)
                item.update(sku)
                item['left_num'] = item['num'] + item['buy_num'] - item['sale_num']
                items.append(item)
        return Response({'data': items})

    def post(self, request, *args, **kwargs):
        m = None
        pattern = re.compile(r'data\[(\w+)\]\[(\w+)\]')
        for k in request.data:
            m = pattern.match(k)
            if m:
                break
        if not m:
            return Response({'error': u'参数错误'})

        typed_value = None
        _id, field = m.group(1, 2)
        value = request.data.get(k) or ''
        _id = int(_id)
        sku = ProductSku.objects.get(pk=_id)
        try:
            typed_value = int(value)
            if typed_value < 0:
                return Response({'error': u'参数错误'})
            ProductSku.objects.filter(pk=_id).update(remain_num=typed_value)
            stat = sku.product.prod_skus.filter(status='normal').aggregate(remain_sum=Sum('remain_num'))
            sku.product.remain_num = stat.get('remain_sum') or 0
            sku.product.save()

            log_action(request.user.id, sku, CHANGE, u'修改预留数: %d' % sku.remain_num)
            log_action(request.user.id, sku.product, CHANGE, u'修改预留数: %d' % sku.product.remain_num)

        except:
            import traceback
            traceback.print_exc()
            return Response({'error': u'参数错误'})

        parts = sku.product.name.rsplit('/', 1)
        if len(parts) > 1:
            name, color = parts[:2]
        elif len(parts) == 1:
            name, color = parts[0], u'未知'
        else:
            name, color = (u'未知',) * 2

        sale_stats = MergeOrder.objects.select_related('merge_trade').filter(
            merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                                   pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
            merge_trade__sys_status__in=
            [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
             pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
             pcfg.REGULAR_REMAIN_STATUS],
            sys_status=pcfg.IN_EFFECT, outer_id=sku.product.outer_id, outer_sku_id=sku.outer_id).values(
                'outer_id', 'outer_sku_id').annotate(sale_num=Sum('num'))[:1]
        if not sale_stats:
            sale_num = 0
        else:
            sale_num = sale_stats[0].get('sale_num') or 0

        dinghuo_stats = OrderDetail.objects \
          .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
          .filter(chichu_id=str(sku.id)) \
          .values('product_id', 'chichu_id') \
          .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                        inferior_quantity=Sum('inferior_quantity'))[:1]
        if not dinghuo_stats:
            buy_num = 0
        else:
            tmp = dinghuo_stats[0]
            buy_num = tmp['buy_quantity'] - min(tmp['buy_quantity'], tmp['arrival_quantity']) - tmp['inferior_quantity']

        left_num = sku.quantity + buy_num - sale_num
        item = {
            'product_id': sku.product.id,
            'sku_id': sku.id,
            'name': name,
            'color': color,
            'properties_name': sku.properties_name,
            'remain_num': typed_value,
            'num': sku.quantity,
            'buy_num': buy_num,
            'sale_num': sale_num,
            'left_num': left_num
        }
        return Response({'data': [item]})


class SyncStockAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def post(self, request, *args, **kwargs):
        sale_product_id = int(request.POST.get('sale_product_id') or 0)

        skus_dict = {}
        skus_dict2 = {}
        product_outer_ids = []
        product_ids = []
        for product in Product.objects.filter(sale_product=sale_product_id, status='normal'):
            product_ids.append(product.id)
            product_outer_ids.append(product.outer_id)
            for sku in product.prod_skus.filter(status='normal'):
                sku_dict = {
                    'id': sku.id,
                    'num': sku.quantity,
                    'remain_num': sku.remain_num,
                    'sale_num': 0,
                    'buy_num': 0
                }
                skus_dict['%s-%s' % (product.outer_id, sku.outer_id)] = sku_dict
                skus_dict2['%d-%d' % (product.id, sku.id)] = sku_dict

        sale_stats = MergeOrder.objects.select_related('merge_trade').filter(
            merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                                   pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
            merge_trade__sys_status__in=
            [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
             pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
             pcfg.REGULAR_REMAIN_STATUS],
            sys_status=pcfg.IN_EFFECT, outer_id__in=product_outer_ids).values(
                'outer_id', 'outer_sku_id').annotate(sale_num=Sum('num'))
        for s in sale_stats:
            skus_dict['%s-%s' % (s['outer_id'], s['outer_sku_id'])]['sale_num'] = s['sale_num']

        dinghuo_stats = OrderDetail.objects \
          .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
          .filter(product_id__in=map(str, product_ids)) \
          .values('product_id', 'chichu_id') \
          .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                        inferior_quantity=Sum('inferior_quantity'))
        for s in dinghuo_stats:
            skus_dict2['%s-%s' % (s['product_id'], s['chichu_id'])]['buy_num'] = s['buy_quantity'] - \
              min(s['buy_quantity'], s['arrival_quantity']) - s['inferior_quantity']


        for product in Product.objects.filter(sale_product=sale_product_id,
                                              status='normal'):
            collect_num = 0
            for sku in product.prod_skus.filter(status='normal'):
                sku_dict = skus_dict2['%d-%d' % (product.id, sku.id)]
                left_num = sku.quantity + sku_dict['buy_num'] - sku_dict['sale_num']
                collect_num += left_num
                sku.remain_num = left_num
                sku.save()
                log_action(request.user.id, sku, CHANGE, u'修改预留数: %d' % sku.remain_num)
            product.collect_num = collect_num
            product.remain_num = collect_num
            product.save()
            log_action(request.user.id, product, CHANGE, u'修改预留数: %d' % product.remain_num)
            log_action(request.user.id, product, CHANGE, u'修改库存: %d' % product.collect_num)
        return Response({'msg': 'OK'})


class ScheduleDetailApproveAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def post(self, request, *args, **kwargs):
        schedule_detail_id = int(request.POST.get('schedule_detail_id') or 0)
        is_approved = (request.POST.get('is_approved') or '是').strip()
        is_approved = 0 if is_approved == '是' else 1
        SaleProductManageDetail.objects.filter(pk=schedule_detail_id).update(
            is_approved=is_approved)
        return Response({'is_approved': '是' if is_approved else '否'})


class ScheduleExportView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        form = forms.SaleProductManageExportForm(request.GET)
        if not form.is_valid():
            return Response('fail')

        items = []
        sale_product_ids = set()
        for m in SaleProductManage.objects.filter(
                sale_time__gte=form.cleaned_attrs.from_date,
                sale_time__lte=form.cleaned_attrs.end_date):
            date_str = m.sale_time.strftime('%Y%m%d')
            for d in m.manage_schedule.filter(today_use_status='normal'):
                sale_product_ids.add(d.sale_product_id)
                items.append({
                    'sale_product_id': d.sale_product_id,
                    'date': date_str,
                    'id': d.id
                })

        sale_products = {}
        for sale_product in SaleProduct.objects.select_related(
                'sale_supplier', 'contactor').filter(
                    pk__in=list(sale_product_ids)):
            if sale_product.contactor:
                contactor_name = '%s%s' % (sale_product.contactor.last_name,
                                           sale_product.contactor.first_name)
                contactor_name = contactor_name or sale_product.contactor.username
            else:
                contactor_name = '未知'

            level_1_category_name, level_2_category_name = SaleCategory.get_category_names(
                sale_product.sale_category_id)
            sale_products[sale_product.id] = {
                'sale_product_name': sale_product.title,
                'supplier_name': sale_product.sale_supplier.supplier_name,
                'contactor_name': contactor_name,
                'level_1_category_name': level_1_category_name
            }

        new_items = []
        for item in sorted(items,
                           key=lambda x: (x['date'], x['id']),
                           reverse=True):
            sale_product = sale_products.get(item['sale_product_id']) or {}
            item.update(sale_product)
            new_items.append(item)

        filename = 'schedule-%s-%s.xlsx' % (
            form.cleaned_attrs.from_date.strftime('%Y%m%d'),
            form.cleaned_attrs.end_date.strftime('%Y%m%d'))
        buff = StringIO()
        workbook = xlsxwriter.Workbook(buff)
        worksheet = workbook.add_worksheet()
        date_format = workbook.add_format({'num_format': 'yyyymmdd'})
        bold = workbook.add_format({'bold': True})

        worksheet.set_column('A:A', 100)
        worksheet.set_column('C:C', 50)

        worksheet.write('A1', '选品名', bold)
        worksheet.write('B1', '类别', bold)
        worksheet.write('C1', '供应商', bold)
        worksheet.write('D1', '买手', bold)
        worksheet.write('E1', '上架日期', bold)

        row = 1
        for item in new_items:
            worksheet.write(row, 0, item.get('sale_product_name') or '')
            worksheet.write(row, 1, item.get('level_1_category_name') or '')
            worksheet.write(row, 2, item.get('supplier_name') or '')
            worksheet.write(row, 3, item.get('contactor_name') or '')
            worksheet.write(row, 4, item['date'], date_format)
            row += 1
        workbook.close()

        response = HttpResponse(
            buff.getvalue(),
            content_type=
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        return response


class SaleProductScheduleDateView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        saleproduct_id = int(request.GET['saleproduct_id'])

        schedule_ids = set()
        for schedule_detail in SaleProductManageDetail.objects.filter(sale_product_id=saleproduct_id, today_use_status=SaleProductManageDetail.NORMAL):
            schedule_ids.add(schedule_detail.schedule_manage_id)

        sale_dates = set()
        for schedule in SaleProductManage.objects.filter(id__in=list(schedule_ids)):
            if schedule.sale_time:
                sale_dates.add(schedule.sale_time)
        sale_date_strs = [x.strftime('%y年%m月%d') for x in sorted(list(sale_dates))]
        return Response({'select_dates': sale_date_strs})



class SaleProductNoteView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        saleproduct_id = int(request.GET['saleproduct_id'])
        note = ''
        product = Product.objects.filter(status=Product.NORMAL,
                                         sale_product=saleproduct_id,
                                         outer_id__iendswith='1'
                                         ).first()
        if product and hasattr(product, 'details'):
            note = product.details.note
        return Response({'note': note})

    def post(self, request):
        saleproduct_id = int(request.POST['saleproduct_id'])
        note = request.POST.get('note') or ''
        if not note:
            return Response({})
        for product in Product.objects.filter(status=Product.NORMAL,
                                              sale_product=saleproduct_id):
            if hasattr(product, 'details'):
                product.details.note = note
                product.details.save()
        return Response({'note': note})

class SaleProductSaleQuantityView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        saleproduct_id = int(request.GET['saleproduct_id'])

        product_ids = []
        for product in Product.objects.filter(sale_product=saleproduct_id).only('id'):
            product_ids.append(product.id)

        product_ids = [str(x) for x in product_ids]
        pay_dates_dict = {}
        for saleorder in SaleOrder.objects.filter(item_id__in=product_ids, status__gte=SaleOrder.WAIT_SELLER_SEND_GOODS):
            if not saleorder.pay_time:
                continue
            date_str = saleorder.pay_time.strftime('%y年%m月%d')
            pay_dates_dict[date_str] = pay_dates_dict.setdefault(date_str, 0) + saleorder.num
        return Response({'sale_dates': pay_dates_dict})
