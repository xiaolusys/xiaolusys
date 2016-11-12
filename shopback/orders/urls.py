from django.conf.urls import include, url
from shopback.orders.views import *

# from core.options.resources import ChartsResource,BaseResource
# from core.options.authentication import UserLoggedInAuthentication
# from core.options.permissions import IsAuthenticated
# from core.options.renderers  import ChartJSONRenderer,ChartTemplateRenderer,BaseJsonRenderer
# from shopback.orders.renderers import TimerOrderStatChartRenderer,ProductOrderTableRenderer,RelatedOrderRenderer\
#     ,RefundOrderRenderer
# from shopback.orders.resources import ChartJsonResource,TimeOrderStatResource


urlpatterns = [
    url(r'^ordernum/pivotchart/$', TimerOrderStatisticsView.as_view(
       # resource=TimeOrderStatResource,
       # renderers=(ChartJSONRenderer,TimerOrderStatChartRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
        )),
    url(r'^product/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/(?P<num_iid>[^/]+)/$',
        ProductOrderView.as_view(
            # resource=ChartsResource,
            #  renderers=(ChartJSONRenderer,ChartTemplateRenderer,ProductOrderTableRenderer,),
            # authentication=(UserLoggedInAuthentication,),
            #  permissions=(IsAuthenticated,)
        )),
    url(r'^related/orders/$', RelatedOrderStateView.as_view(
       # resource=BaseResource,
       # renderers=(RelatedOrderRenderer,BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
        )),
    url(r'^refund/orders/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', RefundOrderView.as_view(
       # resource=BaseResource,
       # renderers=(BaseJsonRenderer,RefundOrderRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
        )),
]
