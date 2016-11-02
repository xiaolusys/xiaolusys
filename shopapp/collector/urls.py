from django.conf.urls import patterns, include, url
# from shopapp.collector.resources  import RankResource
from shopapp.collector.views import ShopsRankView, KeywordsMapItemsRankView, ItemsMapKeywordsRankView, \
    KeywordsMapItemsRankPivotView, ItemsMapKeywordsRankPivotView, ShopMapKeywordsTopTradeView, \
    ShopMapKeywordsTradePivotView

# from shopapp.collector.renderers import JSONRenderer,SearchRankHTMLRenderer,RankChartHtmlRenderer\
#     ,KeysChartHtmlRenderer,RankPivotChartHtmlRenderer,AvgRankPivotChartHtmlRenderer,TradePivotChartHtmlRenderer,TradeTopChartHtmlRenderer
# from core.options.resources import ChartsResource
# from core.options.renderers  import ChartJSONRenderer,ChartTemplateRenderer
# from core.options.authentication import UserLoggedInAuthentication
# from core.options.permissions import IsAuthenticated

__author__ = 'meixqhi'

urlpatterns = patterns('',

                       (r'^taobao/rank/', ShopsRankView.as_view(
                           # resource=RankResource,
                           # renderers=(JSONRenderer,SearchRankHTMLRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),
                       (r'^rank/chart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', KeywordsMapItemsRankView.as_view(
                           # resource=ChartsResource,
                           # renderers=(ChartJSONRenderer,ChartTemplateRenderer,RankChartHtmlRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),
                       (r'^keys/chart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', ItemsMapKeywordsRankView.as_view(
                           # resource=ChartsResource,
                           # renderers=(ChartJSONRenderer,ChartTemplateRenderer,KeysChartHtmlRenderer),
                           #  authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),
                       (r'^rank/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', KeywordsMapItemsRankPivotView.as_view(
                           # resource=ChartsResource,
                           # renderers=(ChartJSONRenderer,ChartTemplateRenderer,RankPivotChartHtmlRenderer,),
                           #  authentication=(UserLoggedInAuthentication,),
                           #  permissions=(IsAuthenticated,)
                       )),
                       (r'^avgrank/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', ItemsMapKeywordsRankPivotView.as_view(
                           #  resource=ChartsResource,
                           # renderers=(ChartJSONRenderer,ChartTemplateRenderer,AvgRankPivotChartHtmlRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),
                       (r'^trade/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', ShopMapKeywordsTradePivotView.as_view(
                           # resource=ChartsResource,
                           # renderers=(ChartJSONRenderer,ChartTemplateRenderer,TradePivotChartHtmlRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           #  permissions=(IsAuthenticated,)
                       )),
                       (r'^trade/topchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', ShopMapKeywordsTopTradeView.as_view(
                           #         resource=ChartsResource,
                           #         renderers=(ChartJSONRenderer,ChartTemplateRenderer,TradeTopChartHtmlRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),

                       )
