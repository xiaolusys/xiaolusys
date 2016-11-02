import time
from django.db.models import Avg, Variance, Sum
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from shopapp.collector.models import ProductPageRank, ProductTrade
from common.utils import parse_datetime, format_time, map_int2str


def genProductPeriodChart(nick, keyword, dt_f, dt_t, index):
    rankqueryset = ProductPageRank.objects.filter(nick=nick, keyword=keyword, created__gt=dt_f, created__lt=dt_t) \
        .values('item_id').distinct('item_id')

    if rankqueryset.count() == 0:
        return None

    series = []
    series_option = {'options': {'type': 'spline', 'stacking': False}, 'terms': {}}

    for prod in rankqueryset:
        serie = {
            'options': {
                'source': ProductPageRank.objects.filter
                (keyword=keyword, created__gt=dt_f, created__lt=dt_t, item_id=prod['item_id'])},
            'terms': [{'created' + prod['item_id']: 'created'}, {prod['item_id']: 'rank'}]}
        series.append(serie)
        series_option['terms'].update({'created' + prod['item_id']: [prod['item_id']]})

    productpagerankdata = DataPool(series=series)

    chart_options = {
        'chart': {'renderTo': "container" + str(index)},
        'title': {'text': '%s-%s' % (nick.encode('utf8'), keyword.encode('utf8'))},
        'xAxis': {
            'title': {'text': 'per half hour'},
            'type': 'string',
            'labels': {
                'rotation': -45,
                'align': 'right',
                'style': {'font': 'normal 12px Verdana, sans-serif'}}},
        'yAxis': {
            'title': {'text': 'ranks'},
            'min': 0,
            'minorGridLineWidth': 0,
            'gridLineWidth': 0,
            'alternateGridColor': None,},
        'plotOptions': {
            'spline': {
                'lineWidth': 1, 'states': {'hover': {'lineWidth': 2}},
                'marker': {
                    'enabled': False,
                    'states': {'hover': {'enabled': True, 'symbol': 'cycle', 'radius': 0, 'lineWidth': 1}}},},}
    }

    productpagerankcht = Chart(
        datasource=productpagerankdata,
        series_options=[series_option],
        chart_options=chart_options)

    return productpagerankcht


def genItemKeywordsChart(item_id, dt_f, dt_t, index):
    queryset = ProductPageRank.objects.filter(item_id=item_id, created__gt=dt_f, created__lt=dt_t) \
        .values('keyword').distinct('keyword')

    if queryset.count() == 0:
        return None

    series = []
    series_option = {'options': {'type': 'spline', 'stacking': False}, 'terms': {}}
    for i in xrange(0, queryset.count()):
        serie = {'options': {
            'source': ProductPageRank.objects.filter
            (keyword=queryset[i]['keyword'], created__gt=dt_f, created__lt=dt_t, item_id=item_id)},
            'terms': [{'created' + str(i): 'created'}, {queryset[i]['keyword']: 'rank'}],
        }
        series.append(serie)
        series_option['terms'].update({'created' + str(i): [queryset[i]['keyword']]})

    productpagerankdata = DataPool(series=series)

    def map_date_str2long(*t):
        ts = long(time.mktime(time.strptime(t[0], "%Y-%m-%d %H:%M"))) * 1000
        return (ts,)

    chart_options = {
        'chart': {'renderTo': "container" + str(index)},
        'title': {
            'text': u'\u67e5\u8be2\u5546\u54c1ID\uff1a%s' % (item_id)},
        'xAxis': {
            'title': {'text': 'per half hour'}, 'type': 'string',
            'labels': {'rotation': -45, 'align': 'right', 'style': {'font': 'normal 12px Verdana, sans-serif'}}},
        'yAxis': {
            'title': {'text': 'ranks'},
            'min': 0,
            'minorGridLineWidth': 0,
            'gridLineWidth': 0,
            'alternateGridColor': None,},
        'plotOptions': {
            'spline': {
                'lineWidth': 1, 'states': {'hover': {'lineWidth': 2}},
                'marker': {
                    'enabled': False,
                    'states': {'hover': {'enabled': True, 'symbol': 'cycle', 'radius': 0, 'lineWidth': 1}}},
            },
            # 'pointInterval':3600000,
            # 'pointStart':1330531200
        },
    }

    productpagerankcht = Chart(
        datasource=productpagerankdata,
        series_options=[series_option],
        # x_sortf_mapf_mts=(None,map_date_str2long,True),
        chart_options=chart_options)

    return productpagerankcht


def genPageRankPivotChart(nick, keyword, dt_f, dt_t, index):
    serie = {
        'options': {
            'source': ProductPageRank.objects.filter(nick=nick, keyword=keyword, created__gt=dt_f, created__lt=dt_t),
            'categories': ['month', 'day'],
            'legend_by': 'item_id',
            # 'top_n_per_cat':3
        },
        'terms': {
            'avg_rank': Avg('rank'),
            'variance_rank': {'func': Variance('rank'), 'legend_by': 'item_id'},}
    }

    productpagerankpivotdata = PivotDataPool(series=[serie])

    series_options = [{
        'options': {'type': 'line', 'stacking': False},
        'terms': ['avg_rank', {'variance_rank': {'type': 'column', 'yAxis': 1}}]}, ],

    chart_options = {
        'chart': {'renderTo': "container" + str(index), 'zoomType': 'xy'},
        'title': {'text': '%s-%s' % (nick.encode('utf8'), keyword.encode('utf8'))},
        'xAxis': {
            'title': {'text': 'Month&Day'},
            'labels': {'rotation': -45, 'align': 'right', 'style': {'font': 'normal 12px Verdana, sans-serif'}}},
        'yAxis': [{'title': {'text': 'rank avg'}}, {'title': {'text': 'rank variance'}, 'opposite': True}]
    }

    productpagerankpivcht = PivotChart(
        datasource=productpagerankpivotdata,
        series_options=series_options,
        chart_options=chart_options)

    return productpagerankpivcht


def genItemAvgRankPivotChart(nick, dt_f, dt_t, index):
    serie = {
        'options': {
            'source': ProductPageRank.objects.filter(nick=nick, created__gt=dt_f, created__lt=dt_t),
            'categories': ['month', 'day'],
            'legend_by': 'item_id',
            # 'top_n_per_cat':3
        },
        'terms': {'avg_rank': Avg('rank'),}
    }

    productpagerankpivotdata = PivotDataPool(series=[serie])

    productpagerankpivcht = PivotChart(
        datasource=productpagerankpivotdata,
        series_options=[{'options': {'type': 'line', 'stacking': False}, 'terms': ['avg_rank']}, ],
        chart_options={
            'chart': {'renderTo': "container" + str(index), 'zoomType': 'xy'},
            'title': {'text': '%s' % (nick.encode('utf8'))},
            'xAxis': {
                'title': {'text': 'Month&Day'},
                'labels': {'rotation': -45, 'align': 'right', 'style': {'font': 'normal 12px Verdana, sans-serif'}}},
            'yAxis': [{'title': {'text': 'rank avg'}}]
        }
    )

    return productpagerankpivcht
