# coding:utf-8
import copy
import datetime
import json
from operator import itemgetter
import re
import sys
from django.db.models import F, Q, Sum, Count
from rest_framework import generics, permissions, renderers, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions
from core.options import log_action, ADDITION, CHANGE
from flashsale.dinghuo.models import (orderdraft, OrderDetail, OrderList,
                                      InBound, InBoundDetail,
                                      OrderDetailInBoundDetail)
from shopback.archives.models import DepositeDistrict
from shopback.items.models import Product, ProductCategory, ProductSku, ProductStock, ProductLocation
from supplychain.supplier.models import SaleProduct, SaleSupplier
from . import forms, functions, functions2view, models
from django.shortcuts import get_object_or_404
from django.shortcuts import HttpResponseRedirect


class InBoundViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = models.OrderList.objects.all()

    EXPRESS_NO_SPLIT_PATTERN = re.compile(r'\s+|,|，')
    DISTRICT_REGEX = re.compile(
        '^(?P<pno>[a-zA-Z0-9=]+)-(?P<dno>[a-zA-Z0-9]+)?$')

    WARE_HOUSES = [
        {'value': 0,
         'text': '未选仓'}, {'value': 1, 'text': '上海仓'}, {'value': 2, 'text': '广州仓'}
    ]

    @list_route(methods=['post'])
    def create_inbound(self, request):
        form = forms.CreateInBoundForm(request.POST)
        if not form.is_valid():
            return Response({'orderlists': []})

        inbound_skus = json.loads(form.cleaned_data['inbound_skus'])
        if not inbound_skus:
            return Response({'orderlists': []})
        inbound_skus_dict = {int(k): v for k, v in inbound_skus.iteritems()}
        for sku in ProductSku.objects.filter(id__in=inbound_skus_dict.keys()):
            inbound_skus_dict[sku.id]['product_id'] = sku.product_id
        orderlist_id = form.cleaned_data.get('orderlist_id')
        express_no = form.cleaned_data['express_no']
        orderlist = OrderList.objects.filter(id__in=orderlist_id.split(',')).first()
        supplier_id = orderlist.supplier.id
        now = datetime.datetime.now()
        username = self.get_username(request.user)
        tmp = ['-->%s %s: 创建入仓单' % (now.strftime('%m月%d %H:%M'), username)]
        if form.cleaned_data['memo']:
            tmp.append(form.cleaned_data['memo'])

        inbound = InBound(supplier_id=supplier_id,
                          creator_id=request.user.id,
                          express_no=express_no,
                          ori_orderlist_id=orderlist_id,
                          memo='\n'.join(tmp))
        if orderlist_id:
            inbound.orderlist_ids = [orderlist_id]
        inbound.save()

        inbounddetails_dict = {}
        for sku in ProductSku.objects.select_related('product').filter(
                id__in=inbound_skus_dict.keys()):
            sku_dict = inbound_skus_dict[sku.id]
            arrival_quantity = sku_dict.get('arrival_quantity') or 0
            inferior_quantity = sku_dict.get('inferior_quantity') or 0
            inbounddetail = InBoundDetail(inbound=inbound,
                                          product=sku.product,
                                          sku=sku,
                                          product_name=sku.product.name,
                                          outer_id=sku.product.outer_id,
                                          properties_name=sku.properties_name,
                                          arrival_quantity=arrival_quantity,
                                          inferior_quantity=inferior_quantity)
            if not inbounddetail.sku:
                inbounddetail.wrong = True
            inbounddetail.save()
            inbounddetails_dict[sku.id] = {
                'id': inbounddetail.id,
                'arrival_quantity': arrival_quantity,
                'inferior_quantity': inferior_quantity
            }
        if 0 in inbound_skus_dict:
            problem_sku_dict = inbound_skus_dict[0]
            InBoundDetail(inbound=inbound,
                          product_name=problem_sku_dict['name'],
                          arrival_quantity=problem_sku_dict['arrival_quantity'],
                          status=InBoundDetail.PROBLEM).save()

        # orderlists = self._find_orderlists(inbound_skus.keys())
        # allocate_dict = self._find_optimized_allocate_dict(
        #     inbound_skus_dict, [x['orderlist_id']
        #                         for x in orderlists], orderlist_id, express_no)
        log_action(request.user.id, inbound, ADDITION, '创建')
        return Response({
            "res": True,
            'inbound': {
                'id': inbound.id,
                # 'details': inbounddetails_dict,
                # 'memo': inbound.memo
            },
        })

    @classmethod
    def _find_orderlists(cls, sku_ids):
        orderlist_ids = set()
        for orderdetail in OrderDetail.objects.filter(
                chichu_id__in=sku_ids).exclude(
            orderlist__status__in=
            [OrderList.COMPLETED, OrderList.ZUOFEI, OrderList.CLOSED,
             OrderList.TO_PAY, OrderList.SUBMITTING]):
            orderlist_ids.add(orderdetail.orderlist_id)
        return cls._build_orderlists(list(orderlist_ids))

    @classmethod
    def _build_orderlists(cls, orderlist_ids):
        status_mapping = dict(OrderList.ORDER_PRODUCT_STATUS)
        product_ids = set()
        sku_ids = set()
        orderlists_dict = {}
        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            buyer_name = '未知'
            if orderlist.buyer_id:
                buyer_name = '%s%s' % (orderlist.buyer.last_name,
                                       orderlist.buyer.first_name)
                buyer_name = buyer_name or orderlist.buyer.username
            orderlists_dict[orderlist.id] = {
                'id': orderlist.id,
                'buyer_name': buyer_name,
                'created': orderlist.created.strftime('%y年%m月%d'),
                'status': status_mapping.get(orderlist.status) or '未知',
                'products': {}
            }
        for orderdetail in OrderDetail.objects.filter(
                orderlist_id__in=orderlist_ids).order_by('id'):
            orderlist_dict = orderlists_dict[orderdetail.orderlist_id]
            product_id = int(orderdetail.product_id)
            sku_id = int(orderdetail.chichu_id)
            product_ids.add(product_id)
            sku_ids.add(sku_id)
            products_dict = orderlist_dict['products']
            skus_dict = products_dict.setdefault(product_id, {})
            skus_dict[sku_id] = {
                'buy_quantity': orderdetail.buy_quantity,
                'plan_quantity': orderdetail.buy_quantity - min(
                    orderdetail.arrival_quantity, orderdetail.buy_quantity),
                'orderdetail_id': orderdetail.id
            }
        saleproduct_ids = set()
        products_dict = {}
        for product in Product.objects.filter(id__in=list(product_ids)):
            products_dict[product.id] = {
                'id': product.id,
                'name': product.name,
                'saleproduct_id': product.sale_product,
                'outer_id': product.outer_id,
                'pic_path': product.pic_path,
                'ware_by': product.ware_by
            }
            saleproduct_ids.add(product.sale_product)
        skus_dict = {}
        for sku in ProductSku.objects.filter(id__in=list(sku_ids)):
            skus_dict[sku.id] = {
                'id': sku.id,
                'properties_name': sku.properties_name or sku.properties_alias,
                'barcode': sku.barcode,
                'is_inbound': 1
            }
        saleproducts_dict = {}
        for saleproduct in SaleProduct.objects.filter(
                id__in=list(saleproduct_ids)):
            saleproducts_dict[saleproduct.id] = {
                'product_link': saleproduct.product_link
            }
        orderlists = []
        for orderlist_id in sorted(orderlists_dict.keys()):
            orderlist_dict = orderlists_dict[orderlist_id]
            orderlist_products_dict = orderlist_dict['products']
            orderlist_products = []
            len_of_skus = 0
            for product_id in sorted(orderlist_products_dict.keys()):
                product_dict = copy.copy(products_dict[product_id])
                product_dict.update(saleproducts_dict.get(product_dict[
                                                              'saleproduct_id']) or {})
                orderlist_skus_dict = orderlist_products_dict[product_id]
                for sku_id in sorted(orderlist_skus_dict.keys()):
                    len_of_skus += 1
                    sku_dict = orderlist_skus_dict[sku_id]
                    sku_dict.update(skus_dict[sku_id])
                    product_dict.setdefault('skus', []).append(sku_dict)
                orderlist_products.append(product_dict)
            orderlist_dict['orderlist_id'] = orderlist_id
            orderlist_dict['products'] = orderlist_products
            orderlist_dict['len_of_skus'] = len_of_skus
            orderlists.append(orderlist_dict)
        return orderlists

    def list(self, request):
        form = forms.InBoundForm(request.GET)
        if not form.is_valid():
            if not form.cleaned_data.get('express_no'):
                return Response({}, template_name='dinghuo/inbound_add.html')
            return Response({"error_message": form.errors.as_text()}, template_name='dinghuo/inbound_add.html')
        if not form.cleaned_data['orderlist_id'] or not form.cleaned_data['express_no']:
            return Response({"error_message": form.errors.as_text()}, template_name='dinghuo/inbound_add.html')
        order_lists = OrderList.objects.filter(id__in=form.cleaned_data['orderlist_id'].split(','))
        if order_lists.count() == 0:
            return Response({"error_message": form.errors.as_text()}, template_name='dinghuo/inbound_add.html')
        if len(order_lists.values("supplier").distinct()) > 1:
            raise exceptions.ValidationError("只有同一个供应商的订货单可写在一起")
        supplier = order_lists.first().supplier
        if not supplier:
            return Response({"error_message": u"这个订货单居然没有指定供应商，请联系技术"}, template_name='dinghuo/inbound_add.html')
        supplier_id = supplier.id
        # TODO@hy 下面一段超傻代码有功夫再去优化吧 前后端重度耦合又故作复杂耗时较大不好改
        orderlist_id_dict = {}
        express_no_dict = {}
        for orderlist in OrderList.objects.select_related('supplier').exclude(
                status__in=[OrderList.COMPLETED, OrderList.ZUOFEI,
                            OrderList.CLOSED, OrderList.TO_PAY]).exclude(supplier_id=None):
            orderlist_id_dict[orderlist.id] = orderlist.supplier_id
            if orderlist.express_no:
                for express_no in self.EXPRESS_NO_SPLIT_PATTERN.split(
                        orderlist.express_no.strip()):
                    express_no_dict[express_no.strip()] = orderlist.supplier_id

        result = {
            'express_no': form.cleaned_data['express_no'],
            'orderlist_id': form.cleaned_data['orderlist_id'],
            'orderlist_ids': [{'id': v,
                               'text': k}
                              for k, v in orderlist_id_dict.iteritems()],
            'express_nos': [{'id': v,
                             'text': k} for k, v in express_no_dict.iteritems()]
        }
        supplier_orderlist_ids = []
        for orderlist in OrderList.objects.filter(
                supplier_id=supplier_id).exclude(
            status__in=[OrderList.COMPLETED, OrderList.ZUOFEI,
                        OrderList.CLOSED, OrderList.TO_PAY]):
            orderlist_express_nos = self.EXPRESS_NO_SPLIT_PATTERN.split(
                orderlist.express_no.strip())
            if form.cleaned_data.get('orderlist_id') and form.cleaned_data[
                'orderlist_id'] == orderlist.id:
                supplier_orderlist_ids.insert(0, orderlist.id)
            elif form.cleaned_data.get('express_no') and form.cleaned_data[
                'express_no'] in orderlist_express_nos:
                supplier_orderlist_ids.insert(0, orderlist.id)
            else:
                supplier_orderlist_ids.append(orderlist.id)

        product_ids = set()
        sku_ids = set()
        product_weights_dict = {}
        max_weight = len(supplier_orderlist_ids)
        weights = {k: i for i, k in enumerate(supplier_orderlist_ids)}

        for orderdetail in OrderDetail.objects.filter(
                orderlist_id__in=supplier_orderlist_ids):
            if orderdetail.buy_quantity <= orderdetail.arrival_quantity:
                continue
            product_id = int(orderdetail.product_id)
            product_weights_dict[product_id] = min(
                product_weights_dict.setdefault(product_id, max_weight),
                weights[orderdetail.orderlist_id])
            product_ids.add(product_id)
            sku_ids.add(int(orderdetail.chichu_id))

        saleproduct_ids = set()
        for product in Product.objects.filter(id__in=list(product_ids)):
            saleproduct_ids.add(product.sale_product)
        saleproducts_dict = {}
        sibling_product_ids = []
        for product in Product.objects.filter(
                sale_product__in=list(saleproduct_ids),
                status=Product.NORMAL):
            saleproducts_dict.setdefault(product.sale_product,
                                         []).append(product.id)
            sibling_product_ids.append(product.id)
        sibling_products_dict = {}
        district_stats = ProductLocation.objects.select_related(
            'district').filter(product_id__in=sibling_product_ids).values(
            'product_id', 'district').annotate(num=Count('sku_id'))
        for district_stat in district_stats:
            product_id = district_stat['product_id']
            sibling_products_dict.setdefault(
                product_id, {'district': district_stat['district'],
                             'num': 0})['num'] += district_stat['num']
        saleproduct_districts_dict = {}
        for saleproduct_id, sibling_product_ids in saleproducts_dict.iteritems(
        ):
            saleproduct_districts = filter(
                None, [sibling_products_dict.get(product_id)
                       for product_id in sibling_product_ids])
            if not saleproduct_districts:
                continue
            saleproduct_districts_dict[saleproduct_id] = max(
                saleproduct_districts,
                key=lambda x: x['num'])['district']

        deposite_districts_dict = {}
        for deposite_district in DepositeDistrict.objects.filter(
                id__in=saleproduct_districts_dict.values()):
            deposite_districts_dict[deposite_district.id] = str(
                deposite_district)
        for k in saleproduct_districts_dict.keys():
            deposite_district_id = saleproduct_districts_dict[k]
            saleproduct_districts_dict[k] = deposite_districts_dict[
                deposite_district_id]

        products_dict = {}
        for sku in ProductSku.objects.select_related('product').filter(
                product_id__in=list(product_ids),
                status=ProductSku.NORMAL):
            product_dict = {
                'id': sku.product.id,
                'saleproduct_id': sku.product.sale_product,
                'name': sku.product.name,
                'outer_id': sku.product.outer_id,
                'district': sku.product.get_district_info(),
                'pic_path': '%s' % sku.product.pic_path.strip(),
                'ware_by': sku.product.ware_by,
                'skus': {},
                'weight': product_weights_dict[sku.product.id]
            }
            product_dict = products_dict.setdefault(sku.product.id,
                                                    product_dict)
            sku_dict = {
                'id': sku.id,
                'properties_name': sku.properties_name or
                                   sku.properties_alias,
                'barcode': sku.barcode,
                'district':
                    saleproduct_districts_dict.get(sku.product.sale_product) or
                    ''
            }
            if sku.id in sku_ids:
                sku_dict['is_required'] = 1
            product_dict['skus'][sku.id] = sku_dict
        saleproducts_dict = {}
        saleproduct_ids = list(set([x['saleproduct_id'] for x in products_dict.values()]))
        for saleproduct in SaleProduct.objects.filter(
                id__in=saleproduct_ids):
            saleproducts_dict[saleproduct.id] = {
                'product_link': saleproduct.product_link,
                'title': saleproduct.title
            }

        products = []
        for product_dict in sorted(products_dict.values(),
                                   key=itemgetter('id')):
            skus_dict = product_dict['skus']
            product_dict['skus'] = [skus_dict[k]
                                    for k in sorted(skus_dict.keys())]
            product_dict.update(saleproducts_dict.get(product_dict[
                                                          'saleproduct_id']) or {})
            products.append(product_dict)
        result.update({
            'supplier_id': supplier.id,
            'supplier_name': supplier.supplier_name,
            'products': products
        })
        return Response(result, template_name='dinghuo/inbound_add.html')

    @detail_route(methods=['post'])
    def set_invalid(self, request, pk=None):
        from shopback.items.tasks import releaseProductTradesTask
        inbound = InBound.objects.get(id=pk)
        if inbound.status == InBound.INVALID:
            return Response({'error': '已经作废'})

        orderlist_ids = set()
        outer_ids = set()
        for inbounddetail in InBoundDetail.objects.filter(inbound=inbound):
            for record in inbounddetail.records.filter(
                    status=OrderDetailInBoundDetail.NORMAL):
                inbounddetail = record.inbounddetail
                orderdetail = record.orderdetail
                sku = inbounddetail.sku

                orderlist_ids.add(orderdetail.orderlist_id)
                outer_ids.add(sku.product.outer_id)

                if record.arrival_quantity > 0:
                    sku.quantity -= record.arrival_quantity
                    sku.save()
                    log_action(request.user.id, sku, CHANGE, u'作废入仓单%d: 更新库存%+d'
                               % (inbound.id, 0 - record.arrival_quantity))
                record.status = OrderDetailInBoundDetail.INVALID
                record.save()

        if orderlist_ids:
            self.update_orderlist(request, list(orderlist_ids))
        if outer_ids:
            releaseProductTradesTask.delay(list(outer_ids))
        inbound.status = InBound.INVALID
        inbound.save()
        log_action(request.user.id, inbound, CHANGE, u'作废')
        return Response({})

    @list_route(methods=['get'])
    def find_orderlists(self, request):
        inbound_skus = json.loads(request.GET['inbound_skus'])
        inbound_id = int(request.GET['inbound_id'])

        inbound = InBound.objects.get(id=inbound_id)
        if inbound.status != InBound.PENDING:
            return Response({'error': '只有待处理入仓单才可以分配'})

        orderlists = self._find_orderlists(inbound_skus.keys())
        return Response({'orderlists': orderlists})

    @list_route(methods=['get'])
    def add_memo(self, request):
        username = self.get_username(request.user)
        now = datetime.datetime.now()
        content = request.GET.get('content') or ''
        if not content:
            return Response({'memo': ''})
        memo = '-->%s %s: %s' % (now.strftime('%m月%d %H:%M'), username, content)
        return Response({'memo': memo})

    @detail_route(methods=['get'])
    def get_allocate_order_lists(self, request, pk=None):
        inbound = get_object_or_404(InBound, pk=pk)
        res = {'order_lists': inbound.may_allocate_order_list_items(),
               'inbound_sku_data': inbound.sku_data,
               }
        if inbound.status == InBound.PENDING:
            res['suggest_allocate'] = inbound.get_optimized_allocate_dict()
        return Response(res)

    @detail_route(methods=['get'])
    def get_allocate_inbound_details(self, request, pk=None):
        inbound = get_object_or_404(InBound, pk=pk)
        res = {'order_lists': inbound.may_allocate_order_list_items2(),
               'inbound_sku_data': inbound.sku_data,
               }
        if inbound.status == InBound.PENDING:
            res['suggest_allocate'] = inbound.get_optimized_allocate_dict()
        return Response(res)

    @detail_route(methods=['get'])
    def get_allocate_inbound_order_details(self, request, pk=None):
        inbound = get_object_or_404(InBound, pk=pk)
        res = {'order_lists': inbound.get_allocate_order_details_dict(),
               'inbound_sku_data': inbound.sku_data,
               }
        if inbound.status == InBound.PENDING:
            res['suggest_allocate'] = inbound.get_optimized_allocate_dict()
        return Response(res)

    @detail_route(methods=['get'])
    def get_optimized_allocate_dict(self, request, pk=None):
        inbound = get_object_or_404(InBound, pk=pk)
        return Response(inbound.get_optimized_allocate_dict())

    @list_route(methods=['post'])
    def save_memo(self, request):
        form = forms.SaveMemoForm(request.POST)
        if not form.is_valid():
            return Response({'error': '参数错误'})

        if form.cleaned_data['memo']:
            inbound = InBound.objects.get(id=form.cleaned_data['inbound_id'])
            inbound.memo = form.cleaned_data['memo']
            inbound.save()
        return Response({})

    @classmethod
    def get_username(cls, user):
        from common.utils import get_admin_name
        return get_admin_name(user)

    @detail_route(methods=['post'])
    def allocate(self, request, pk=None):
        inbound = InBound.objects.get(id=pk)
        data = json.loads(request.POST.get('data') or '[]')
        inbound.allocate(data)
        return Response({'res': True})

    @detail_route(methods=['post'])
    def add_total_quantity(self, request, pk=None):
        num = int(request.POST.get('num', 1))
        inbound_detail_id = request.POST.get('inbound_detail_id')
        inbound_detail = get_object_or_404(InBoundDetail, id=inbound_detail_id)
        try:
            inbound_detail.change_total_quantity(num)
            return Response({'res': True})
        except Exception, e0:
            raise exceptions.ParseError(e0.message)

    @detail_route(methods=['post'])
    def add_allocate_quantity(self, request, pk=None):
        num = int(request.POST.get('num', 1))
        orderdetail_id = request.POST.get('orderdetail_id')
        inbound = get_object_or_404(InBound, pk=pk)
        orderdetail = get_object_or_404(OrderDetail, pk=orderdetail_id)
        relation = OrderDetailInBoundDetail.objects.filter(orderdetail_id=orderdetail_id,
                                     inbounddetail__inbound__id=inbound.id).first()
        try:
            if relation:
                relation.change_arrival_quantity(num)
            else:
                relation = inbound.add_order_detail(orderdetail, num)
            return Response({'res': True, 'data': {'sku': relation.inbounddetail.sku_id,
                                                   'status_info': relation.inbounddetail.get_status_info()}})
        except Exception, e0:
            raise exceptions.ParseError(e0.message)

    @detail_route(methods=['post'])
    def finish_check(self, request, pk):
        inbound = get_object_or_404(InBound, pk=pk)
        inferior_data = request.POST.get("data")
        sku_data = json.loads(inferior_data)
        inbound.finish_check(sku_data)
        return Response({'res': True})

    @detail_route(methods=['post'])
    def finish_item_check(self, request, pk):
        inbound_detail_id = request.POST.get('inbound_detail_id')
        inbound_detail = get_object_or_404(InBoundDetail, id=inbound_detail_id)
        arrival_quantity = int(request.POST.get("arrival_quantity"))
        inferior_quantity = int(request.POST.get("inferior_quantity"))
        try:
            inbound_detail.finish_change_inferior(arrival_quantity, inferior_quantity)
            return Response({'res': True})
        except Exception, e0:
            raise exceptions.ParseError(e0.message)

    @detail_route(methods=['post'])
    def generate_return_goods(self, request, pk):
        inbound = get_object_or_404(InBound, pk=pk)
        inbound.generate_return_goods(request.user.username)
        return Response({'res': True})

    @detail_route(methods=['post'])
    def reset_to_verify(self, request, pk):
        inbound = InBound.objects.get(id=pk)
        if inbound.status != InBound.COMPLETED:
            raise exceptions.APIException(u'已完成状态的入库单才需要重置到待检查')
        inbound.reset_to_verify()
        return Response({})

    @detail_route(methods=['post'])
    def reset_to_allocate(self, request, pk):
        inbound = InBound.objects.get(id=pk)
        if inbound.status != InBound.WAIT_CHECK:
            raise exceptions.APIException(u'待质检状态的入库单才需要重置到待分配')
        inbound.reset_to_allocate()
        return Response({})

    def retrieve(self, request, pk=None):
        inbound = get_object_or_404(InBound, id=pk)
        supplier = inbound.supplier

        result = {
            'supplier_id': supplier.id,
            'supplier_name': supplier.supplier_name,
            'warehouses': self.WARE_HOUSES,
            'inbound': inbound
        }
        if inbound.status == InBound.PENDING:
            template_name = 'dinghuo/inbound_allocate.html'
        elif inbound.status == InBound.WAIT_CHECK:
            template_name = 'dinghuo/inbound_verify.html'
        else:
            template_name = 'dinghuo/inbound_detail.html'
        return Response(result, template_name=template_name)

    # --------------------------------------------------------------------------
    @classmethod
    def _find_optimized_allocate_dict(cls, inbound_skus_dict, orderlist_ids,
                                      orderlist_id, express_no):
        import numpy as np
        boxes = []
        orderlists = []
        orderlist_ids_with_express_no = []
        for orderlist in OrderList.objects.filter(
                id__in=orderlist_ids).order_by('id'):
            orderlists.append(orderlist)
            orderlist_express_nos = [
                x.strip()
                for x in cls.EXPRESS_NO_SPLIT_PATTERN.split(
                    orderlist.express_no.strip())
                ]
            if express_no and orderlist.express_no and express_no.strip(
            ) in orderlist_express_nos:
                orderlist_ids_with_express_no.append(orderlist_id)
            orderlist_skus_dict = {}
            for orderdetail in orderlist.order_list.all():
                orderlist_skus_dict[int(orderdetail.chichu_id)] = max(
                    orderdetail.buy_quantity - orderdetail.arrival_quantity, 0)
            row = []
            for sku_id in sorted(inbound_skus_dict.keys()):
                row.append(orderlist_skus_dict.get(sku_id) or 0)
            boxes.append(row)
        boxes = np.matrix(boxes)
        package = np.matrix([inbound_skus_dict[k]['arrival_quantity']
                             for k in sorted(inbound_skus_dict.keys())])
        orderlist_ids = sorted(orderlist_ids)
        n = len(orderlist_ids)
        z = sys.maxint
        solution = 0
        for i in range(1, 1 << n):
            x = np.matrix([int(j) for j in ('{0:0%db}' % n).format(i)])
            tmp = np.dot(boxes.T, x.T) - package.T
            tmp = np.abs(tmp).sum()
            if z > tmp:
                z = tmp
                solution = i
        matched_orderlist_ids = []
        for i, j in enumerate(('{0:0%db}' % n).format(solution)):
            if int(j) > 0:
                matched_orderlist_ids.append(orderlist_ids[i])
        if orderlist_id and orderlist_id not in matched_orderlist_ids:
            matched_orderlist_ids.append(orderlist_id)
        tail_orderlist_ids = []
        for orderlist in orderlists:
            if orderlist.id in matched_orderlist_ids:
                continue
            if orderlist.id in orderlist_ids_with_express_no:
                matched_orderlist_ids.append(orderlist.id)
            else:
                tail_orderlist_ids.append(orderlist.id)
        orderlists = sorted(
            orderlists,
            key=
            lambda x: (matched_orderlist_ids + tail_orderlist_ids).index(x.id))
        allocate_dict = {}
        for orderlist in orderlists:
            for orderdetail in orderlist.order_list.all():
                sku_id = int(orderdetail.chichu_id)
                inbound_sku_dict = inbound_skus_dict.get(sku_id)
                if not inbound_sku_dict:
                    continue
                delta = min(
                    max(orderdetail.buy_quantity - orderdetail.arrival_quantity,
                        0), inbound_sku_dict['arrival_quantity'])
                if delta > 0:
                    allocate_dict[orderdetail.id] = delta
                    inbound_sku_dict['arrival_quantity'] -= delta
                    if inbound_sku_dict['arrival_quantity'] <= 0:
                        inbound_skus_dict.pop(sku_id, False)
        return allocate_dict

    @classmethod
    def _find_allocate_dict(cls, inbound_skus_dict, orderlist_ids, orderlist_id,
                            express_no):
        orderlists_with_express_no = []
        orderlists_without_express_no = []
        for orderlist in OrderList.objects.filter(
                id__in=[x for x in orderlist_ids if x != orderlist_id
                        ]).order_by('id'):
            if express_no and orderlist.express_no:
                if express_no.strip() in [
                    x.strip()
                    for x in cls.EXPRESS_NO_SPLIT_PATTERN.split(
                        orderlist.express_no.strip())
                    ]:
                    orderlists_with_express_no.append(orderlist)
                    continue
            orderlists_without_express_no.append(orderlist)
        if orderlist_id:
            orderlists = [OrderList.objects.get(id=orderlist_id)]
        else:
            orderlists = []
        orderlists = orderlists + orderlists_with_express_no + orderlists_without_express_no
        allocate_dict = {}
        for orderlist in orderlists:
            for orderdetail in orderlist.order_list.all():
                sku_id = int(orderdetail.chichu_id)
                inbound_sku_dict = inbound_skus_dict.get(sku_id)
                if not inbound_sku_dict:
                    continue
                delta = min(
                    max(orderdetail.buy_quantity - orderdetail.arrival_quantity,
                        0), inbound_sku_dict['arrival_quantity'])
                if delta > 0:
                    allocate_dict[orderdetail.id] = delta
                    inbound_sku_dict['arrival_quantity'] -= delta
                    if inbound_sku_dict['arrival_quantity'] <= 0:
                        inbound_skus_dict.pop(sku_id, False)
        return allocate_dict
