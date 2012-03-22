from django.conf.urls.defaults import patterns, include, url
from search.resources  import SearchResource,RankResource
from search.views import ShopsRankView,KeywordsMapItemsRankView,ItemsMapKeywordsRankView,KeywordsMapItemsRankPivotView,ItemsMapKeywordsRankPivotView,ShopMapKeywordsTopTradeView,ShopMapKeywordsTradePivotView
from shopback.orders.views import UserHourlyOrderView
from search.renderers import JSONRenderer,ChartJSONRenderer,SearchRankHTMLRenderer,ChartTemplateRenderer,RankChartHtmlRenderer\
    ,KeysChartHtmlRenderer,RankPivotChartHtmlRenderer,AvgRankPivotChartHtmlRenderer,TradePivotChartHtmlRenderer,TradeTopChartHtmlRenderer,OrderNumPiovtChartHtmlRenderer
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.permissions import IsAuthenticated


urlpatterns = patterns('',

    (r'^taobao/rank/',ShopsRankView.as_view(
        resource=RankResource,
        renderers=(JSONRenderer,SearchRankHTMLRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^rank/chart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',KeywordsMapItemsRankView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartTemplateRenderer,RankChartHtmlRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^keys/chart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',ItemsMapKeywordsRankView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartTemplateRenderer,KeysChartHtmlRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^rank/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',KeywordsMapItemsRankPivotView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartTemplateRenderer,RankPivotChartHtmlRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^avgrank/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',ItemsMapKeywordsRankPivotView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartTemplateRenderer,AvgRankPivotChartHtmlRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^trade/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',ShopMapKeywordsTradePivotView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartTemplateRenderer,TradePivotChartHtmlRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^trade/topchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',ShopMapKeywordsTopTradeView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartTemplateRenderer,TradeTopChartHtmlRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^ordernum/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',UserHourlyOrderView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartTemplateRenderer,OrderNumPiovtChartHtmlRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),

)


  