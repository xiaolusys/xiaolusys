# -*- coding:utf8 -*-
import time
import datetime
import django_filters
import hashlib
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.parsers import JSONParser
from rest_framework.decorators import detail_route, list_route
from rest_framework.decorators import parser_classes
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from rest_framework import filters
from django_filters import Filter
from django_filters.fields import Lookup
from core.options import get_systemoa_user, log_action
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES
from shopback.items.models import Product
from supplychain.supplier.models import (
    SaleSupplier,
    SaleProduct,
    SaleCategory,
    SupplierZone,
    SaleProductManage,
    SaleProductManageDetail,
    CategoryPreference,
    PreferencePool
)
from supplychain.supplier import serializers
from supplychain.basic import fetch_urls

import logging

logger = logging.getLogger(__name__)


class ListFilter(Filter):
    def filter(self, qs, value):
        value_list = [s for s in value.split(u',') if s]
        if not value_list:
            return qs
        return super(ListFilter, self).filter(qs, Lookup(value_list, 'in'))


class SaleSupplierFilter(filters.FilterSet):
    id = ListFilter(name='id')
    progress = ListFilter(name='progress')
    category = ListFilter(name='category')
    supplier_zone = ListFilter(name='supplier_zone')
    created_start = django_filters.DateFilter(name="created", lookup_type='gte')
    created_end = django_filters.DateFilter(name="created", lookup_type='lte')
    supplier_name = django_filters.CharFilter(name="supplier_name", lookup_type='contains')
    supplier_code = django_filters.CharFilter(name="supplier_code", lookup_type='contains')

    class Meta:
        model = SaleSupplier
        fields = ['id', 'category', 'supplier_name', 'supplier_code', 'supplier_type', 'supplier_zone', 'progress',
                  "mobile", 'created_start', 'created_end']


class SaleSupplierViewSet(viewsets.ModelViewSet):
    """
    ### 供应商REST API接口：
    - [/apis/chain/v1/supplier](/apis/chain/v1/supplier) 供应商列表:
        * method: GET
            1. 可过滤字段:
                * `id`: 供应商id
                * `category`: 类别
                * `supplier_name`:　名称
                * `supplier_type`:　类型
                * `supplier_zone`:　地区
                * `progress`:　进度
                * `created_start`:　最早创建时间
                * `created_end`:　最迟创建时间
            2. 可排序字段:
                * `id`: 供应商id
                * `created`: 创建时间
                * `modified`: 修改时间
                * `figures__payment`: 销售额
                * `figures__return_good_rate`: 退货率
                * `figures__out_stock_num`: 缺货率
        * method: POST
            1. 参数解释:
                * `supplier_name`: "小林的店铺2" 供应商名称  非空&唯一
                * `supplier_code`: "" 品牌缩写
                * `description`: ""　品牌简介
                * `brand_url`: ""　商标图片
                * `main_page`: ""　品牌主页
                * `product_link`: ""　商品链接
                * `platform`: ""　来自平台
                * `category`: 1　类别
                * `speciality`: ""　特长
                * `contact`: "linjie"　联系人 (非空)
                * `phone`: "",
                * `mobile`: "13739234188"　(非空)
                * `fax`: ""　传真
                * `zip_code`: ""　其他联系方式
                * `email`: ""　邮箱
                * `address`: "上海..."　(非空)
                * `account_bank`: ""　汇款银行
                * `account_no`: ""　汇款帐号
                * `memo`: ""　备注
                * `status`: ""　状态
                * `progress`: ""　进度
                * `supplier_type`: 0　
                * `supplier_zone`: 1, (非空)
                * `ware_by`:  1　(非空) 0:未选仓　1: 上海仓 2: 广州仓
        * method: PATCH
    - [/apis/chain/v1/supplier/list_filters](/apis/chain/v1/supplier/list_filters): 获取供应商过滤条件
    """
    queryset = SaleSupplier.objects.all()
    serializer_class = serializers.SaleSupplierSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('id', 'total_refund_num', 'total_sale_num', 'created', 'modified',
                       'figures__payment',
                       'figures__return_good_rate',
                       'figures__out_stock_num')
    filter_class = SaleSupplierFilter

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        categorys = SaleCategory.objects.filter(status=SaleCategory.NORMAL)
        return Response({
            'categorys': categorys.values_list('id', 'name', 'parent_cid', 'is_parent', 'sort_order'),
            'supplier_type': SaleSupplier.SUPPLIER_TYPE,
            'progress': SaleSupplier.PROGRESS_CHOICES,
            'supplier_zone': SupplierZone.objects.values_list('id', 'name'),
            'platform': SaleSupplier.PLATFORM_CHOICE,
            'ware_by': WARE_CHOICES,
            'return_ware_by': WARE_CHOICES,
            'status': SaleSupplier.STATUS_CHOICES,
        })

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        ordering = request.GET.get('ordering') or '-created'
        queryset = queryset.exclude(progress=SaleSupplier.REJECTED)\
            .extra(select={'refund_rate': 'total_refund_num/total_sale_num'}).order_by(ordering)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = request.user
        request.data.update({"buyer": user.id})
        serializer = serializers.SaleSupplierFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        raise exceptions.APIException('method not allowed!')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = serializers.SaleSupplierFormSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        log_action(request.user, instance, CHANGE, u'修改字段:%s' % ''.join(request.data.keys()))
        return Response(serializer.data)


class SaleCategoryViewSet(viewsets.ModelViewSet):
    """
    ### 特卖/选品类目 API

    #### GET /apis/chain/v1/salescategory  查询所有类目
    - cid, 类目ID，选填（获取该类目所有子类目）

    -----

    #### GET /apis/chain/v1/salescategory/[cid] 查询单个类目（[cid]）

    -----

    #### POST /apis/chain/v1/salescategory  创建类目
    - parent_cid, 父ID, 必填（一级类目填０）
    - name, 名称,　必填
    - cat_pic, 图片, 选填
    - sort_order, 权重, 选填

    -----

    #### PUT /apis/chain/v1/salescategory/[cid] 修改类目
    - parent_cid, 父ID, 必填（一级类目填０）
    - name, 名称,　必填
    - cat_pic, 图片, 选填
    - sort_order, 权重, 选填

    -----

    #### DELETE /apis/chain/v1/salescategory/[cid]  删除类目

    -----
    """
    queryset = SaleCategory.objects.all()
    serializer_class = serializers.SaleCategorySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = '__all__'

    def list(self, request, *args, **kwargs):
        tree = []
        cid = request.query_params.get('cid')
        if cid:
            items = SaleCategory.get_salecategory_jsontree()
            for item in items:
                if item.get('cid') == cid:
                    tree = [item]
                    break
        else:
            items = SaleCategory.get_salecategory_jsontree()
            tree = items

        def replace_key_name(dict_data, old_name, new_name):
            for k, v in dict_data.items():
                if k == old_name:
                    dict_data[new_name] = []
                    for item in dict_data.pop(k):
                        item = replace_key_name(item, 'childs', 'children')
                        dict_data[new_name].append(item)
            return dict_data

        new_tree = []
        for item in tree:
            item = replace_key_name(item, 'childs', 'children')
            new_tree.append(item)

        return Response(new_tree)

    def retrieve(self, request, pk=None, *args, **kwargs):
        salecategory = SaleCategory.objects.filter(cid=pk).first()
        if salecategory:
            serializer = serializers.SaleCategorySerializer(salecategory)
            return Response(serializer.data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        serializer = serializers.SaleCategorySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            cache.delete(SaleCategory.CACHE_KEY)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk, format=None):
        salecategory = SaleCategory.objects.filter(cid=pk).first()
        if salecategory:
            salecategory.delete()
            cache.delete(SaleCategory.CACHE_KEY)
            log_action(request.user, salecategory, DELETION, u'删除分类')
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, pk, format=None):
        salecategory = SaleCategory.objects.filter(cid=pk).first()
        if salecategory:
            serializer = serializers.SaleCategorySerializer(salecategory, data=request.data)
            if serializer.is_valid():
                serializer.save()
                cache.delete(SaleCategory.CACHE_KEY)
                log_action(request.user, salecategory, CHANGE, u'修改字段:%s' % ''.join(request.data.keys()))
                return Response(serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class SaleProductFilter(filters.FilterSet):
    id = ListFilter(name='id')
    status = ListFilter(name='status')
    sale_supplier = ListFilter(name='sale_supplier')
    min_price = django_filters.NumberFilter(name="price", lookup_type='gte')
    max_price = django_filters.NumberFilter(name="price", lookup_type='lte')

    class Meta:
        model = SaleProduct
        fields = ['id', 'sale_supplier', 'sale_category',
                  'sale_supplier__supplier_name', 'status',
                  'min_price', 'max_price']


class SaleProductViewSet(viewsets.ModelViewSet):
    """
    ### 排期管理商品REST API接口：
    - [/apis/chain/v1/saleproduct](/apis/chain/v1/saleproduct): 选品列表
        * method: get
        * method: post
        * method: patch
        * method: delete

    - [/apis/chain/v1/saleproduct/list_filters](/apis/chain/v1/saleproduct/list_filters): 列表过滤条件
        * method: get
        * return: {'status':[...], 'categorys':[...]}

    ### 抓取其他平台产品参数接口
    - [/apis/chain/v1/saleproduct/fetch_platform_product](/apis/chain/v1/supplier/fetch_platform_product?fetch_url=https%3A%2F%2Fitem.taobao.com%2Fitem.htm%3Fspm%3Da310p.7395725.1998460392.1.IxL35J%26id%3D531297154104)
        * method: get
        * args:
            1. `fetch_url`: 抓取的网址链接(urlquote)例如: 'https%3A%2F%2Fitem.taobao.com%2Fitem.htm%3Fspm%3Da310p.7395725.1998460392.1.IxL35J%26id%3D531297154104'
    """
    queryset = SaleProduct.objects.all().order_by('-created')
    serializer_class = serializers.SimpleSaleProductSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('created', 'modified', 'sale_time', 'remain_num', 'hot_value')
    filter_class = SaleProductFilter

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        categorys = SaleCategory.objects.filter(status=SaleCategory.NORMAL)
        return Response({
            'status': SaleProduct.STATUS_CHOICES,
            'categorys': categorys.values_list('id', 'name', 'parent_cid', 'is_parent', 'sort_order'),
            'platform': SaleSupplier.PLATFORM_CHOICE
        })

    @list_route(methods=['get'])
    def fetch_platform_product(self, request):
        supplier_id = request.GET.get('supplier_id') or 0
        fetch_url = request.GET.get('fetch_url', '').strip()
        if not fetch_url or not fetch_url.startswith(('http://', 'https://')):
            raise exceptions.APIException(u'请输入合法的URL')
        supplier = get_object_or_404(SaleSupplier, pk=int(supplier_id))
        tsoup, response = fetch_urls.getBeaSoupByCrawUrl(fetch_url)
        data = {
            'sale_supplier': supplier.id,
            'title': fetch_urls.getItemTitle(tsoup),
            'pic_url': fetch_urls.getItemPic(fetch_url, tsoup),
            'price': fetch_urls.getItemPrice(tsoup),
            'fetch_url': fetch_url,
            'sale_category': supplier.category.id if supplier.category else None,
            'supplier_sku': fetch_urls.supplier_sku(fetch_url, tsoup)
        }
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        model_product = instance.model_product
        if model_product:
            instance.title = model_product.name
            instance.sale_category = model_product.salecategory

        serializer = serializers.RetrieveSaleProductSerializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.exclude(status=SaleProduct.REJECTED)  # 排除淘汰的产品
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if request.user.has_perm('supplier.delete_sale_product'):
            instance = self.get_object()
            if instance.model_product:
                raise exceptions.APIException(u'已有资料禁止删除!')
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    def set_instance_special_fields(self, serializer):
        instance = self.queryset.filter(id=serializer.data.get('id')).first()
        instance.set_special_fields_by_skuextras()

    def create(self, request, *args, **kwargs):
        product_link = request.data.get('product_link')
        outer_id  = product_link and hashlib.md5(product_link).hexdigest() or 'OO%d' % time.time()
        request.data.update({
            'outer_id': outer_id,
            'contactor': request.user.id,
            'status': SaleProduct.PASSED
        })
        if product_link and str(product_link).strip() and self.queryset.filter(outer_id=outer_id).exists():
            raise exceptions.APIException(u'该款已经录入了[如果要录入多份，请在图片链接尾部加上标注如："#标注1"]!')
        salesupplier_id = request.data.get('sale_supplier')
        salesupplier  = SaleSupplier.objects.get(id=salesupplier_id)
        if not salesupplier.ware_by:
            raise exceptions.APIException(u'请先设置供应商所属仓库!')
        serializer = serializers.ModifySaleProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        self.set_instance_special_fields(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = serializers.ModifySaleProductSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.set_instance_special_fields(serializer)  # 设置价格等信息
        model_product = instance.model_product
        if model_product:  # 有款式
            model_product.update_fields_with_kwargs(**{
                'name': instance.title,
                'salecategory': instance.sale_category,
            })
            Product.create_or_update_skus(model_product, request.user)  # 保存saleproduct 之后才做更新

        serializer = serializers.RetrieveSaleProductSerializer(instance)
        return Response(serializer.data)


class SaleProductManageFilter(filters.FilterSet):
    sale_time_start = django_filters.DateFilter(name="sale_time", lookup_type='gte')
    sale_time_end = django_filters.DateFilter(name="sale_time", lookup_type='lte')
    suppliers_name = django_filters.CharFilter(name="sale_suppliers__supplier_name", lookup_type='contains')

    class Meta:
        model = SaleProductManage
        fields = ['sale_time_start', 'sale_time_end', 'schedule_type', 'sale_suppliers', 'suppliers_name']


class SaleScheduleViewSet(viewsets.ModelViewSet):
    """
    ###排期管理REST API接口：
    - schedule_type: (brand, 品牌),(atop, TOP榜),(topic, 专题),(sale, 特卖)
    - 列表过滤条件: schedule_type, sale_suppliers
    - /aggregate: 获取按日期聚合排期列表
    """
    queryset = SaleProductManage.objects.all()
    serializer_class = serializers.SimpleSaleProductManageSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,
                          permissions.IsAdminUser,
                          permissions.DjangoModelPermissions)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = SaleProductManageFilter
    # filter_fields = ('schedule_type', 'sale_suppliers')
    ordering_fields = ('sale_time', 'id', 'created', 'modified', 'product_num')

    @list_route(methods=['get'])
    def aggregate(self, request, *args, **kwargs):
        sale_date = request.GET.get('sale_date', '')
        if not sale_date:
            start_date = datetime.date.today() - datetime.timedelta(days=7)
            queryset = self.queryset.filter(sale_time__gte=start_date)
        else:
            sale_date = datetime.datetime.strftime(sale_date, '%Y-%m-%d').date()
            queryset = self.queryset.filter(sale_time=sale_date)

        schedule_values = queryset.values(
            'sale_time', 'id', 'schedule_type', 'product_num', 'lock_status')
        aggregate_data = {}
        for value in schedule_values:
            sdate = value['sale_time'].strftime("%Y-%m-%d")
            product_num = value['product_num']
            if sdate in aggregate_data:
                aggregate_data[sdate]['schedules'].append(value)
                aggregate_data[sdate]['product_sum'] += product_num
            else:
                aggregate_data[sdate] = {
                    'schedule_list': [value],
                    'schedule_date': sdate,
                    'product_sum': product_num
                }
        aggregate_list = sorted(aggregate_data.values(), key=lambda x: x['schedule_date'], reverse=True)
        return Response(aggregate_list)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.SaleProductManageSerializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        raise NotImplemented

    def create(self, request, *args, **kwargs):
        user = request.user
        request.data.update({"responsible_person_name": user.username, "responsible_people_id": user.id})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.order_by('-id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.SaleProductManageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        is_locked = instance.lock_status
        sale_supplier_ids = [supplier.id for supplier in instance.sale_suppliers.all()]  # 修改前供应商id
        sale_suppliers_id = request.data.get('sale_suppliers')
        is_deleted_sale_suppliers = set(sale_suppliers_id) < set(sale_supplier_ids)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        log_action(request.user, instance, CHANGE, u'修改字段:%s' % ''.join(request.data.keys()))
        self.perform_update(serializer)
        # 清理供应商下的产品
        if not is_locked and is_deleted_sale_suppliers:  # 非锁定状态　并且删除过供应商　予以清理排期明细
            if instance.clean_deleted_supplier_manager_details():
                log_action(request.user, instance, CHANGE, u'清理删除了的供应商的排期明细')
        return Response(serializer.data)


class SaleScheduleDetailFilter(filters.FilterSet):
    order_weight = django_filters.NumberFilter(name="order_weight")

    class Meta:
        model = SaleProductManageDetail
        fields = ['order_weight', "id", 'material_status', 'design_take_over', 'design_complete', 'is_promotion']


class SaleScheduleDetailViewSet(viewsets.ModelViewSet):
    """
    ### 排期管理商品REST API接口：
    - [/apis/chain/v1/saleschedule/186/product](/apis/chain/v1/saleschedule/186/product)
        * method: get
        * 可过滤字段:
            1. `sale_supplier`: 供应商 例如: 29491
            2. `min_price`: 区间最低价 例如: 0
            3. `max_price`: 区间最高价 例如: 50
            4. `sale_category`: 类别 例如: 1
            5. `id`: 排期明细id
        * 可排序字段：
            1. `order_weight` : 排序权重
            2. `is_promotion` : 是否推广
            3. `sale_category`: 类别
    - /apis/chain/v1/saleschedule/**schedule_id**/product/<schedule_detail_id>:
      method: delete (授权用户可以删除)
    - /apis/chain/v1/saleschedule/**schedule_id**/adjust_order_weight/<schedule_detail_id>:
      method: patch
      args:
        移动方向: `direction`
         plus: 向上
         minus: 向下　
         移动距离: `distance`
    - [/apis/chain/v1/saleschedule/**schedule_id**/update_assign_worker]() 分配任务;
        * method: post
        * args:
            1. `manager_detail_ids`: 排期明细的id  例如: [8772, 8773, 8774],
            2. `reference_user`: 资料人的id　例如: 1,
            3. `photo_user`: 平面制作人的id 例如: 1
        * return:
            1. 没有权限: {"detail": "You do not have permission to perform this action."}
            2. 请求成功: http status = 206
    - [/apis/chain/v1/saleschedule/**schedule_id**/product/list_filters](/apis/chain/v1/saleschedule/**schedule_id**/product/list_filters) 过滤参数列表;
        * method: get
    - [/apis/chain/v1/saleschedule/**schedule_id**/modify_manage_detail/**detailid**](/apis/chain/v1/saleschedule/186/modify_manage_detail/**detailid**)
        * method: patch
        * args:
            1. `material_status`: 'complete'    : complete: 资料完成,
            2. `design_complete`: 1 : 平面资料完成
    """
    queryset = SaleProductManageDetail.objects.all()
    serializer_class = serializers.SaleProductManageDetailSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    ordering_fields = ('order_weight', 'is_promotion', 'sale_category','id')
    filter_class = SaleScheduleDetailFilter

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        return Response({
            'material_status': SaleProductManageDetail.MATERIAL_STATUS,
            'design_take_over': SaleProductManageDetail.DESIGN_TAKE_STATUS,
            'design_complete': [{0: "未完成", 1: "已经完成"}],
        })

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        sale_product_ids = list(queryset.values_list('sale_product_id', flat=True))

        sakeproducts = SaleProduct.objects.filter(id__in=sale_product_ids)
        for bk in list(SaleProductViewSet.filter_backends):
            sakeproducts = bk().filter_queryset(self.request, sakeproducts, SaleProductViewSet)
        p_ids = list(sakeproducts.values_list('id', flat=True))
        return queryset.filter(sale_product_id__in=p_ids)

    def list(self, request, schedule_id=None, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if schedule_id:
            queryset = queryset.filter(schedule_manage_id=schedule_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any)
        if request.user.has_perm('supplier.delete_schedule_detail'):
            instance = self.get_object()
            res = instance.get_status_salenum_in_schedule()  # 排期内有订单
            if res:
                raise exceptions.APIException(u'排期内有销量禁止删除!')
            delete_order_weight = instance.order_weight
            model_pro = instance.modelproducts.first()
            manager = instance.schedule_manage
            self.perform_destroy(instance)
            if model_pro and model_pro.onshelf_time == instance.schedule_manage.upshelf_time:
                model_pro.reset_shelf_info()  # 删除明细后需要设置款式下架，　上下架时间设置为none
            manager.save(update_fields=['product_num'])
            # 删除之后　要给　大于delete_order_weight 减去1　方便后面排序接口
            schedule_details = manager.manage_schedule.filter(order_weight__gt=delete_order_weight)
            for schedule_detail in schedule_details:
                schedule_detail.order_weight -= 1
                schedule_detail.save(update_fields=['order_weight'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    @parser_classes(JSONParser)
    @transaction.atomic()
    def create_manage_detail(self, request, schedule_id, *args, **kwargs):
        sale_product_id = request.data.get('sale_product_id') or None
        sale_products = SaleProduct.objects.filter(id__in=sale_product_id)
        details = SaleProductManageDetail.objects.filter(schedule_manage_id=schedule_id,
                                                         today_use_status=SaleProductManageDetail.NORMAL)
        for sale_product in sale_products:
            order_weight = details.count() + 1
            modelproduct = sale_product.model_product
            request.data.update({
                "schedule_manage": schedule_id,
                "sale_product_id": sale_product.id,
                "name": sale_product.title,
                "today_use_status": SaleProductManageDetail.NORMAL,
                "pic_path": sale_product.pic_url,
                "product_link": sale_product.product_link,
                "sale_category": sale_product.sale_category.full_name,
                "order_weight": order_weight,
                "design_complete": True if modelproduct and modelproduct.head_imgs and modelproduct.content_imgs else False,
                "material_status": SaleProductManageDetail.COMPLETE if modelproduct else SaleProductManageDetail.WORKING,
            })
            serializer = serializers.SaleProductManageDetailSimpleSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        return Response(status=status.HTTP_201_CREATED)

    def modify_manage_detail(self, request, schedule_id, pk, *args, **kwargs):
        kwargs['partial'] = True
        partial = kwargs.pop('partial', False)
        instance = get_object_or_404(SaleProductManageDetail, id=pk)
        serializer = self.get_serializer(instance, data=request.data, partial=partial,
                                         context={'request': request})
        if 'design_complete' in request.data.keys() and str(request.data.get('design_complete')).strip():
            if instance.photo_user != request.user.id:
                raise exceptions.APIException(u'平面状态修改必须是平面制作人操作')
        if 'material_status' in request.data.keys() and str(request.data.get('material_status')).strip():
            if instance.reference_user != request.user.id:
                raise exceptions.APIException(u'资料录入状态必须是资料录入人操作')
        serializer.is_valid(raise_exception=True)
        log_action(request.user, instance, CHANGE, u'修改字段:%s' % ''.join(request.data.keys()))
        self.perform_update(serializer)
        return Response(serializer.data)

    def adjust_order_weight(self, request, schedule_id, pk, *args, **kwargs):
        """
        调整排序字段
        当前id : instance id
        移动方向: plus  minus
        移动距离: distance
        """
        direction = request.data.get('direction') or None
        distance = request.data.get('distance') or None
        instance = get_object_or_404(SaleProductManageDetail, id=pk)
        if not (direction and distance):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(schedule_manage=instance.schedule_manage,
                                        today_use_status=SaleProductManageDetail.NORMAL).order_by('order_weight')
        if direction == 'plus':  # 变大
            heiger_details = queryset.filter(order_weight__gt=instance.order_weight)
            if heiger_details.count() <= 0:
                raise exceptions.APIException(u'已经最大了')
            # 当前order_weight 和　目标order_weight 之间的　instance 需要变化
            zone_details = heiger_details.filter(order_weight__lte=instance.order_weight + int(distance))
            abs_distance = zone_details.count()
            for detail in zone_details:
                detail.order_weight -= 1
                detail.save(update_fields=['order_weight'])
            instance.order_weight = instance.order_weight + abs_distance
            instance.save(update_fields=['order_weight'])

        elif direction == 'minus':  # 变小
            lower_details = queryset.filter(order_weight__lt=instance.order_weight)
            if lower_details.count() <= 0:
                raise exceptions.APIException(u'已经最小了')
            zone_details = lower_details.filter(order_weight__gte=instance.order_weight - int(distance))
            abs_distance = zone_details.count()
            for detail in zone_details:
                detail.order_weight += 1
                detail.save(update_fields=['order_weight'])
            instance.order_weight = instance.order_weight - abs_distance
            instance.save(update_fields=['order_weight'])
        return Response(status=status.HTTP_200_OK)

    @parser_classes(JSONParser)
    @transaction.atomic()
    def update_assign_worker(self, request, *args, **kwargs):
        if not request.user.has_perm('supplier.distribute_schedule_detail'):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        manager_detail_ids = request.data.get('manager_detail_ids') or []
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(id__in=manager_detail_ids)
        partial = kwargs.pop('partial', True)
        for q in queryset:
            serializer = serializers.ManageDetailAssignWorkerSerializer(q, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            log_action(request.user, q, CHANGE, u'修改字段:%s' % ''.join(request.data.keys()))
        return Response(status=status.HTTP_206_PARTIAL_CONTENT)


class PreferencePoolFilter(filters.FilterSet):
    category = django_filters.CharFilter(name="categorys", lookup_type='contains')

    class Meta:
        model = PreferencePool
        fields = ["id", "category", 'is_sku']


class PreferencePoolViewSet(viewsets.ModelViewSet):
    """
    ### 资料参数池 API接口：
    - [/apis/chain/v1/preferencepool](/apis/chain/v1/preferencepool) 参数池列表:
        * method: get
    - [/apis/chain/v1/preferencepool?configed_category=63](/apis/chain/v1/preferencepool?configed_category=63) 指定配置过的参数列表:
        * method: get
    """
    queryset = PreferencePool.objects.all()
    serializer_class = serializers.PreferencePoolSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    ordering_fields = ('id', )
    filter_class = PreferencePoolFilter

    def list(self, request, *args, **kwargs):
        configed_category = request.GET.get('configed_category') or 0
        queryset = self.filter_queryset(self.get_queryset())
        if configed_category:
            cfg_cat = CategoryPreference.objects.filter(category__id=configed_category, is_default=True).first()
            queryset = queryset.filter(id__in=cfg_cat.preferences) if cfg_cat else queryset
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
