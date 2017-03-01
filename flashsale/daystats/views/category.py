# coding: utf8
from __future__ import absolute_import, unicode_literals

import copy
import datetime
from collections import defaultdict
from django.db.models import F, Q, Sum, Count

from rest_framework import generics, permissions, renderers, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions

from core.utils.timeutils import parse_str2date
from supplychain.supplier.models import SaleCategory
from shopback.items.models import ProductSku
from flashsale.pay.models import ModelProduct
from ..models import DailySkuDeliveryStat, DailySkuAmountStat, DailyBoutiqueStat

import logging
logger = logging.getLogger(__name__)

DEFAULT_DELIVERY_TPL = {
    '1': {'post_num': 0, 'wait_num': 0},
    '2': {'post_num': 0, 'wait_num': 0},
    '3': {'post_num': 0, 'wait_num': 0},
    '4': {'post_num': 0, 'wait_num': 0},
    '5': {'post_num': 0, 'wait_num': 0},
    '6': {'post_num': 0, 'wait_num': 0},
    'inf': {'post_num': 0, 'wait_num': 0},
}

DEFAULT_SALES_TPL = {
    'total_amount': 0, 'direct_payment': 0, 'coupon_amount': 0,
    'coupon_payment': 0, 'exchg_amount': 0, 'coupon_sale_num': 0,
    'coupon_use_num': 0, 'coupon_refund_num': 0, 'model_stock_num': 0,
    'model_sale_num': 0, 'model_refund_num': 0, 'sale_amount': 0
}

def get_category_node_maps():
    districts = SaleCategory.objects.order_by('parent_cid', 'sort_order')
    districts_values = districts.values('id', 'cid', 'parent_cid', 'name')
    cid_id_maps = dict([(v['cid'], v['id']) for v in districts_values])

    category_node_maps = defaultdict(list)
    for district in districts_values:
        parent_id = cid_id_maps.get(district['parent_cid'], 0)
        category_node_maps[parent_id].append(district)
    return category_node_maps


class CategoryStatViewSet(viewsets.GenericViewSet):
    # serializer_class = InBoundSerializer
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = DailySkuDeliveryStat.objects.all()

    def recurse_calc_serial_data(self, node, node_maps, cat_maps):
        copy_node = node.copy()
        cat_id    = copy_node['id']
        child_nodes = node_maps.get(cat_id)
        copy_node.setdefault('children', [])
        serial_data = copy.deepcopy(DEFAULT_DELIVERY_TPL)
        serial_data.update(cat_maps.get(cat_id, {}))
        copy_node['serial_data'] = serial_data
        if not child_nodes:
            return copy_node

        for child_node in child_nodes:
            sub_node = self.recurse_calc_serial_data(child_node, node_maps, cat_maps)
            copy_node['children'].append(sub_node)
            for k, v in sub_node['serial_data'].iteritems():
                copy_node['serial_data'][k]['post_num'] += v['post_num']
                copy_node['serial_data'][k]['wait_num'] += v['wait_num']
        return copy_node


    @list_route(methods=['GET'])
    def delivery_stats(self, request, **kwargs):
        data = request.GET
        start_date = (data.get('start_date') and parse_str2date(data.get('start_date'))
                      or datetime.date.today() - datetime.timedelta(days=1))
        end_date   = data.get('end_date') and parse_str2date(data.get('end_date')) or datetime.date.today()

        delivery_qs = DailySkuDeliveryStat.objects.filter(stat_date__range=(start_date, end_date))
        delivery_skuids = list(delivery_qs.values_list('sku_id', flat=True))
        sku_category_maps = ProductSku.objects.get_sku_and_category_id_maps(delivery_skuids)

        post_stats = delivery_qs.values('sku_id','days').annotate(Sum('post_num'))\
            .values_list('sku_id', 'days', 'post_num__sum')
        wait_stats = DailySkuDeliveryStat.objects.filter(stat_date=start_date).values_list('sku_id', 'days', 'wait_num')

        category_delivery_maps = defaultdict(dict)
        for sku_id, days, num in post_stats:
            stat_days = days >= 6 and 'inf' or str(days + 1)
            cat_id    = sku_category_maps.get(sku_id)
            category_delivery_maps.setdefault(cat_id, copy.deepcopy(DEFAULT_DELIVERY_TPL))
            category_delivery_maps[cat_id][stat_days]['post_num'] += num

        for sku_id, days, num in wait_stats:
            stat_days = days >= 6 and 'inf' or str(days + 1)
            cat_id = sku_category_maps.get(sku_id)
            category_delivery_maps.setdefault(cat_id, copy.deepcopy(DEFAULT_DELIVERY_TPL))
            category_delivery_maps[cat_id][stat_days]['wait_num'] += num

        category_node_maps = get_category_node_maps()

        category_serial_data = self.recurse_calc_serial_data(
            {'id': 0, 'name':'全部类目' }, category_node_maps, category_delivery_maps)

        return Response({
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'serial_data': category_serial_data,
            })

    def recurse_sale_serial_data(self, node, node_maps, cat_sale_maps):
        copy_node = node.copy()
        cat_id = copy_node['id']
        child_nodes = node_maps.get(cat_id)
        copy_node.setdefault('children', [])
        serial_data = copy.deepcopy(DEFAULT_SALES_TPL)
        serial_data.update(cat_sale_maps.get(cat_id, {}))
        copy_node['serial_data'] = serial_data
        if not child_nodes:
            return copy_node

        for child_node in child_nodes:
            sub_node = self.recurse_sale_serial_data(child_node, node_maps, cat_sale_maps)
            copy_node['children'].append(sub_node)
            for k, v in sub_node['serial_data'].iteritems():
                copy_node['serial_data'][k] += v
        return copy_node

    @list_route(methods=['GET'])
    def skusale_stats(self, request, **kwargs):
        data = request.GET
        product_type = data.get('product_type') or 'all'
        start_date = (data.get('start_date') and parse_str2date(data.get('start_date'))
                      or datetime.date.today() - datetime.timedelta(days=1))
        end_date = data.get('end_date') and parse_str2date(data.get('end_date')) or datetime.date.today()

        virtual_modelids = list(ModelProduct.objects.filter(
            product_type=ModelProduct.VIRTUAL_TYPE).values_list('id', flat=True))

        skustock_qs  = DailyBoutiqueStat.objects.filter(stat_date__range=(start_date, end_date))
        skuamount_qs = DailySkuAmountStat.objects.filter(stat_date__range=(start_date, end_date))

        if (product_type == str(ModelProduct.USUAL_TYPE)):
            skustock_qs = skustock_qs.exclude(model_id__in=virtual_modelids)
            skuamount_qs = skuamount_qs.exclude(model_id__in=virtual_modelids)
        elif (product_type == str(ModelProduct.VIRTUAL_TYPE)):
            skustock_qs = skustock_qs.filter(model_id__in=virtual_modelids)
            skuamount_qs = skuamount_qs.filter(model_id__in=virtual_modelids)

        model_ids = list(skustock_qs.values_list('model_id', flat=True))
        model_ids.extend(list(skuamount_qs.values_list('model_id', flat=True)))

        model_category_maps = dict(ModelProduct.objects.filter(id__in=model_ids).values_list('id', 'salecategory_id'))

        #　销售金额
        modelamount_values = skuamount_qs.values('model_id').annotate(
            Sum('total_amount'),
            Sum('direct_payment'),
            Sum('coupon_amount'),
            Sum('coupon_payment'),
            Sum('exchg_amount'),
        )

        #　精品券数量, 库存, 销售数量
        modelsales_values = skustock_qs.values('model_id').annotate(
            Sum('coupon_sale_num'),
            Sum('coupon_use_num'),
            Sum('coupon_refund_num'),
            # Sum('model_stock_num'),
            Sum('model_sale_num'),
            Sum('model_refund_num'),
        )
        modelsales_maps = dict([(s['model_id'], s) for s in modelsales_values ])

        modelstock_maps = dict(skustock_qs.filter(stat_date=start_date)
        .values_list('model_id', 'model_stock_num'))

        for mvalue in modelamount_values:
            model_id = mvalue['model_id']
            modelsales_maps[model_id] = modelsales_maps.get(model_id, {})
            modelsales_maps[model_id].update(mvalue)

        category_sales_maps = defaultdict(dict)
        for mstock in modelsales_maps.iteritems():
            model_id, mvalue = mstock
            mvalue.pop('model_id')
            copy_dict = DEFAULT_SALES_TPL.copy()
            for k, v in mvalue.iteritems():
                copy_dict[k.replace('__sum', '')] = v

            copy_dict['sale_amount'] = (
                copy_dict.get('direct_payment', 0) + copy_dict.get('coupon_payment', 0)
            )
            copy_dict['model_stock_num'] = modelstock_maps.get(model_id, 0)

            cid = model_category_maps.get(model_id, 0)
            if cid not in category_sales_maps:
                category_sales_maps[cid] = copy_dict
                continue

            for k, v in copy_dict.iteritems():
                category_sales_maps[cid][k] += v

        category_node_maps = get_category_node_maps()

        category_serial_data = self.recurse_sale_serial_data(
            {'id': 0, 'name': '全部类目'}, category_node_maps, category_sales_maps)

        return Response({
            'product_type': product_type,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'serial_data': category_serial_data,
        })
