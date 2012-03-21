from django.conf.urls.defaults import patterns, include, url
from search.resources  import SearchResource,RankResource
from search.views import ShopsRankView,KeywordsMapItemsRankView,ItemsMapKeywordsRankView,KeywordsMapItemsRankPivotView,ItemsMapKeywordsRankPivotView,ShopMapKeywordsTopTradeView,ShopMapKeywordsTradePivotView
from shopback.orders.views import UserHourlyOrderView
from shopback.base.renderers import JSONRenderer,ChartJSONRenderer,ChartHtmlRenderer,SearchRankHTMLRenderer


urlpatterns = patterns('',

    (r'^taobao/rank/',ShopsRankView.as_view(
        resource=RankResource,
        renderers=(JSONRenderer,SearchRankHTMLRenderer,),
    )),
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
    (r'^trade/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',ShopMapKeywordsTradePivotView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartHtmlRenderer,),
    )),
    (r'^trade/topchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',ShopMapKeywordsTopTradeView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartHtmlRenderer,),
    )),
    (r'^ordernum/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',UserHourlyOrderView.as_view(
        resource=SearchResource,
        renderers=(ChartJSONRenderer,ChartHtmlRenderer,),
    )),

)


  