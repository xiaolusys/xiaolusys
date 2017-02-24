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
from ..models import DailySkuDeliveryStat, DailySkuAmountStat

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

        post_stats = delivery_qs.values('sku_id','days').annotate(Sum('post_num')).values_list('sku_id', 'days', 'post_num__sum')
        wait_stats = DailySkuDeliveryStat.objects.filter(stat_date=start_date).values_list('sku_id', 'days', 'wait_num')

        category_delivery_maps = defaultdict(dict)
        for sku_id, days, num in post_stats:
            stat_days = days >= 6 and 'inf' or str(days + 1)
            cat_id    = sku_category_maps.get(sku_id)
            category_delivery_maps.setdefault(cat_id, copy.deepcopy(DEFAULT_DELIVERY_TPL))
            cat_stat  = category_delivery_maps.get(cat_id)
            if not cat_stat:
                category_delivery_maps[cat_id][stat_days] = {'post_num': num, 'wait_num': 0}
            else:
                category_delivery_maps[cat_id][stat_days]['post_num'] += num

        for sku_id, days, num in wait_stats:
            stat_days = days >= 6 and 'inf' or str(days + 1)
            cat_id = sku_category_maps.get(sku_id)
            category_delivery_maps.setdefault(cat_id, copy.deepcopy(DEFAULT_DELIVERY_TPL))
            cat_stat = category_delivery_maps.get(cat_id)
            if not cat_stat:
                category_delivery_maps[cat_id][stat_days] = {'post_num': 0, 'wait_num': num}
            else:
                category_delivery_maps[cat_id][stat_days]['wait_num'] += num

        districts = SaleCategory.objects.order_by('parent_cid', 'sort_order')
        districts_values = districts.values('id', 'cid', 'parent_cid', 'name')
        cid_id_maps = dict([(v['cid'], v['id']) for v in districts_values])

        category_node_maps = defaultdict(list)
        for district in districts_values:
            parent_id = cid_id_maps.get(district['parent_cid'], 0)
            print parent_id, type(parent_id)
            category_node_maps[parent_id].append(district)

        category_serial_data = self.recurse_calc_serial_data(
            {'id': 0, 'name':'全部类目' }, category_node_maps, category_delivery_maps)

        return Response({
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'serial_data': category_serial_data,
            })

