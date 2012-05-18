import datetime
import json
from django.http import HttpResponse
from django.db.models import Sum,Count,Avg
from djangorestframework.response import ErrorResponse
from djangorestframework import status
from djangorestframework.views import ModelView
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from auth import staff_requried
from auth.utils import parse_datetime,parse_date,format_time,map_int2str
from shopback.orders.models import Order,Trade,ORDER_SUCCESS_STATUS,ORDER_FINISH_STATUS
from shopback.orders.tasks import updateAllUserOrdersAmountTask,updateAllUserDailyIncrementOrders


class UserHourlyOrderView(ModelView):
    """ docstring for class ShopMapKeywordsTradeView """

    def get(self, request, *args, **kwargs):

        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
        nicks = request.GET.get('nicks',None)
        cat_by = request.GET.get('cat_by','hour')
        pay_type = request.GET.get('type','all')
        xy = request.GET.get('xy','horizontal')
        base = request.GET.get('base','created')

        nicks_list = nicks.split(',')

        dt_f = parse_date(dt_f)
        dt_t = parse_date(dt_t)+datetime.timedelta(1,0,0)

        queryset = Trade.objects.filter(seller_nick__in = nicks_list)
        if base == 'consign':
            queryset = queryset.filter(consign_time__gte=dt_f,consign_time__lt=dt_t)
        elif base == 'modified':
            queryset = queryset.filter(modified__gte=dt_f,modified__lt=dt_t)
        else:
            queryset = queryset.filter(created__gte=dt_f,created__lt=dt_t)

        if pay_type == 'pay':
            queryset = queryset.filter(status__in = ORDER_SUCCESS_STATUS)
        elif pay_type == 'finish':
            queryset = queryset.filter(status = ORDER_FINISH_STATUS)

        if queryset.count() == 0:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND,content="No data for these nick!")

        if xy == 'vertical':
            categories = [cat_by]
        else:
            if cat_by == 'year':
                categories = ['year']
            elif cat_by == 'month':
                categories = ['year','month']
            elif cat_by == 'day':
                categories = ['year','month','day']
            elif cat_by == 'week':
                categories = ['year','week']
            else :
                categories = ['year','month','day','hour']

        series = {
            'options': {'source': queryset,'categories': categories,'legend_by': 'seller_nick'},
            'terms': {
                'total_trades':{'func':Count('id'),'legend_by':'seller_nick'},
                'total_sales':{'func':Sum('payment'),'legend_by':'seller_nick'},
                'post_fees':{'func':Sum('post_fee'),'legend_by':'seller_nick'},
                'commission_fees':{'func':Sum('commission_fee'),'legend_by':'seller_nick'},
            }

        }

        ordersdata = PivotDataPool(series=[series],sortf_mapf_mts=(None,map_int2str,True))

        series_options =[{
            'options':{'type': 'column','stacking': True,'yAxis': 0},
            'terms':['total_trades',
                     {'total_sales':{'type':'line','stacking':False,'yAxis':1}},
                     {'post_fees':{'type':'line','stacking':False,'yAxis':1}},
                     {'commission_fees':{'type':'line','stacking':False,'yAxis':1}},
            ]},
        ]

        chart_options = {
            'chart':{'zoomType': 'xy','renderTo': "container1"},
            'title': {'text': nicks},
            'xAxis': {'title': {'text': 'per %s'%(cat_by)},
                      'labels':{'rotation': -45,'align':'right','style': {'font': 'normal 12px Verdana, sans-serif'}}},
            'yAxis': [{'title': {'text': u'\u8ba2\u5355\u6570'}},
                      {'title': {'text': u'\u4ea4\u6613\u989d'},'opposite': True},
                      {'title': {'text': u'\u90ae\u8d39'},'opposite': True},
                      {'title': {'text': u'\u4f63\u91d1'},'opposite': True}
            ]
        }

        orders_data_cht = PivotChart(
                datasource = ordersdata,
                series_options = series_options,
                chart_options = chart_options )

        chart_data = {"charts":[orders_data_cht]}

        return chart_data


@staff_requried(login_url='/admin/login/')
def update_finish_trade_amount(request,dt_f,dt_t):

    dt_f = parse_date(dt_f)
    dt_t = parse_date(dt_t)

    order_amount_task = updateAllUserOrdersAmountTask.delay(dt_f,dt_t)

    ret_params = {'task_id':order_amount_task.task_id}

    return HttpResponse(json.dumps(ret_params),mimetype='application/json')




@staff_requried(login_url='/admin/login/')
def update_increment_trade(request,dt_f,dt_t):

    dt_f = parse_date(dt_f)
    dt_t = parse_date(dt_t)

    increment_task = updateAllUserDailyIncrementOrders.delay(dt_f,dt_t)

    ret_params = {'task_id':increment_task.task_id}

    return HttpResponse(json.dumps(ret_params),mimetype='application/json')

