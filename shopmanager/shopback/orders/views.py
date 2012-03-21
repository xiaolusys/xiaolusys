import time
import datetime
from django.db.models import Avg
from django.db.models import Sum
from djangorestframework.response import ErrorResponse
from djangorestframework import status
from djangorestframework.views import ModelView
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from auth.utils import parse_datetime,format_time,map_int2str
from shopback.orders.models import Order
from shopback.items.tasks import ORDER_SUCCESS_STATUS


class UserHourlyOrderView(ModelView):
    """ docstring for class ShopMapKeywordsTradeView """

    def get(self, request, *args, **kwargs):

        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
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
            raise ErrorResponse(status.HTTP_404_NOT_FOUND,content="No data for these nick!")

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


        series = {
            'options': {'source': queryset,'categories': categories,'legend_by': 'seller_nick'},
            'terms': {'total_num':Sum('num'),'total_sales':{'func':Sum('total_fee'),'legend_by':'seller_nick'}}}


        ordersdata = PivotDataPool(series=[series],sortf_mapf_mts=(None,map_int2str,True))

        series_options =[{
            'options':{'type': 'column','stacking': True,'yAxis': 0},
            'terms':['total_num',{'total_sales':{'type':'line','stacking':False,'yAxis':1}}]},]

        chart_options = {
            'chart':{'zoomType': 'xy','renderTo': "container1"},
            'title': {'text': nicks},
            'xAxis': {'title': {'text': 'per %s(%s)'%(cat_by,u'\u4e0d\u5305\u542b\u90ae\u8d39')},
                      'labels':{'rotation': -45,'align':'right','style': {'font': 'normal 12px Verdana, sans-serif'}}},
            'yAxis': [{'title': {'text': 'total num '}},{'title': {'text': 'total sales'},'opposite': True}]}

        orders_data_cht = PivotChart(
                datasource = ordersdata,
                series_options = series_options,
                chart_options =chart_options )

        chart_data = {"charts":[orders_data_cht]}

        return chart_data

