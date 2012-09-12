from django.conf.urls.defaults import patterns, include, url
from shopback.orders.views import UserHourlyOrderView,ProductOrderView,RelatedOrderStateView,RefundOrderView
from shopback.base.resources import ChartsResource,BaseResource
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.permissions import IsAuthenticated
from shopback.base.renderers  import ChartJSONRenderer,ChartTemplateRenderer,BaseJsonRenderer
from shopback.orders.renderers import OrderNumPiovtChartHtmlRenderer,ProductOrderTableRenderer,RelatedOrderRenderer,RefundOrderRenderer
from shopback.orders.resources import ChartJsonResource


urlpatterns = patterns('shopback.orders.views',

    url('update/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_interval_trade',name='interval_trade'),

    (r'^ordernum/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$',UserHourlyOrderView.as_view(
        resource=ChartsResource,
        renderers=(ChartJSONRenderer,ChartTemplateRenderer,OrderNumPiovtChartHtmlRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
                       
    (r'^product/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/(?P<num_iid>[^/]+)/$',ProductOrderView.as_view(
        resource=ChartsResource,
        renderers=(ChartJSONRenderer,ChartTemplateRenderer,ProductOrderTableRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
                       
    (r'^related/orders/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/(?P<num_iid>[^/]+)/$',RelatedOrderStateView.as_view(
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
  