from django.conf.urls.defaults import patterns, include, url
from shopback.orders.views import TimerOrderStatisticsView,ProductOrderView,RelatedOrderStateView,RefundOrderView
from shopback.base.resources import ChartsResource,BaseResource
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.permissions import IsAuthenticated
from shopback.base.renderers  import ChartJSONRenderer,ChartTemplateRenderer,BaseJsonRenderer
from shopback.orders.renderers import TimerOrderStatChartRenderer,ProductOrderTableRenderer,RelatedOrderRenderer\
    ,RefundOrderRenderer
from shopback.orders.resources import ChartJsonResource,TimeOrderStatResource


urlpatterns = patterns('shopback.orders.views',


    (r'^ordernum/pivotchart/$',TimerOrderStatisticsView.as_view(
        resource=TimeOrderStatResource,
        renderers=(ChartJSONRenderer,TimerOrderStatChartRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
                       
    (r'^product/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/(?P<num_iid>[^/]+)/$',ProductOrderView.as_view(
        resource=ChartsResource,
        renderers=(ChartJSONRenderer,ChartTemplateRenderer,ProductOrderTableRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
                       
    (r'^related/orders/$',RelatedOrderStateView.as_view(
        resource=BaseResource,
        renderers=(RelatedOrderRenderer,BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    
    (r'^refund/orders/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',RefundOrderView.as_view(
        resource=BaseResource,
        renderers=(BaseJsonRenderer,RefundOrderRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
                       
)
  