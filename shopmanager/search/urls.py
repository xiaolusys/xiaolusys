from django.conf.urls.defaults import patterns, include, url
from search.resources  import SearchResource
from search.views import KeywordsMapItemsRankView,ItemsMapKeywordsRankView,KeywordsMapItemsRankPivotView,ItemsMapKeywordsRankPivotView,ShopMapKeywordsTradeView,ShopMapKeywordsTradePivotView
from shopback.orders.views import UserHourlyOrderView
from shopback.base.renderers import ChartJSONRenderer,ChartHtmlRenderer


urlpatterns = patterns('',

    (r'^taobao/rank/','search.views.getShopsRank'),

    (r'^rank/chart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',KeywordsMapItemsRankView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartHtmlRenderer,),
    )),
    (r'^keys/chart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',ItemsMapKeywordsRankView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartHtmlRenderer,),
    )),
    (r'^rank/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',KeywordsMapItemsRankPivotView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartHtmlRenderer,),
    )),
    (r'^avgrank/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',ItemsMapKeywordsRankPivotView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartHtmlRenderer,),
    )),
    (r'^avgrank/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',ShopMapKeywordsTradeView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartHtmlRenderer,),
    )),
    (r'^trade/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',ShopMapKeywordsTradePivotView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartHtmlRenderer,),
    )),
    (r'^ordernum/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',UserHourlyOrderView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartHtmlRenderer,),
    )),

)


  