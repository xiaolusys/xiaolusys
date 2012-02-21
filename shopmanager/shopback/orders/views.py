import time
import datetime
import json
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Avg
from django.template import RequestContext
from django.db.models import Sum,Q
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from auth.utils import parse_datetime,format_time
from shopback.orders.models import Order


def genHourlyOrdersChart(request,dt_f,dt_t):

    nicks = request.GET.get('nicks',None)
    nicks_list = nicks.split(',')

    queryset = Order.objects.filter(created__gt=dt_f,created__lt=dt_t)\
        .filter(seller_nick__in = nicks_list)

    if queryset.count() == 0:
        return HttpResponse('No data for these nick!')

    series = {'options': {
           'source': queryset,
           'categories': ['month','day','hour'],
           'legend_by': 'seller_nick'},
           'terms': {'total_num':Sum('num')}}

    ordersdata = PivotDataPool(series=[series])

    series_option ={'options':{'type': 'column','stacking': True,'xAxis': 0,'yAxis': 0},'terms':['total_num']}
    ordersdatacht = PivotChart(
            datasource = ordersdata,
            series_options = [series_option],
            chart_options =
              {'title': {
                   'text': nicks},
               'xAxis': {
                    'title': {
                       'text': 'per hour'}},
               'yAxis': {
                    'title': {
                       'text': 'total sales'}}})

    params = {'ordersdatacht':ordersdatacht}


    return render_to_response('hourly_ordernumschart.html',params,context_instance=RequestContext(request))