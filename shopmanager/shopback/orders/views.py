import time
import datetime
import json
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Avg
from django.template import RequestContext
from django.db.models import Sum
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from auth.utils import parse_datetime,format_time
from shopback.orders.models import Order
from shopback.items.tasks import ORDER_SUCCESS_STATUS


def genHourlyOrdersChart(request,dt_f,dt_t):

    nicks = request.GET.get('nicks',None)
    cat_by = request.GET.get('cat_by','hour')
    pay_type = request.GET.get('type','all')
    xy = request.GET.get('xy','horizontal')

    nicks_list = nicks.split(',')

    queryset = Order.objects.filter(created__gt=dt_f,created__lt=dt_t)\
        .filter(seller_nick__in = nicks_list)

    if pay_type == 'pay':
        queryset = queryset.filter(status__in = ORDER_SUCCESS_STATUS)


    if queryset.count() == 0:
        return HttpResponse('No data for these nick!')

    if xy == 'vertical':
        categories = [cat_by]
    else:
        if cat_by == 'month':
            categories = ['month']
        elif cat_by == 'day':
            categories = ['month','day']
        elif cat_by == 'week':
            categories = ['week']
        else :
            categories = ['month','day','hour']


    series = {'options': {
           'source': queryset,
           'categories': categories,
           'legend_by': 'seller_nick'},
           'terms': {'total_num':Sum('num'),'total_sales':{'func':Sum('total_fee'),'legend_by':'seller_nick'}}}

    ordersdata = PivotDataPool(series=[series])

    series_options =[{'options':{'type': 'column','stacking': True,'yAxis': 0},
                      'terms':['total_num',{'total_sales':{'type':'line','stacking':False,'yAxis':1}}]},]
    ordersdatacht = PivotChart(
            datasource = ordersdata,
            series_options = series_options,
            chart_options =
              { 'chart':{'zoomType': 'xy'},
                'title': {'text': nicks},
                'xAxis': {'title': {'text': 'per %s'%cat_by}},
                'yAxis': [{'title': {'text': 'total num '}},{'title': {'text': 'total sales'},'opposite': True}]})

    params = {'ordersdatacht':ordersdatacht}


    return render_to_response('hourly_ordernumschart.html',params,context_instance=RequestContext(request))
