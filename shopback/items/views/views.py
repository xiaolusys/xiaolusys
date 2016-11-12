# coding: utf-8

import re
import datetime
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseNotFound
from django.db.models import Q, Sum, F
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
# from djangorestframework.serializer import Serializer
# from djangorestframework.utils import as_tuple
# from djangorestframework import status
# from djangorestframework.response import Response,ErrorResponse
# from djangorestframework.mixins import CreateModelMixin

from shopback import paramconfig as pcfg
# from core.options.views import ModelView,ListOrCreateModelView,ListModelView
from shopback.items.models import (Item,
                                   SkuProperty,
                                   Product,
                                   ProductSku,
                                   ProductLocation,
                                   ProductDaySale,
                                   ProductScanStorage)
from shopback.archives.models import DepositeDistrict
from shopback.users.models import User
from shopback.items.tasks import updateUserItemsTask, updateItemNum
from shopback.base.authentication import login_required_ajax
from shopapp.taobao import apis
from common.utils import update_model_fields, parse_date, format_date
from core.options import log_action, ADDITION, CHANGE
from django.views.generic import View
# 2015-7-27
from rest_framework import authentication
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import exceptions
from rest_framework.compat import OrderedDict
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework import authentication
from shopback.items import serializers
from rest_framework import status
from shopback.base.new_renders import new_BaseJSONRenderer
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
from shopback.items.models import SkuStock
from shopback.items import serializers
from shopback.items.renderers import *
from supplychain.supplier.models import SaleSupplier
###########7-27
import logging

DISTRICT_REGEX = '^(?P<pno>[a-zA-Z0-9=]+)-(?P<dno>[a-zA-Z0-9]+)?$'
ASSRIGN_PARAMS_REGEX = '^(?P<num_iid>[0-9]+)-(?P<sku_id>[0-9]+)?$'
logger = logging.getLogger('django.request')


@staff_member_required
def update_user_items(request):
    content = request.REQUEST
    user_id = content.get('user_id') or request.user.get_profile().visitor_id

    update_nums = updateUserItemsTask(user_id)

    response = {'update_nums': update_nums}

    return HttpResponse(json.dumps(response), content_type='application/json')


@csrf_exempt
@login_required_ajax
def update_product_stock(request):
    content = request.REQUEST
    outer_id = content.get('outer_id')
    product_id = content.get('product_id')
    sku_id = content.get('sku_id')
    outer_sku_id = content.get('outer_sku_id')
    num = content.get('num')
    remain_num = content.get('remain_num', '')
    reduce_num = content.get('reduce_num', 0)
    mode = content.get('mode', 0)  # 0增量，1全量
    if not request.user.has_perm('items.change_product_skunum'):
        return HttpResponse(json.dumps({'code': 2, 'response_error': u'权限不足'})
                            , content_type='application/json')

    if not num:
        return HttpResponse(json.dumps({'code': 1, 'response_error': u'库存数量不能为空'})
                            , content_type='application/json')

    prod = None
    prod_sku = None
    num, mode, reduce_num = int(num), int(mode), int(reduce_num)
    try:
        try:
            prod = Product.objects.get(id=product_id)
        except:
            prod = Product.objects.get(outer_id=outer_id)

        if sku_id or outer_sku_id:
            if sku_id:
                prod_sku = ProductSku.objects.get(id=sku_id)
            else:
                prod_sku = ProductSku.objects.get(product__outer_id=outer_id, outer_id=outer_sku_id)

            prod_sku.update_quantity(num, full_update=mode, dec_update=False)
            prod_sku.update_reduce_num(reduce_num, full_update=mode, dec_update=False)
            prod = prod_sku.product

        else:
            prod.update_collect_num(num, full_update=mode)
            prod.update_reduce_num(reduce_num, full_update=mode, dec_update=False)

        if remain_num:
            if prod_sku:
                prod_sku.remain_num = int(remain_num)
            else:
                prod.remain_num = int(remain_num)
            update_model_fields(prod_sku or prod, update_fields=['remain_num'])
    except Product.DoesNotExist:
        response = {'code': 1, 'response_error': u'商品未找到'}
        return HttpResponse(json.dumps(response), content_type='application/json')
    except ProductSku.DoesNotExist:
        response = {'code': 1, 'response_error': u'商品规格未找到'}
        return HttpResponse(json.dumps(response), content_type='application/json')
    except Exception, exc:
        response = {'code': 1, 'response_error': exc.message}
        return HttpResponse(json.dumps(response), content_type='application/json')

    log_action(request.user.id, prod, CHANGE, u'更新商品库存,%s，编码%s-%s,库存数%d,预留数%s,预减数%d' %
               (mode and u'全量' or u'增量', prod.outer_id,
                prod_sku and prod_sku.outer_id or sku_id, num, remain_num or '-', reduce_num))

    response = {
        'id': prod.id,
        'outer_id': prod.outer_id,
        'collect_num': prod.collect_num,
        'remain_num': prod.remain_num,
        'is_stock_warn': prod.is_stock_warn,
        'is_warning': prod.is_warning,
    }
    if prod_sku:
        quantity = prod_sku.quantity
        response['sku'] = {
            'id': prod_sku.id,
            'outer_id': prod_sku.outer_id,
            'quantity': prod_sku.quantity,
            'remain_num': prod_sku.remain_num,
            'is_stock_warn': prod_sku.is_stock_warn,
            'is_warning': prod_sku.is_warning,
        }
    response = {'code': 0, 'response_content': response}
    return HttpResponse(json.dumps(response), content_type='application/json')


#######################################################################################33
@staff_member_required
def update_user_item(request):
    content = request.REQUEST
    user_id = content.get('user_id')
    num_iid = content.get('num_iid')

    try:
        profile = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist:
        return HttpResponse(json.dumps({'code': 0, 'error_reponse': 'user_id is not correct'}))

    try:
        Item.objects.get(num_iid=None)
    except Item.DoesNotExist:
        try:
            response = apis.taobao_item_get(num_iid=num_iid, tb_user_id=profile.visitor_id)
            item_dict = response['item_get_response']['item']
            item = Item.save_item_through_dict(user_id, item_dict)

        except Exception, e:
            return HttpResponse(json.dumps({'code': 0, 'error_reponse': 'update item fail.'}))

    # item_dict = {'code':1,'reponse':Serializer().serialize(item)}#  fang 2015-7-28
    item_dict = {'code': 1, 'reponse': serializers.ItemSerializer(item).data}
    return HttpResponse(json.dumps(item_dict, cls=DjangoJSONEncoder))


##fang
from rest_framework import viewsets
import math


# fang
class ProductListView(viewsets.ModelViewSet):
    """ docstring for ProductListView """
    queryset = None
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductListHtmlRenderer, JSONRenderer, BrowsableAPIRenderer,)

    def list(self, request, *args, **kwargs):
        # 获取库存商品列表
        # model = self.resource.model
        print "get"
        model = Product
        queryset = self.get_queryset() if self.get_queryset() is not None else model.objects.all()

        if hasattr(self, 'resource'):
            ordering = getattr(self.resource, 'ordering', None)
        else:
            ordering = None

        kwargs.update({'status': pcfg.NORMAL})

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)
        queryset = queryset.filter(**kwargs)
        # 得到页数，每页10
        print len(queryset), "88"
        page = int(math.ceil(len(queryset) / 10.0))
        print page, "页数"
        # queryset =serializers.ProductSerializer( queryset.filter(**kwargs),many=True).data
        ##fang
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        # a=page
        # serializer.data.update("page",page)
        # a['data']=serializer.data
        # a['b']=page1
        # print serializer,"99999"
        return Response(serializer.data)

    def get_queryset(self):
        return self.queryset


class ProductItemView(APIView):  # ListModelView
    """ docstring for ProductItemView """
    queryset = None
    serializer_class = serializers.ProductItemSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductItemHtmlRenderer, JSONRenderer, BrowsableAPIRenderer,)

    # template_name = "fullcalendar/default.html"
    def get(self, request, *args, **kwargs):
        # 获取某outer_id对应的商品，以及同步商品库存
        print Item.objects.all()[0].outer_id
        outer_id = kwargs.get('outer_id', '')
        sync_stock = request.REQUEST.get('sync_stock', 'no')
        # model = self.resource.model
        model = Item
        update_time = datetime.datetime.now()
        if sync_stock == 'yes':
            items = model.objects.filter(outer_id=outer_id, approve_status=pcfg.ONSALE_STATUS)
            for item in items:
                updateItemNum(item.num_iid, update_time)

        queryset = self.get_queryset() if self.get_queryset() is not None else model.objects.all()

        if hasattr(self, 'resource'):
            ordering = getattr(self.resource, 'ordering', None)
        else:
            ordering = None

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)

        item_dict = {}
        items = queryset.filter(**kwargs)
        # item_dict['itemobjs'] =  Serializer().serialize(items)
        item_dict['itemobjs'] = serializers.ItemSerializer(items, many=True).datas
        item_dict['layer_table'] = render_to_string('items/itemstable.html',
                                                    {'object': item_dict['itemobjs']})

        return Response({"object": item_dict})

    def post(self, request, *args, **kwargs):
        # 删除product或productsku
        outer_id = kwargs.get('outer_id')
        outer_sku_id = request.REQUEST.get('outer_sku_id', None)

        if outer_sku_id:
            row = ProductSku.objects.filter(product=outer_id,
                                            outer_id=outer_sku_id).update(status=pcfg.DELETE)
        else:
            row = Product.objects.filter(outer_id=outer_id).update(status=pcfg.DELETE)

        return Response({'updates_num': row})

    def get_queryset(self):
        return self.queryset


class ProductModifyView(APIView):
    """ docstring for ProductListView """
    serializer_class = serializers.ProductItemSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, *args, **kwargs):
        # 取消库存警告
        outer_id = kwargs.get('outer_id')
        outer_sku_id = request.REQUEST.get('outer_sku_id', None)
        if outer_sku_id:
            row = ProductSku.objects.filter(product=outer_id,
                                            outer_id=outer_sku_id).update(is_assign=True)
        else:
            row = Product.objects.filter(outer_id=outer_id).update(is_assign=True)

        return Response({'updates_num': row})


class ProductUpdateView(APIView):
    """ docstring for ProductListView """
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductUpdateHtmlRenderer, JSONRenderer, BrowsableAPIRenderer,)

    def get(self, request, *args, **kwargs):

        outer_id = kwargs.get('outer_id', 'None')
        try:
            instance = Product.objects.get(outer_id=outer_id)
        except:
            return HttpResponseNotFound(u'商品未找到')

        ins_dict = instance.json

        return Response({'object': ins_dict})

    def post(self, request, *args, **kwargs):
        # 修改库存商品信息

        return Response(0)

        #  fang 2015-7-26 没有引用到就删掉了


# class ProductSkuCreateView(ModelView):
#     """ docstring for ProductSkuCreateView """
#
#     def get(self, request, *args, **kwargs):
#
#         prod_sku_id = request.REQUEST.get('prod_sku_id',None)
#         try:
#             instance = ProductSku.objects.get(id=prod_sku_id)
#         except:
#             raise Http404
#
#         return instance
#
#
#     def post(self, request, *args, **kwargs):
#         #创建库存产品属性信息
#
#
#         return 0


class ProductSkuInstanceView(APIView):
    """ docstring for ProductSkuInstanceView """
    serializer_class = serializers.ProductSkuSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductSkuHtmlRenderer, JSONRenderer, BrowsableAPIRenderer,)

    def get(self, request, sku_id, *args, **kwargs):

        try:
            instance = ProductSku.objects.get(id=sku_id)
        except:
            # raise ErrorResponse(status.HTTP_404_NOT_FOUND)
            raise Http404
        # product_sku = self._resource.filter_response(instance)
        product_sku = serializers.ProductSkuSerializer(instance).data
        product_sku['layer_table'] = render_to_string('items/productskutable.html',
                                                      {'object': instance})

        return Response({"object": product_sku})

    def post(self, request, *args, **kwargs):
        # 修改库存商品信息

        return Response(0)


############################ 库存商品操作 ###############################
from shopback.categorys.models import ProductCategory


class ProductView(APIView):
    """ docstring for ProductView """

    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductHtmlRenderer, new_BaseJSONRenderer, BrowsableAPIRenderer,)

    def get(self, request, id, *args, **kwargs):
        product = Product.objects.get(id=id)
        prod_serializer = serializers.ProductSerializer(product).data
        prod_serializer['skus'] = serializers.ProductSkuSerializer(product.pskus, many=True).data
        return Response(prod_serializer)  # 这个也能实现2015-7-27
        # return  Response({'object':serializers.ProductSerializer(product).data})

    def post(self, request, id, *args, **kwargs):
        try:
            product = Product.objects.get(id=id)
            content = request.REQUEST
            update_fields = []
            fields = ['outer_id', 'barcode', 'name', 'category', 'remain_num', 'weight', 'cost', 'ware_by',
                      'std_purchase_price', 'std_sale_price', 'agent_price', 'staff_price', 'is_split',
                      'sync_stock', 'post_check', 'is_match', 'match_reason', 'buyer_prompt', 'memo', 'storage_charger']
            check_fields = set(['is_split', 'sync_stock'])
            if not product.prod_skus.count() > 0:
                check_fields.update(['post_check', 'is_match'])
            for k, v in content.iteritems():
                if k not in fields: continue
                if k in check_fields:
                    v = (True, False)[v == '' and 1 or 0]
                if k in ('wait_post_num', 'remain_num'):
                    v = int(v)
                if hasattr(product, k) and getattr(product, k) != v:
                    if k == 'category':
                        cate = ProductCategory.objects.get(cid=v)
                        pu = Product.objects.filter(id=product.id)
                        pu.update(category=cate)
                        continue
                    setattr(product, k, v)
                    update_fields.append(k)
            update_model_fields(product, update_fields=update_fields)
        except Product.DoesNotExist:
            return Response(u'商品未找到')
        except Exception, exc:
            raise exceptions.APIException(u'填写信息不规则:%s' % exc.message)
        update_field_labels = []
        for field in update_fields:
            update_field_labels.append(
                '%s:%s' % (Product._meta.get_field(field).verbose_name.title(), getattr(product, field)))
        log_action(request.user.id, product, CHANGE, u'更新[%s]信息' % (','.join(update_field_labels)))
        prod_serializer = serializers.ProductSerializer(product).data
        prod_serializer['skus'] = serializers.ProductSkuSerializer(product.pskus, many=True).data
        return Response(prod_serializer)


class ProductSkuView(APIView):
    """ docstring for ProductSkuView """
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)

    def get(self, request, pid, sku_id, *args, **kwargs):

        try:
            instance = ProductSku.objects.get(id=sku_id)
        except:
            # raise ErrorResponse(status.HTTP_404_NOT_FOUND)
            raise Http404
        # product_sku = self._resource.filter_response(instance)
        product_sku = serializers.ProductSkuSerializer(instance).data
        # print
        # print type(product_sku),product_sku
        product_sku['layer_table'] = render_to_string('items/productskutable.html', {'object': instance})

        return Response(product_sku)

    def post(self, request, pid, sku_id, *args, **kwargs):
        # 修改库存商品信息
        try:
            product_sku = ProductSku.objects.get(product=pid, id=sku_id)
            content = request.REQUEST
            update_check = content.get('update_check')
            update_fields = []
            fields = ['outer_id', 'properties_alias', 'wait_post_num', 'remain_num', 'warn_num'
                , 'cost', 'std_sale_price', 'agent_price', 'staff_price', 'match_reason'
                , 'barcode', 'buyer_prompt', 'memo']
            check_fields = set(['sync_stock', 'post_check', 'is_match'])
            if update_check:
                fields.extend(list(check_fields))

            for k, v in content.iteritems():
                if k not in fields:
                    continue
                if k in check_fields:
                    check_fields.remove(k)
                if k in ('cost', 'std_sale_price', 'agent_price', 'staff_price'):
                    v = float(v)
                if k in ('wait_post_num', 'remain_num', 'warn_num'):
                    v = int(v)
                if v == getattr(product_sku, k):
                    continue
                setattr(product_sku, k, v)
                update_fields.append(k)

            if update_check:
                for k in check_fields:
                    setattr(product_sku, k, False)
                    update_fields.append(k)
            product_sku.save()
        except ProductSku.DoesNotExist:
            return Response('未找到商品属性')
        except Exception, exc:
            return Response(u'填写信息不规则')
        update_field_labels = []
        for field in update_fields:
            update_field_labels.append(
                '%s:%s' % (ProductSku._meta.get_field(field).verbose_name.title(), getattr(product_sku, field)))
        product = product_sku.product
        log_action(request.user.id, product, CHANGE,
                   u'更新规格(%s,%s)信息' % (unicode(product_sku), ','.join(update_field_labels)))

        return Response(product_sku.json)


class ProductSearchView(APIView):
    """ 根据商品编码，名称查询商品 """
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer, BrowsableAPIRenderer)

    @classmethod
    def get_skus_by_outer_id(cls, outer_id):
        product = Product.objects.filter(outer_id=outer_id).first()
        if not product:
            return Response({'code': 1, 'msg': '商品不存在'})
        skus = []
        for sku in product.prod_skus.filter(status=ProductSku.NORMAL).order_by('id'):
            skus.append({
                'id': sku.id,
                'properties_name': sku.properties_name or sku.properties_alias
            })
        product_dict = {
            'id': product.id,
            'name': product.name,
            'outer_id': product.outer_id,
            'pic_path': product.pic_path,
            'skus': skus
        }
        return Response({'product': product_dict, 'code': 0})

    def get(self, request, *args, **kwargs):
        # print Product.objects.all()[1].outer_id
        outer_id = request.GET.get('outer_id')
        if outer_id:
            return self.get_skus_by_outer_id(outer_id)

        q = request.GET.get('q')
        # print q,"000"
        if not q:
            return Response('没有输入查询关键字'.decode('utf8'))
        products = Product.objects.filter(Q(outer_id=q) | Q(name__contains=q), status__in=(pcfg.NORMAL, pcfg.REMAIN))

        prod_list = [(prod.outer_id,
                      prod.pic_path,
                      prod.name,
                      prod.cost,
                      prod.collect_num,
                      prod.created,
                      [(sku.outer_id, sku.name, sku.quantity)
                       for sku in prod.pskus.order_by('-created')])
                     for prod in products]

        return Response(prod_list)

    def post(self, request, *args, **kwargs):
        # 修改库存商品信息

        return Response(0)


class ProductBarCodeView(APIView):
    """ docstring for ProductBarCodeView """

    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductBarcodeHtmlRenderer, new_BaseJSONRenderer,)

    def get(self, request, *args, **kwargs):
        # 获取库存商品列表
        print     Product.objects.all()[0].outer_id
        content = request.REQUEST
        outer_id = content.get('outer_id', '')

        products = Product.objects.getProductByBarcode(outer_id)

        product_json = [p.json for p in products]

        return Response({'products': product_json, 'outer_id': outer_id})

    def post(self, request, *args, **kwargs):

        content = request.REQUEST
        outer_id = content.get('outer_id') or None
        outer_sku_id = content.get('outer_sku_id')
        barcode = content.get('barcode') or ''

        product = None
        product_sku = None
        try:
            product = Product.objects.get(outer_id=outer_id)
            if outer_sku_id:
                product_sku = ProductSku.objects.get(outer_id=outer_sku_id, product=product)

                product_sku.barcode = barcode.strip()
                product_sku.save()
            else:
                product.barcode = barcode.strip()
                product.save()
        except Product.DoesNotExist:
            return Response(u'未找到商品')
        except ProductSku.DoesNotExist:
            return Response(u'未找到商品规格')
        except Exception, exc:
            return Response(exc.message)

        log_action(request.user.id, product, CHANGE, u'更新商品条码:(%s-%s,%s)'
                   % (outer_id or '', outer_sku_id or '', barcode))
        # product_sku=ProductSku.objects.all()[0]  fang add  ceshi
        # print product_sku
        return Response({'barcode': product_sku and product_sku.BARCODE or product.BARCODE})


############################################ 产品区位操作 #######################################
class ProductDistrictView(APIView):
    """ 根据商品编码，名称查询商品
        TODO@hy　设计不清，重构中 参见ProductLocationViewSet
    """
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductDistrictHtmlRenderer, new_BaseJSONRenderer,)

    def get(self, request, id, *args, **kwargs):

        content = request.REQUEST
        try:
            product = Product.objects.get(id=id)
        except:
            return Response(u'商品未找到')

        product_district = product.get_districts_code() or u'--'

        return Response({'product': product.json, 'product_districts': product_district})

    def post(self, request, id, *args, **kwargs):
        #         print "post"
        content = request.REQUEST
        outer_id = content.get('outer_id') or None
        outer_sku_id = content.get('outer_sku_id') or None
        district = content.get('district')
        r = re.compile(DISTRICT_REGEX)
        m = r.match(district)
        if not m:
            return Response(u'标签不合规则')

        tag_dict = m.groupdict()
        pno = tag_dict.get('pno')
        dno = tag_dict.get('dno')
        deposit_obj = DepositeDistrict.objects.get(parent_no=pno or '', district_no=dno or '')
        district_obj = serializers.DepositeDistrictSerializer(deposit_obj).data

        product = Product.objects.get(outer_id=outer_id)
        prod_sku = None
        if outer_sku_id:
            prod_sku = ProductSku.objects.get(outer_id=outer_sku_id, product=product)

        location, state = ProductLocation.objects.get_or_create(
            product_id=product.id, sku_id=prod_sku and prod_sku.id, district=deposit_obj)

        log_action(request.user.id, product, CHANGE, u'更新商品库位:(%s-%s,%s)'
                   % (outer_id or '', outer_sku_id or '', district))

        return Response({'outer_id': location.outer_id,
                         'outer_sku_id': location.outer_sku_id,
                         'district': district_obj})


@csrf_exempt
@login_required_ajax
def delete_product_district(request):
    content = request.REQUEST
    outer_id = content.get('outer_id') or None
    outer_sku_id = content.get('outer_sku_id') or None
    district = content.get('district')

    r = re.compile(DISTRICT_REGEX)
    m = r.match(district)
    if not m:
        ret = {'code': 1, 'error_response': u'标签不合规则'}
        return HttpResponse(json.dumps(ret), content_type="application/json")

    tag_dict = m.groupdict()
    pno = tag_dict.get('pno')
    dno = tag_dict.get('dno')
    district = DepositeDistrict.objects.get(parent_no=pno or '', district_no=dno or '')

    try:
        product = Product.objects.get(outer_id=outer_id)
        prod_sku = None
        if outer_sku_id:
            prod_sku = ProductSku.objects.get(outer_id=outer_sku_id, product=product)

        location = ProductLocation.objects.get(
            product_id=product.id, sku_id=prod_sku and prod_sku.id, district=district)
        location.delete()
    except Exception, exc:
        logger.error(exc.message, exc_info=True)
        ret = {'code': 1, 'error_response': u'未找到删除项'}
        return HttpResponse(json.dumps(ret), content_type="application/json")

    log_action(request.user.id, Product.objects.get(outer_id=outer_id), CHANGE,
               u'删除商品库位:(%s-%s,%s)' % (outer_id or '', outer_sku_id or '', district))

    ret = {'code': 0, 'response_content': 'success'}
    return HttpResponse(json.dumps(ret), content_type="application/json")


@csrf_exempt
@login_required_ajax
def deposite_district_query(request):
    content = request.REQUEST
    q = content.get('term')
    if not q:
        ret = {'code': 1, 'error_response': u'查询内容不能为空'}
        return HttpResponse(json.dumps(ret), content_type="application/json")

    districts = DepositeDistrict.objects.filter(parent_no__istartswith=q)

    ret = [{'id': str(d), 'value': str(d)} for d in districts]

    return HttpResponse(json.dumps(ret), content_type="application/json")


##################################### 警告库存商品规格管理 ##################################

class ProductOrSkuStatusMdView(APIView):
    """ 库存警告商品管理 """
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer,)

    def post(self, request, *args, **kwargs):

        content = request.REQUEST
        outer_id = content.get('outer_id')
        outer_sku_id = content.get('outer_sku_id')
        product_id = content.get('product_id')
        sku_id = content.get('sku_id')
        is_delete = content.get('is_delete') == 'true'
        is_remain = content.get('is_remain') == 'true'

        status = (is_delete and pcfg.DELETE) or (is_remain and pcfg.REMAIN) or pcfg.NORMAL

        queryset = ProductSku.objects.all()
        if product_id:
            queryset = queryset.filter(product__id=product_id)
        else:
            queryset = queryset.filter(product__outer_id=outer_id)

        if sku_id:
            queryset = queryset.filter(id=sku_id)

        if outer_sku_id:
            queryset = queryset.filter(outer_id=outer_sku_id)

        row = queryset.update(status=status)

        log_action(request.user.id, queryset[0].product, CHANGE,
                   u'更改规格库存状态:%s,%s' % (outer_sku_id or sku_id,
                                        dict(Product.STATUS_CHOICES).get(status)))

        return Response({'updates_num': row})


class ProductWarnMgrView(APIView):
    """ 库存警告商品管理 """
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductWarnHtmlRenderer, new_BaseJSONRenderer)

    def get(self, request, *args, **kwargs):
        pskus = ProductSku.objects.filter(product__status=pcfg.NORMAL, status=pcfg.NORMAL, is_assign=False) \
            .extra(where=["(quantity<=shop_items_productsku.remain_num+shop_items_productsku.wait_post_num " +
                          "OR quantity<=shop_items_productsku.remain_num)"])
        pskus_new = serializers.ProductSkuSerializer(pskus, many=True).data
        return Response({"object": {'warn_skus': pskus_new}})

    def post(self, request, *args, **kwargs):
        pass
        return Response({"examle": "unused post"})


class ProductNumAssignView(APIView):
    """ docstring for ProductNumAssignView """
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (new_BaseJSONRenderer,)

    def get(self, request, *args, **kwargs):
        # 获取某outer_id对应的商品，以及同步商品库存
        content = request.REQUEST
        outer_id = content.get('outer_id')
        outer_sku_id = content.get('outer_sku_id')

        real_num = 0
        lday_num = 0
        product = Product.objects.get(outer_id=outer_id)
        product_sku = None
        if outer_sku_id:
            try:
                product_sku = ProductSku.objects.get(product__outer_id=outer_id,
                                                     outer_id=outer_sku_id)
            except:
                pass
            else:
                real_num = product_sku.quantity - product_sku.wait_post_num
                lday_num = product_sku.warn_num
        else:
            real_num = product.collect_num - product.wait_post_num
            lday_num = product.warn_num

        items_dict_list = []
        items = Item.objects.filter(outer_id=outer_id, status=True)
        for item in items:

            # item = Item.get_or_create(item.user.visitor_id,item.num_iid,force_update=True)
            item_dict = {}
            sku_dict = {}
            if outer_sku_id:
                try:
                    spty = SkuProperty.objects.get(num_iid=item.num_iid, outer_id=outer_sku_id, status=pcfg.NORMAL)
                except:
                    continue
                else:
                    sku_dict['sku_id'] = spty.sku_id
                    sku_dict['outer_id'] = spty.outer_id
                    sku_dict['properties_name'] = product_sku.properties_name
                    sku_dict['with_hold_quantity'] = spty.with_hold_quantity
                    sku_dict['quantity'] = spty.quantity

            item_dict['sku'] = sku_dict

            item_dict['num_iid'] = item.num_iid
            item_dict['outer_id'] = item.outer_id
            item_dict['seller_nick'] = item.user.nick
            item_dict['sync_stock'] = item.sync_stock and 1 or 0
            item_dict['approve_status'] = dict(Item.APPROVE_STATUS).get(item.approve_status, '')
            item_dict['with_hold_quantity'] = item.with_hold_quantity
            item_dict['has_showcase'] = item.has_showcase and 1 or 0
            item_dict['num'] = item.num
            item_dict['title'] = item.title
            item_dict['pic_url'] = item.pic_url
            item_dict['detail_url'] = item.detail_url

            items_dict_list.append(item_dict)

        assign_tpl_string = render_to_string('items/product_assign_warn.html',
                                             {
                                                 'items_list': items_dict_list,
                                                 'outer_id': outer_id,
                                                 'outer_sku_id': outer_sku_id,
                                                 'real_num': real_num,
                                                 'lday_num': lday_num
                                             })

        return Response({'id': product.id,
                         'outer_id': outer_id,
                         'name': product.name,
                         'barcode': product.barcode,
                         'is_match': product.is_match,
                         'sync_stock': product.sync_stock,
                         'is_assign': product.is_assign,
                         'post_check': product.post_check,
                         'buyer_prompt': product.buyer_prompt,
                         'memo': product.memo,
                         'match_reason': product.match_reason,
                         'sku': product_sku and product_sku.json or {},
                         'assign_template': assign_tpl_string
                         })

    def post(self, request, *args, **kwargs):
        # 删除product或productsku

        content = request.REQUEST
        outer_id = content.get('assign_outer_id')
        outer_sku_id = content.get('assign_outer_sku_id')
        try:
            item_list = self.parse_params(content)

            self.valid_params(item_list, outer_id, outer_sku_id)

            self.assign_num_action(item_list)
        except Exception, exc:
            logger.error(exc.message, exc_info=True)
            return Response(exc.message)

        product = Product.objects.get(outer_id=outer_id)

        if outer_sku_id:
            row = ProductSku.objects.filter(outer_id=outer_sku_id, product__outer_id=outer_id).update(is_assign=True)
        else:
            row = Product.objects.filter(outer_id=outer_id).update(is_assign=True)

        log_action(request.user.id, product, CHANGE, u'手动分配商品线上库存')

        return Response({'success': row})

    def parse_params(self, content):

        items_list = []
        try:
            r = re.compile(ASSRIGN_PARAMS_REGEX)

            for k, v in content.iteritems():
                m = r.match(k)
                if not m:
                    continue

                d = m.groupdict()
                items_list.append((d['num_iid'], d['sku_id'], int(v)))

        except:
            raise Exception('参数格式不对'.decode('utf8'))
        return items_list

    def valid_params(self, item_list, outer_id, outer_sku_id):

        product = None
        product_sku = None
        if outer_sku_id:
            product_sku = ProductSku.objects.get(product__outer_id=outer_id, outer_id=outer_sku_id)

        product = Product.objects.get(outer_id=outer_id)

        real_num = product_sku and product_sku.realnum or product.realnum
        assign_num = 0
        for item in item_list:
            if item[2] != 0 and item[1] and not product_sku:
                raise Exception('线上规格不在系统规格中'.decode('utf8'))
            assign_num += item[2]

        if assign_num > real_num:
            raise Exception('库存分配超出实际库存'.decode('utf8'))

    def assign_num_action(self, item_list):

        for item in item_list:

            im = Item.objects.get(num_iid=item[0])
            hold_num = im.with_hold_quantity

            sku = None
            if item[1]:
                sku = SkuProperty.objects.get(num_iid=item[0], sku_id=item[1])
                hold_num = sku.with_hold_quantity

            if item[2] < hold_num:
                raise Exception('分配库存小于线上拍下待付款数'.decode('utf8'))

            if im.user.isValid():
                apis.taobao_item_quantity_update \
                    (num_iid=item[0], quantity=item[2], sku_id=item[1], tb_user_id=im.user.visitor_id)

            if sku:
                sku.quantity = item[2]
                sku.save()
            else:
                im.num = item[2]
                im.save()


class StatProductSaleView(APIView):
    """ docstring for class StatisticsMergeOrderView """
    # serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductSaleHtmlRenderer, new_BaseJSONRenderer,)

    def parseDate(self, start_dt):

        if not start_dt:
            dt = datetime.datetime.now()
            return (dt - datetime.timedelta(days=1)).date()

        return parse_date(start_dt)

    def getProductByOuterId(self, outer_id):

        try:
            return Product.objects.get(outer_id=outer_id)
        except:
            return None

    def getSaleSortedItems(self, queryset):

        sale_items = {}
        for sale in queryset:
            product_id = sale.product_id
            sku_id = sale.sku_id

            if sale_items.has_key(product_id):
                sale_items[product_id]['sale_num'] += sale.sale_num
                sale_items[product_id]['sale_payment'] += sale.sale_payment
                sale_items[product_id]['sale_refund'] += sale.sale_refund
                sale_items[product_id]['confirm_num'] += sale.confirm_num
                sale_items[product_id]['confirm_payment'] += sale.confirm_payment

                if not sku_id: continue
                skus = sale_items[product_id]['skus']
                if skus.has_key(sku_id):
                    skus[sku_id]['sale_num'] += sale.sale_num
                    skus[sku_id]['sale_payment'] += sale.sale_payment
                    skus[sku_id]['sale_refund'] += sale.sale_refund
                    skus[sku_id]['confirm_num'] += sale.confirm_num
                    skus[sku_id]['confirm_payment'] += sale.confirm_payment
                else:
                    skus[sku_id] = {
                        'sale_num': sale.sale_num,
                        'sale_payment': sale.sale_payment,
                        'sale_refund': sale.sale_refund,
                        'confirm_num': sale.confirm_num,
                        'confirm_payment': sale.confirm_payment}
            else:
                product = Product.objects.get(id=product_id)
                pic_path = product.pic_path
                if pic_path.startswith('http://img02.taobaocdn'):
                    pic_path = pic_path.rstrip('_80x80.jpg') + '.jpg_80x80.jpg'
                sale_items[product_id] = {
                    'pic_path': pic_path,
                    'title': product.title,
                    'sale_num': sale.sale_num,
                    'sale_payment': sale.sale_payment,
                    'sale_refund': sale.sale_refund,
                    'confirm_num': sale.confirm_num,
                    'confirm_payment': sale.confirm_payment,
                    'skus': {}}
                if sku_id:
                    sale_items[product_id]['skus'][sku_id] = {
                        'sale_num': sale.sale_num,
                        'sale_payment': sale.sale_payment,
                        'sale_refund': sale.sale_refund,
                        'confirm_num': sale.confirm_num,
                        'confirm_payment': sale.confirm_payment,
                    }

        return sorted(sale_items.items(), key=lambda d: d[1]['sale_num'], reverse=True)

    def calcSaleSortedItems(self, queryset):

        total_stock_num = 0
        total_sale_num = 0
        total_sale_payment = 0
        total_confirm_num = 0
        total_confirm_payment = 0
        total_confirm_cost = 0
        total_sale_refund = 0
        total_stock_cost = 0
        sale_stat_list = self.getSaleSortedItems(queryset)

        for product_id, sale_stat in sale_stat_list:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue
            has_sku = sale_stat['skus'] and True or False
            sale_stat['name'] = product.name
            sale_stat['outer_id'] = product.outer_id
            sale_stat['confirm_cost'] = not has_sku and product.cost * sale_stat['confirm_num'] or 0
            sale_stat['collect_num'] = not has_sku and product.collect_num or 0
            sale_stat['stock_cost'] = not has_sku and product.cost * product.collect_num or 0

            for sku_id, sku_stat in sale_stat['skus'].iteritems():
                try:
                    sku = ProductSku.objects.get(id=sku_id)
                except ProductSku.DoesNotExist:
                    continue
                sku_stat['name'] = sku.name
                sku_stat['outer_id'] = sku.outer_id
                sku_stat['quantity'] = sku.quantity
                sku_stat['confirm_cost'] = sku.cost * sku_stat['confirm_num']
                sku_stat['stock_cost'] = sku.cost * sku.quantity
                sale_stat['confirm_cost'] += sku_stat['confirm_cost']
                sale_stat['collect_num'] += sku.quantity
                sale_stat['stock_cost'] += sku_stat['stock_cost']

            sale_stat['skus'] = sorted(sale_stat['skus'].items(),
                                       key=lambda d: d[1]['sale_num'],
                                       reverse=True)

            total_stock_num += sale_stat['collect_num']
            total_sale_num += sale_stat['sale_num']
            total_confirm_num += sale_stat['confirm_num']
            total_confirm_payment += sale_stat['confirm_payment']
            total_confirm_cost += sale_stat['confirm_cost']
            total_sale_payment += sale_stat['sale_payment']
            total_sale_refund += sale_stat['sale_refund']
            total_stock_cost += sale_stat['stock_cost']

        return {'sale_items': sale_stat_list,
                'total_confirm_cost': total_confirm_cost,
                'total_confirm_num': total_confirm_num,
                'total_confirm_payment': total_confirm_payment,
                'total_sale_num': total_sale_num,
                'total_sale_refund': total_sale_refund,
                'total_sale_payment': total_sale_payment,
                'total_stock_num': total_stock_num,
                'total_stock_cost': total_stock_cost}

    def calcUnSaleSortedItems(self, queryset, p_outer_id=None):

        total_stock_num = 0
        total_stock_cost = 0
        product_list = Product.objects.filter(status=pcfg.NORMAL)
        if p_outer_id:
            product_list = product_list.filter(outer_id__startswith=p_outer_id)

        ps_tuple = set(queryset.values_list('product_id', 'sku_id').distinct())
        productid_set = set(s[0] for s in ps_tuple)
        sale_items = {}
        for product in product_list:
            product_id = product.id

            if product.collect_num <= 0:
                continue

            for sku in product.pskus:
                sku_id = sku.id

                if (product_id, sku_id) in ps_tuple or sku.quantity <= 0:
                    continue

                if not sale_items.has_key(product_id):
                    sale_items[product_id] = {
                        'sale_num': 0,
                        'sale_payment': 0,
                        'sale_refund': 0,
                        'confirm_num': 0,
                        'confirm_payment': 0,
                        'confirm_cost': 0,
                        'name': product.name,
                        'outer_id': product.outer_id,
                        'sale_cost': 0,
                        'stock_cost': 0,
                        'collect_num': 0,
                        'skus': {}}

                sale_items[product_id]['skus'][sku_id] = {
                    'name': sku.name,
                    'outer_id': sku.outer_id,
                    'quantity': sku.quantity,
                    'sale_cost': 0,
                    'sale_num': 0,
                    'sale_payment': 0,
                    'sale_refund': 0,
                    'confirm_num': 0,
                    'confirm_payment': 0,
                    'confirm_cost': 0,
                    'stock_cost': sku.quantity * sku.cost
                }
                sale_items[product_id]['collect_num'] += sku.quantity
                sale_items[product_id]['stock_cost'] += sku.quantity * sku.cost

            if product_id not in productid_set and not sale_items.has_key(product_id):
                product = Product.objects.get(id=product_id)
                pic_path = product.pic_path
                if pic_path.startswith('http://img02.taobaocdn'):
                    pic_path = pic_path.rstrip('_80x80.jpg') + '.jpg_80x80.jpg'

                sale_items[product_id] = {'pic_path': pic_path,
                                          'title': product.title,
                                          'sale_num': 0,
                                          'sale_payment': 0,
                                          'sale_refund': 0,
                                          'confirm_num': 0,
                                          'confirm_payment': 0,
                                          'confirm_cost': 0,
                                          'name': product.name,
                                          'outer_id': product.outer_id,
                                          'collect_num': product.collect_num,
                                          'sale_cost': 0,
                                          'stock_cost': product.collect_num * product.cost,
                                          'skus': {}}

            if sale_items.has_key(product_id):
                sale_items[product_id]['skus'] = sorted(sale_items[product_id]['skus'].items(),
                                                        key=lambda d: d[1]['quantity'],
                                                        reverse=True)

                total_stock_num += sale_items[product_id]['collect_num']
                total_stock_cost += sale_items[product_id]['stock_cost']

        return {'sale_items': sorted(sale_items.items(),
                                     key=lambda d: d[1]['collect_num'],
                                     reverse=True),
                'total_confirm_cost': 0,
                'total_confirm_num': 0,
                'total_confirm_payment': 0,
                'total_sale_num': 0,
                'total_sale_refund': 0,
                'total_sale_payment': 0,
                'total_stock_num': total_stock_num,
                'total_stock_cost': total_stock_cost}

    def calcSaleItems(self, queryset, p_outer_id=None, show_sale=True):

        if show_sale:
            return self.calcSaleSortedItems(queryset)

        return self.calcUnSaleSortedItems(queryset, p_outer_id=p_outer_id)

    def get(self, request, *args, **kwargs):
        try:
            content = request.REQUEST
            start_dt = content.get('df', '').strip()
            end_dt = content.get('dt', '').strip()
            shop_id = content.get('shop_id')
            p_outer_id = content.get('outer_id', '')
            show_sale = not content.has_key('_unsaleable')
            sale_items = {}
            params = {'day_date__gte': self.parseDate(start_dt),
                      'day_date__lte': self.parseDate(end_dt)}
            if shop_id:
                params.update(user_id=shop_id)

            if p_outer_id:
                params.update(outer_id__startswith=p_outer_id)

            sale_qs = ProductDaySale.objects.filter(**params)
            sale_items = self.calcSaleItems(sale_qs, p_outer_id=p_outer_id, show_sale=show_sale)
            sale_items.update({
                'df': format_date(self.parseDate(start_dt)),
                'dt': format_date(self.parseDate(end_dt)),
                'outer_id': p_outer_id,
                'shops': serializers.UserSerializer(User.effect_users.all(), many=True).data,
                'shop_id': shop_id and int(shop_id) or '',
            })
        except Exception, exc:
            exc_msg = exc.message or 'calc sale product error'
            logger.error(exc_msg, exc_info=True)
            raise exceptions.APIException(exc_msg)
        return Response({'object': {'sale_stats': sale_items}})

    post = get


from shopback.items.tasks import CalcProductSaleAsyncTask


class StatProductSaleAsyncView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductSaleAsyncHtmlRenderer, new_BaseJSONRenderer,)

    def parseDate(self, start_dt):

        if not start_dt:
            dt = datetime.datetime.now()
            return (dt - datetime.timedelta(days=1)).date()

        return parse_date(start_dt)

    def get(self, request, *args, **kwargs):
        content = request.REQUEST
        start_dt = content.get('df', '').strip()
        end_dt = content.get('dt', '').strip()
        buyer_name = content.get('buyer_name', '').strip()
        supplier = content.get('supplier', '').strip()
        shop_id = content.get('shop_id')
        p_outer_id = content.get('outer_id', '')
        show_sale = '_unsaleable' not in content
        params = {'day_date__gte': self.parseDate(start_dt),
                  'day_date__lte': self.parseDate(end_dt)}
        if shop_id:
            params.update(user_id=shop_id)

        if p_outer_id:
            params.update(outer_id__startswith=p_outer_id)

        task_id = CalcProductSaleAsyncTask().delay(params, buyer_name=buyer_name, supplier=supplier,
                                                   p_outer_id=p_outer_id, show_sale=show_sale)
        sale_items = {
            'df': format_date(self.parseDate(start_dt)),
            'dt': format_date(self.parseDate(end_dt)),
            'outer_id': p_outer_id,
            'shops': serializers.UserSerializer(User.effect_users.all(), many=True).data,
            'shop_id': shop_id and int(shop_id) or '',
            'task_id': task_id,
            'buyer_name': buyer_name,
            'supplier': supplier
        }
        return Response(sale_items)


class ProductScanView(APIView):
    # serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    renderer_classes = (ProductScanRenderer, new_BaseJSONRenderer,)

    def get(self, request, *args, **kwargs):

        wave_no = datetime.datetime.now().strftime("%Y-%m-%d-%H")

        return Response({'wave_no': wave_no})

    def post(self, request, *args, **kwargs):

        content = request.REQUEST

        barcode = content.get('barcode')
        product_sku_list = Product.objects.getProductSkuByBarcode(barcode)
        if len(product_sku_list) == 0:
            product_list = Product.objects.getProductByBarcode(barcode)
            if len(product_list) == 0:
                return Response(u'条码未找到商品')

            if len(product_list) > 1:
                return Response(u'条码对应多件商品')

        if len(product_sku_list) > 1:
            return Response(u'条码对应多件商品')

        if len(product_sku_list) == 1:
            product_sku = product_sku_list[0]
            product = product_sku.product
        else:
            product_sku = None
            product = product_list[0]

        wave_no = content.get('wave_no')
        num = content.get('num')

        prod, state = ProductScanStorage.objects.get_or_create(wave_no=wave_no,
                                                               product_id=product.id,
                                                               sku_id=product_sku and product_sku.id or '')
        prod.product_name = product.name
        prod.sku_name = product_sku and product_sku.name or ''
        prod.qc_code = product.outer_id
        prod.sku_code = product_sku and product_sku.outer_id or ''
        prod.barcode = barcode
        prod.scan_num = F('scan_num') + int(num)
        prod.status = ProductScanStorage.WAIT
        prod.save()

        return Response({"object": {'product_id': prod.product_id,
                                    'product_name': prod.product_name,
                                    'sku_name': prod.sku_name,
                                    'scan_num': prod.scan_num,
                                    'location': product.get_districts_code(),
                                    'barcode': prod.barcode}})


#######  fang  2015-7-28
def as_tuple(obj):
    """
    Given an object which may be a list/tuple, another object, or None,
    return that object in list form.

    IE:
    If the object is already a list/tuple just return it.
    If the object is not None, return it in a list with a single element.
    If the object is None return an empty list.
    """
    if obj is None:
        return ()
    elif isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, tuple):
        return obj
    return (obj,)


class StockRedundanciesView(View):
    def get(self, request):
        s = ','.join([str(p) for p in SkuStock.redundancies()])
        return HttpResponseRedirect('/admin/items/skustock?id__in=%s' % s)


class ProductSkuStatsTmpView(View):
    def get(self, request):
        supplier_id = request.GET.get('supplier_id')
        supplier_name = request.GET.get('supplier_name')
        if supplier_id:
            supplier = get_object_or_404(SaleSupplier, pk=supplier_id)
        elif supplier_name:
            supplier = get_object_or_404(SaleSupplier, supplier_name=SaleSupplier)
        else:
            return HttpResponseRedirect('/admin/items/skustock')
        s = ','.join([str(p) for p in SkuStock.filter_by_supplier(supplier.id)])
        return HttpResponseRedirect('/admin/items/skustock?product_id__in=%s' % s)


class ProductSkuStatsViewSet(View):
    pass
