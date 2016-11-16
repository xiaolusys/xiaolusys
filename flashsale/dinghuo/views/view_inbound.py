# coding=utf-8
import copy
import datetime
import json
import re
import sys
from collections import defaultdict
from django.db.models import F, Q, Sum, Count
from rest_framework import generics, permissions, renderers, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions
from core.options import log_action, ADDITION, CHANGE
from flashsale.dinghuo.models import (OrderDraft, OrderDetail, OrderList,
                                      InBound, InBoundDetail,
                                      OrderDetailInBoundDetail)
from shopback.items.models import Product,ProductSku
from supplychain.supplier.models import SaleProduct, SaleSupplier
from .. import forms, functions, functions2view, models
from django.shortcuts import get_object_or_404
from django.shortcuts import HttpResponseRedirect
from flashsale.dinghuo.serializers import InBoundSerializer
from .. import services

import logging
logger = logging.getLogger(__name__)


class InBoundViewSet(viewsets.GenericViewSet):
    serializer_class = InBoundSerializer
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

    def get_optimize_forecast_id(self, inbound_skus):
        forecast_group = defaultdict(list)
        for id, sku in inbound_skus.iteritems():
            forecast_group[int(sku['forecastId'])].append(int(sku['arrival_quantity']))
        forecast_group_sum = dict([(k, sum(v)) for k, v in forecast_group.items()])
        optimize_groups = {}
        for forecast_id, arrival_num in forecast_group_sum.items():
            forecast_data = services.get_forecastinbound_data(forecast_id)
            delta_num = forecast_data['total_forecast_num'] - forecast_data['total_arrival_num']
            if delta_num >= arrival_num:
                optimize_groups[forecast_id] = arrival_num
        if not optimize_groups:
            optimize_groups = forecast_group_sum
        optimize_forecast_id = max(optimize_groups, key=lambda x: optimize_groups.get(x))
        logger.warning('inbound:optimize_forecast_id=%s, forecast_group=%s, optimize_groups=%s'%(
            optimize_forecast_id, dict(forecast_group), optimize_groups))
        return optimize_forecast_id

    @list_route(methods=['post'])
    def create_inbound(self, request):
        form = forms.CreateInBoundForm(request.POST)
        if not form.is_valid():
            return Response({'orderlists': [], "error_message": form.errors.as_text()})

        inbound_skus = json.loads(form.cleaned_data['inbound_skus'])
        if not inbound_skus:
            return Response({'orderlists': [], "error_message": 'inbound skus data not valid;'})
        inbound_skus_dict = {int(k): v for k, v in inbound_skus.iteritems()}
        for sku in ProductSku.objects.filter(id__in=inbound_skus_dict.keys()):
            inbound_skus_dict[sku.id]['product_id'] = sku.product_id
        orderlist_id = form.cleaned_data.get('orderlist_id')

        optimize_forecast_id = self.get_optimize_forecast_id(inbound_skus)
        forecast_inbound_data = services.get_forecastinbound_data(optimize_forecast_id)
        express_no = form.cleaned_data['express_no']
        relate_orderids = forecast_inbound_data['relate_order_set']
        supplier_id = forecast_inbound_data['supplier']
        now = datetime.datetime.now()
        username = self.get_username(request.user)
        tmp = ['-->%s %s: 创建入仓单' % (now.strftime('%m月%d %H:%M'), username)]
        if form.cleaned_data['memo']:
            tmp.append(form.cleaned_data['memo'])

        inbound = InBound(supplier_id=supplier_id,
                          creator_id=request.user.id,
                          express_no=express_no,
                          forecast_inbound_id=optimize_forecast_id,
                          ori_orderlist_id=orderlist_id,
                          memo='\n'.join(tmp))
        if relate_orderids:
            inbound.orderlist_ids = list(relate_orderids.values_list('id', flat=True))
        inbound.save()
        
        inbounddetails_dict = {}
        wrong_sku_id = 222222
        for sku in ProductSku.objects.select_related('product').filter(
                id__in=inbound_skus_dict.keys()):
            sku_dict = inbound_skus_dict[sku.id]
            arrival_quantity = sku_dict.get('arrival_quantity') or 0
            inferior_quantity = sku_dict.get('inferior_quantity') or 0
            memo = sku_dict.get('memo', '')
            inbounddetail = InBoundDetail(inbound=inbound,
                                          product=sku.product,
                                          sku=sku,
                                          product_name=sku.product.name,
                                          outer_id=sku.product.outer_id,
                                          properties_name=sku.properties_name,
                                          arrival_quantity=arrival_quantity,
                                          inferior_quantity=inferior_quantity,
                                          memo=memo)
            if inbounddetail.sku_id == wrong_sku_id:
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

        try:
            from flashsale.forecast import apis
            apis.api_create_or_update_realinbound_by_inbound(inbound.id)
        except Exception,exc:
            logger.error(exc.message, exc_info=True)
        log_action(request.user.id, inbound, ADDITION, '创建')
        from flashsale.dinghuo.tasks import task_inbound_check_out_stock, task_inbound_check_inferior
        task_inbound_check_out_stock.delay()
        task_inbound_check_inferior.delay()
        return Response({
            "res": True,
            'inbound': {
                'id': inbound.id,
                # 'details': inbounddetails_dict,
                # 'memo': inbound.memo
            },
        })

    @classmethod
    def get_forecast_inbounds(cls, express_no, orderlist_id):
        """ 根据订单号及快递单号找到未到货预测单,　如果没有找到则列出所有未完成预测单 """
        from flashsale.forecast.models import ForecastInbound
        if orderlist_id.isdigit():
            orderlist_id = int(orderlist_id)
        else:
            orderlist_id = 0
        order_list = OrderList.objects.filter(Q(id=orderlist_id) | Q(express_no=express_no)).first()
        supplier = None
        forecast_inbounds = ForecastInbound.objects.filter(
            Q(relate_order_set=orderlist_id) | Q(express_no=express_no),
            status__in=(ForecastInbound.ST_APPROVED,ForecastInbound.ST_DRAFT))
        if forecast_inbounds.exists():
            return forecast_inbounds.distinct()

        forecast_inbounds = []
        if order_list:
            supplier = order_list.supplier
        else:
            forecast_inbound = ForecastInbound.objects.filter(
                Q(id=orderlist_id) | Q(express_no=express_no)).first()
            if forecast_inbound:
                supplier = forecast_inbound.supplier

        if supplier:
            forecast_qs = ForecastInbound.objects.filter(supplier=supplier,
                status__in=(ForecastInbound.ST_APPROVED,ForecastInbound.ST_DRAFT,ForecastInbound.ST_ARRIVED)
            ).exclude(status=ForecastInbound.ST_ARRIVED,has_lack=False,has_defact=False).order_by('-status','created')
            for fi in forecast_qs:
                if fi.express_no == express_no or fi.id == orderlist_id:
                    forecast_inbounds.insert(0, fi)
                    continue
                is_find_obj = False
                order_values = fi.relate_order_set.values('id','express_no')
                for order in order_values:
                    if order['id'] == orderlist_id or order['express_no'] == express_no:
                        forecast_inbounds.insert(0, fi)
                        is_find_obj = True
                        continue
                if not is_find_obj:
                    forecast_inbounds.append(fi)
        return forecast_inbounds

    def list(self, request, *args, **kwargs):
        form = forms.InBoundForm(request.GET)
        if not form.is_valid():
            if not form.cleaned_data.get('express_no'):
                return Response({}, template_name='dinghuo/inbound_add.html')
            return Response({"error_message": form.errors.as_text()}, template_name='dinghuo/inbound_add.html')
        orderlist_id = form.cleaned_data['orderlist_id']
        if not orderlist_id or not form.cleaned_data['express_no']:
            return Response({"error_message": form.errors.as_text()}, template_name='dinghuo/inbound_add.html')
        forecast_inbounds = InBoundViewSet.get_forecast_inbounds(form.cleaned_data['express_no'], orderlist_id)
        if not forecast_inbounds:
            return Response({"error_message": form.errors.as_text()}, template_name='dinghuo/inbound_add.html')
        supplier = forecast_inbounds[0].supplier
        if not supplier:
            return Response({"error_message": u"这个预测到货单居然没有指定供应商，请联系技术"}, template_name='dinghuo/inbound_add.html')

        result = {
            'express_no': form.cleaned_data['express_no'],
            'orderlist_id': form.cleaned_data['orderlist_id'],
        }

        forecast_list = []
        for forecast in forecast_inbounds:
            forecast_details = forecast.normal_details.values('product_id','sku_id','forecast_arrive_num')
            forecast_details_dict = dict([(d['sku_id'], d) for d in forecast_details])

            product_ids = set([f['product_id'] for f in forecast_details])
            product_qs = Product.objects.filter(id__in=product_ids)
            forecast_product_list = []
            for product in product_qs:
                sku_dict_list = []
                for sku in product.normal_skus:
                    sku_dict = {
                        "id": sku.id,
                        "properties_name": sku.name,
                        "barcode": sku.BARCODE,
                        "district": ','.join(['%s-%s'%(k, v) for k,v in  sku.get_district_list()])
                    }
                    fi_sku_dict = forecast_details_dict.get(sku.id, {})
                    sku_dict.update({
                        'is_required': fi_sku_dict and 1 or 0,
                        'forecast_arrive_num': fi_sku_dict and fi_sku_dict['forecast_arrive_num'] or 0
                    })
                    sku_dict_list.append(sku_dict)

                forecast_product_list.append({
                    "name": product.name,
                    "weight": 1,
                    "saleproduct_id": product.sale_product,
                    "ware_by": product.ware_by,
                    "district": ','.join(['%s-%s'%(k, v) for k,v in  product.get_district_list()]),
                    "pic_path": product.pic_path,
                    "outer_id": product.outer_id,
                    "id": product.id,
                    "skus": sku_dict_list
                })
            sale_product_ids  = set([p['saleproduct_id'] for p in forecast_product_list])
            saleproduct_values = SaleProduct.objects.filter(id__in=sale_product_ids)\
                .values('id','product_link')
            saleproduct_values_dict = dict([(v['id'],v) for v in saleproduct_values])
            for fp in forecast_product_list:
                saleproduct_dict = saleproduct_values_dict.get(fp['saleproduct_id'], {})
                fp.update({
                    'product_link': saleproduct_dict and saleproduct_dict['product_link'] or ''
                })

            forecast_list.append({
                'id': forecast.id,
                'relate_order_ids': ','.join([str(s) for s in forecast.relate_order_set.values_list('id', flat=True)]),
                'total_detail_num': forecast.total_detail_num,
                'products': forecast_product_list
            })

        result.update({
            'supplier_id': supplier.id,
            'supplier_name': supplier.supplier_name,
            'forecasts': forecast_list
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
            inbound.update_orderlist(request, list(orderlist_ids))
        if outer_ids:
            releaseProductTradesTask.delay(list(outer_ids))
        inbound.status = InBound.INVALID
        inbound.save()
        log_action(request.user.id, inbound, CHANGE, u'作废')
        return Response({})

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
        try:
            inbound.finish_check(sku_data)
            return Response({'res': True})
        except Exception, e0:
            raise exceptions.ParseError(e0.message)

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