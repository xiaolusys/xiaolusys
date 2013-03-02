#-*- coding:utf8 -*-
import datetime
import json
from django.http import HttpResponse
from django.db.models import Sum,Count,Avg
from django.db import connection,transaction
from djangorestframework.response import ErrorResponse
from djangorestframework import status
from djangorestframework.views import ModelView
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from auth import staff_requried,apis
from auth.utils import parse_datetime,parse_date,format_time,map_int2str,format_datetime
from shopback.items.models import Item,OnlineProduct,OnlineProductSku
from shopback.orders.models import Order,Trade
from shopback import paramconfig as pcfg

class UserHourlyOrderView(ModelView):
    """ docstring for class UserHourlyOrderView """

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
            queryset = queryset.filter(status__in = pcfg.ORDER_SUCCESS_STATUS)
        elif pay_type == 'finish':
            queryset = queryset.filter(status = pcfg.ORDER_FINISH_STATUS)

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
            'options': {'source': queryset,'categories': categories,'legend_by':'seller_nick'},
            'terms': {
                'total_trades':{'func':Count('id'),'legend_by':'seller_nick'},
                'total_sales':{'func':Sum('payment'),'legend_by':'seller_nick'},
                'post_fees':{'func':Sum('post_fee'),'legend_by':'seller_nick'},
                'commission_fees':{'func':Sum('commission_fee'),'legend_by':'seller_nick'},
                'buyer_obtain_point_fees':{'func':Sum('buyer_obtain_point_fee'),'legend_by':'seller_nick'},
            }

        }

        ordersdata = PivotDataPool(series=[series],sortf_mapf_mts=(None,map_int2str,True))

        series_options =[{
            'options':{'type':'column','stacking':True,'yAxis':0},
            'terms':['total_trades',
                     {'total_sales':{'type':'line','stacking':False,'yAxis':1}},
                     {'post_fees':{'type':'line','stacking':False,'yAxis':1}},
                     {'commission_fees':{'type':'area','stacking':False,'yAxis':1}},
                     {'buyer_obtain_point_fees':{'type':'column','stacking':False,'yAxis':4}},
            ]},
        ]

        chart_options = {
            'chart':{'zoomType': 'xy','renderTo': "container1"},
            'title': {'text': nicks},
            'xAxis': {'title': {'text': 'per %s'%(cat_by)},
                      'labels':{'rotation': 45,'align':'right','style': {'font': 'normal 12px Verdana, sansserif'}}},
            'yAxis': [{'title': {'text': u'\u8ba2\u5355\u6570'}},
                      {'title': {'text': u'\u4ea4\u6613\u989d'},'opposite': True},
                      {'title': {'text': u'\u90ae\u8d39'},'opposite': True},
                      {'title': {'text': u'\u4f63\u91d1'},'opposite': True},
                      {'title': {'text': u'\u79ef\u5206'},},
            ]
        }

        orders_data_cht = PivotChart(
                datasource = ordersdata,
                series_options = series_options,
                chart_options = chart_options )

        chart_data = {"charts":[orders_data_cht]}

        return chart_data

class ProductOrderView(ModelView):
    """ docstring for class ProductOrderView """

    def get(self, request, *args, **kwargs):
        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
        num_iid = kwargs.get('num_iid')
        nicks = request.GET.get('nicks',None)
        cat_by = request.GET.get('cat_by','hour')
        pay_type = request.GET.get('type','all')
        xy = request.GET.get('xy','horizontal')
        base = request.GET.get('base','created')
        
        nicks_list = nicks.split(',')
        
        dt_f = parse_date(dt_f)
        dt_t = parse_date(dt_t)+datetime.timedelta(1,0,0)
        
        try:
            item = Item.objects.get(num_iid=num_iid)
        except Item.DoesNotExist:    
            outer_id = num_iid
        else:
            outer_id = item.outer_id
        
        try:
            product = OnlineProduct.objects.get()
        except:    
            product_name = '商品名未知'
        else:
            product_name = product.name
 
        queryset = Order.objects.filter(seller_nick__in = nicks_list,outer_id=outer_id)
        if base == 'consign':
            queryset = queryset.filter(trade__consign_time__gte=dt_f,trade__consign_time__lt=dt_t)
        else:
            queryset = queryset.filter(trade__created__gte=dt_f,trade__created__lt=dt_t)
           
        if pay_type == 'pay':
            queryset = queryset.filter(status__in = pcfg.ORDER_SUCCESS_STATUS)
        elif pay_type == 'finish':
            queryset = queryset.filter(status = pcfg.ORDER_FINISH_STATUS)
             
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
            'options': {'source': queryset,'categories': categories,'legend_by':['seller_nick','outer_sku_id']},
            'terms': {
                'sku_nums':{'func':Sum('num'),'legend_by':['seller_nick','outer_sku_id']},
            }

        }

        ordersdata = PivotDataPool(series=[series],sortf_mapf_mts=(None,map_int2str,True))

        series_options =[{
            'options':{'type':'area','stacking':True,'yAxis':0},
            'terms':['sku_nums',]},
        ]

        chart_options = {
            'chart':{'zoomType': 'xy','renderTo': "container1"},
            'title': {'text': product_name},
            'xAxis': {'title': {'text': 'per %s'%(cat_by)},
                      'labels':{'rotation': 45,'align':'right','style': {'font': 'normal 12px Verdana, sansserif'}}},
            'yAxis': [{'title': {'text': u'\u9500\u552e\u6570\u91cf'}},]
        }

        orders_data_cht = PivotChart(
                datasource = ordersdata,
                series_options = series_options,
                chart_options = chart_options )
        
        product_sku = OnlineProductSku.objects.filter(product=outer_id)
        sku_list = []
        for psku in product_sku:
            sku = {}
            sku['sku_outer_id'] = psku.outer_id
            sku['sku_values'] = psku.properties_values
            sku_list.append(sku)

        chart_data = {"charts":[orders_data_cht],'skus':sku_list}
        
        if self.request.REQUEST.get('format') == 'table':
            
            class ChartEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, (Chart,PivotChart)):
                        return obj.hcoptions #Serializer().serialize
                    return DjangoJSONEncoder.default(self, obj)
            chart_data = json.loads(json.dumps(chart_data, cls=ChartEncoder))

        return chart_data
  
   
   
class RelatedOrderStateView(ModelView):
    """ docstring for class RelatedOrderStateView """
    
    def get(self, request, *args, **kwargs):
        
        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
        num_iid = kwargs.get('num_iid')
        outer_sku_ids = request.REQUEST.get('sku_ids')
        limit  = request.REQUEST.get('limit',10) 
        
        try:
            item = Item.objects.get(num_iid=num_iid)
        except Item.DoesNotExist:    
            outer_id = num_iid
        else:
            outer_id = item.outer_id
        
        dt_f = datetime.datetime.strptime(dt_f,'%Y-%m-%d')
        dt_t = datetime.datetime.strptime(dt_t,'%Y-%m-%d')
        
        merge_orders = Order.objects.filter(outer_id=outer_id,created__gte=dt_f,created__lte=dt_t).exclude(
                    status__in=(pcfg.TRADE_CLOSED_BY_TAOBAO,pcfg.WAIT_BUYER_PAY,pcfg.TRADE_CLOSED))
        if outer_sku_ids:
            sku_ids = outer_sku_ids.split(',')
            merge_orders = merge_orders.filter(outer_sku_id__in=sku_ids)
        
        buyer_set = set()
        relative_orders_dict = {} 
        for order in merge_orders:
            buyer_nick = order.buyer_nick
            try:
                buyer_set.remove(buyer_nick)
            except:
                buyer_set.add(buyer_nick)
                relat_orders = Order.objects.filter(buyer_nick=buyer_nick,created__gte=dt_f,created__lte=dt_t).exclude(
                    status__in=(pcfg.TRADE_CLOSED_BY_TAOBAO,pcfg.WAIT_BUYER_PAY,pcfg.TRADE_CLOSED))
                for o in relat_orders:
                    relat_outer_id = o.outer_id
                    if relative_orders_dict.has_key(relat_outer_id):
                        relative_orders_dict[relat_outer_id]['cnum'] += o.num
                    else:
                        relative_orders_dict[relat_outer_id] = {'pic_path':o.pic_path,'title':o.title,'cnum':o.num}
            else:
                buyer_set.add(buyer_nick)
            
        relat_order_list = sorted(relative_orders_dict.items(),key=lambda d:d[1]['cnum'],reverse=True)  
        order_item_list  = []
        for order in relat_order_list[0:limit]:
            order_item = []
            order_item.append(order[0])
            order_item.append(order[1]['pic_path'])
            order_item.append(order[1]['title'])
            order_item.append(order[1]['cnum'])
            order_item_list.append(order_item)

        return order_item_list
        
        
        #    def gen_query_sql(self,outer_id,outer_sku_ids,dt_f,dt_t,limit):
        #        sql_list = []
        #        sql_list.append("select sob.outer_id,sob.pic_path,sob.title ,count(sob.outer_id) cnum from shop_orders_order soa ")
        #        sql_list.append("left join shop_orders_order sob on soa.buyer_nick=sob.buyer_nick where soa.outer_id='%s' "%outer_id)
        #        if outer_sku_ids:
        #            sql_list.append(" and soa.outer_sku_id in (%s)"%outer_sku_ids)
        #            
        #        sql_list.append(" and sob.status not in ('TRADE_CLOSED_BY_TAOBAO','WAIT_BUYER_PAY','TRADE_CLOSED') ")
        #        sql_list.append(" and sob.created >'%s' and sob.created<'%s' group by sob.outer_id order by cnum desc limit %d;"%(dt_f,dt_t,limit))
        #        return ''.join(sql_list)


class RefundOrderView(ModelView):
    """ docstring for class RefundOrderView """
    
    def get(self, request, *args, **kwargs):
        
        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
        
        dt_f = parse_date(dt_f)
        dt_t = parse_date(dt_t)+datetime.timedelta(1,0,0)

        queryset = Order.objects.filter(created__gte=dt_f,created__lte=dt_t,refund_status=pcfg.REFUND_SUCCESS)
        total_refund_num = queryset.count()
        
        full_refunds_num = 0
        part_refunds_num = 0
        consign_full_refunds_num = 0
        consign_part_refunds_num = 0
        refund_orders = queryset.values_list('trade',flat=True).distinct('trade')
        for trade in refund_orders:
            trade  = Trade.objects.get(id=trade)
            refunds = Order.objects.filter(trade=trade).exclude(refund_status=pcfg.REFUND_SUCCESS)
            if refunds.count()>0:
                part_refunds_num += 1
                if trade.consign_time:
                    consign_part_refunds_num += 1
            else:
                full_refunds_num += 1
                if trade.consign_time:
                    consign_full_refunds_num += 1
            
            
        cursor = connection.cursor()
        cursor.execute(self.gen_refund_sql(format_datetime(dt_f),format_datetime(dt_t)))
        result = cursor.fetchall()
        
        ret_dict = {
                    'result':result,
                    'total_refunds':total_refund_num,
                    'full_refunds':full_refunds_num,
                    'part_refunds':part_refunds_num,
                    'consign_part_refunds':consign_part_refunds_num,
                    'consign_full_refunds':consign_full_refunds_num,
        }
        
        return ret_dict
    
    def gen_refund_sql(self,dt_f,dt_t):
        sql_list = []
        sql_list.append("select outer_id,outer_sku_id,pic_path,title,count(outer_sku_id) num from shop_orders_order ")
        sql_list.append(" where created >='%s' and created<='%s' and consign_time is not NULL and refund_status='SUCCESS' "%(dt_f,dt_t))
        sql_list.append('group by outer_id,outer_sku_id order by outer_id desc,num desc;')
        return ' '.join(sql_list)
        












