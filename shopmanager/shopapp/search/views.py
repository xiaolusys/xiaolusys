# -*- coding: utf-8 -*-
from django.db.models import Avg, Variance,Sum
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from djangorestframework.views import ModelView
from djangorestframework.response import ErrorResponse
from djangorestframework import status
from shopback.items.models import Item
from shopapp.search.models import ProductPageRank,ProductTrade
from shopapp.search.gencharts import genProductPeriodChart,genItemKeywordsChart,genPageRankPivotChart,genItemAvgRankPivotChart
from shopapp.search.crawurldata import getTaoBaoPageRank, getCustomShopsPageRank
from auth.utils import map_int2str

class ShopsRankView(ModelView):
    """ docstring for class ShopsRankView """

    def get(self, request, *args, **kwargs):

        nicks = request.GET.get('nicks', None)
        keywords = request.GET.get('keywords', None)
        page_nums = int(request.GET.get('page_nums', '5'))

        if not nicks and not keywords:
            return ErrorResponse(status.HTTP_404_NOT_FOUND,content="There is no data for these nicks and keywords!")

        nicks = nicks.split(',')
        keywords = keywords.split(',')

        results = getCustomShopsPageRank(nicks, keywords, page_nums)

        rank_result = {"results":results}

        return rank_result

####################################### PageRank Chart views #######################################

class KeywordsMapItemsRankView(ModelView):
    """ docstring for class KeywordsMapItemsRankView """

    def get(self, request, *args, **kwargs):

        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
        nicks = request.GET.get('nicks')
        keywords = request.GET.get('keywords', None)

        nicks_list = nicks.split(',')

        if not keywords:
            keys = request.user.get_profile().craw_keywords
            keywords_list = keys.split(',') if keys else []
        else:
            keywords_list = keywords.split(',')

        page_rank_chts = []

        for keyword in keywords_list:
            for nick in nicks_list:
                index = len(page_rank_chts) + 1
                cht = genProductPeriodChart(nick, keyword, dt_f, dt_t, index)
                if cht:
                    page_rank_chts.append(cht)

        if not page_rank_chts:

            raise ErrorResponse(status.HTTP_404_NOT_FOUND,content="There is no data for this nick!")

        page_rank_queryset = ProductPageRank.objects.filter\
                (nick__in=nicks_list, keyword__in=keywords_list, created__gt=dt_f, created__lt=dt_t)\
                .values('item_id','nick', 'title').distinct('item_id')

        items_dict = {}
        for item in  page_rank_queryset:
            item_dict = {}
            item_dict['title'] = item['title']
            item_dict['nick']  = item['nick']
            try:
                prod = Item.objects.get(num_iid=item['item_id'])
                item_dict['pic_url'] = prod.pic_url
            except:
                pass
            items_dict[str(item['item_id'])] = item_dict

        chart_data = {"charts":page_rank_chts,"item_dict":items_dict}

        return chart_data



class ItemsMapKeywordsRankView(ModelView):
    """ docstring for class ItemsMapKeywordsRankView """

    def get(self, request, *args, **kwargs):

        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
        item_ids = request.GET.get('item_ids')
        item_ids = item_ids.split(',')

        page_rank_chts = []

        for item_id in item_ids:
            index = len(page_rank_chts) + 1
            cht = genItemKeywordsChart(item_id, dt_f, dt_t, index)
            if cht:
                page_rank_chts.append(cht)

        if not page_rank_chts:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND,content="item_ids is not avalible.")

        page_rank_queryset = ProductPageRank.objects.filter(item_id__in = item_ids)\
            .values('item_id', 'nick', 'title').distinct('item_id')

        items_dict = {}
        for item in  page_rank_queryset:
            item_dict = {}
            item_dict['title'] = item['title']
            item_dict['nick']  = item['nick']
            try:
                prod = Item.objects.get(num_iid=item['item_id'])
                item_dict['pic_url'] = prod.pic_url
            except:
                pass
            items_dict[str(item['item_id'])] = item_dict

        chart_data = {"charts":page_rank_chts,"item_dict":items_dict}

        return chart_data

####################################### PageRank PivotChart views #######################################

class KeywordsMapItemsRankPivotView(ModelView):
    """ docstring for class ItemsMapKeywordsRankView """

    def get(self, request, *args, **kwargs):

        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
        nicks = request.GET.get('nicks')
        keywords = request.GET.get('keywords', None)

        nicks_list = nicks.split(',')
        if not keywords:
            keys = request.user.get_profile().craw_keywords
            keywords_list = keys.split(',') if keys else []
        else:
            keywords_list = keywords.split(',')

        page_rank_chts = []

        for keyword in keywords_list:
            for nick in nicks_list:
                index = len(page_rank_chts) + 1
                cht = genPageRankPivotChart(nick, keyword, dt_f, dt_t, index)
                if cht:
                    page_rank_chts.append(cht)

        if not page_rank_chts:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND,content="nick is not avalible under this keyword.")

        page_rank_queryset = ProductPageRank.objects.filter\
                (nick__in=nicks_list, keyword__in=keywords_list, created__gt=dt_f, created__lt=dt_t)\
                .values('item_id', 'nick', 'title').distinct('item_id')

        items_dict = {}
        for item in  page_rank_queryset:
            item_dict = {}
            item_dict['title'] = item['title']
            item_dict['nick']  = item['nick']
            try:
                prod = Item.objects.get(num_iid=item['item_id'])
                item_dict['pic_url'] = prod.pic_url
            except:
                pass
            items_dict[str(item['item_id'])] = item_dict

        chart_data = {"charts":page_rank_chts,"item_dict":items_dict}

        return chart_data


class ItemsMapKeywordsRankPivotView(ModelView):
    """ docstring for class ItemsMapKeywordsRankView """

    def get(self, request, *args, **kwargs):

        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
        nicks = request.GET.get('nicks')
        nicks_list = nicks.split(',')

        page_rank_chts = []

        for nick in nicks_list:
            index = len(page_rank_chts) + 1
            cht = genItemAvgRankPivotChart(nick,dt_f, dt_t,index)
            if cht:
                page_rank_chts.append(cht)

        if not page_rank_chts:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND,content="nick is not avalible under this keyword.")

        page_rank_queryset = ProductPageRank.objects.filter\
                (nick__in=nicks_list,created__gt=dt_f, created__lt=dt_t)\
                   .values('item_id', 'nick', 'title').distinct('item_id')

        items_dict = {}
        for item in  page_rank_queryset:
            item_dict = {}
            item_dict['title'] = item['title']
            item_dict['nick']  = item['nick']
            try:
                prod = Item.objects.get(num_iid=item['item_id'])
                item_dict['pic_url'] = prod.pic_url
            except:
                pass
            items_dict[str(item['item_id'])] = item_dict

        chart_data = {"charts":page_rank_chts,"item_dict":items_dict}

        return chart_data


####################################### Trade  views #######################################


class ShopMapKeywordsTradePivotView(ModelView):
    """ docstring for class ShopMapKeywordsTradeView """

    def get(self, request, *args, **kwargs):

        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
        nicks = request.GET.get('nicks',None)
        cat_by = request.GET.get('cat_by','hour')
        xy = request.GET.get('xy','horizontal')

        nicks_list = nicks.split(',')

        prod_trade_queryset = ProductTrade.objects.filter(trade_at__gte=dt_f,trade_at__lt=dt_t)\
            .filter(nick__in = nicks_list)

        if prod_trade_queryset.count() == 0:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND,content="nick is not avalible under this keyword.")


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
            'options': {'source': prod_trade_queryset,'categories': categories,'legend_by': 'nick'},
            'terms': {'total_num':Sum('num'),'total_sales':{'func':Sum('price'),'legend_by':'nick'}}
        }

        ordersdata = PivotDataPool(series=[series],sortf_mapf_mts=(None,map_int2str,True))

        series_options =[{
            'options':{'type': 'column','stacking': True,'yAxis': 0},
            'terms':['total_num',{'total_sales':{'type':'line','stacking':False,'yAxis':1}}]},]

        chart_options = {
            'chart':{'zoomType': 'xy','renderTo': "container1"},
            'title': {'text': nicks},
            'xAxis': {'title': {'text': 'per %s'%(cat_by)},
                      'labels':{'rotation': -45,'align':'right','style': {'font': 'normal 12px Verdana, sans-serif'}}},
            'yAxis': [{'title': {'text': 'total num '}},{'title': {'text': 'total sales'},'opposite': True}]}

        orders_data_cht = PivotChart(
                datasource = ordersdata,
                series_options = series_options,
                chart_options = chart_options)

        chart_data = {"charts":[orders_data_cht]}

        return chart_data


class ShopMapKeywordsTopTradeView(ModelView):
    """ docstring for class ShopMapKeywordsTradeView """

    def get(self, request, *args, **kwargs):

        dt_f = kwargs.get('dt_f')
        dt_t = kwargs.get('dt_t')
        seller_num = int(request.GET.get('seller_num',20))
        type = request.GET.get('sort_by','total_nums')

        queryset = ProductTrade.objects.filter(trade_at__gte=dt_f,trade_at__lt=dt_t)

        if queryset.count() == 0:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND,content="No data for these nick!")

        series = {
            'options': {'source': queryset,'categories': ['user_id',]},
            'terms': {'total_nums':Sum('num'),'total_sales':{'func':Sum('price')},},
        }

        def map_id2nick(*t):
            key = t[0][0]
            nick = ProductTrade.objects.filter(user_id=key)[0].nick
            return (nick,)

        ordersdata = PivotDataPool(series=[series],top_n=seller_num,
                                   top_n_term=type,pareto_term=type,sortf_mapf_mts=(None,map_id2nick,True))

        series_options =[{
            'options':{'type': 'column','yAxis': 0},
            'terms':['total_nums',{'total_sales':{'type':'column','stacking':False,'yAxis':1}}]},]

        chart_options = {
            'chart':{'zoomType': 'xy','renderTo': "container1"},
            'title': {'text':u'\u9500\u552e\u91cf\u53ca\u9500\u552e\u989d\u6392\u524d%s\u7684\u5356\u5bb6\u6570\u636e'%seller_num},
            'xAxis': {'title': {'text': 'total nums & sales'},
                    'labels':{'rotation': -45,'align':'right','style': {'font': 'normal 12px Verdana, sans-serif'}}},
            'yAxis': [{'title': {'text': 'total nums '}},{'title': {'text': 'total sales'},'opposite': True},],}

        orders_data_cht = PivotChart(
                datasource = ordersdata,
                series_options = series_options,
                chart_options =chart_options )

        chart_data = {"charts":[orders_data_cht]}

        return chart_data
  
