from django.conf.urls import patterns, include, url
from shopback.orders.views import TimerOrderStatisticsView, ProductOrderView, RelatedOrderStateView, RefundOrderView

# from core.options.resources import ChartsResource,BaseResource
# from core.options.authentication import UserLoggedInAuthentication
# from core.options.permissions import IsAuthenticated
# from core.options.renderers  import ChartJSONRenderer,ChartTemplateRenderer,BaseJsonRenderer
# from shopback.orders.renderers import TimerOrderStatChartRenderer,ProductOrderTableRenderer,RelatedOrderRenderer\
#     ,RefundOrderRenderer
# from shopback.orders.resources import ChartJsonResource,TimeOrderStatResource


urlpatterns = patterns('shopback.orders.views',

                       (r'^ordernum/pivotchart/$', TimerOrderStatisticsView.as_view(
                           # resource=TimeOrderStatResource,
                           # renderers=(ChartJSONRenderer,TimerOrderStatChartRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),

                       (r'^product/pivotchart/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/(?P<num_iid>[^/]+)/$',
                        ProductOrderView.as_view(
                            # resource=ChartsResource,
                            #  renderers=(ChartJSONRenderer,ChartTemplateRenderer,ProductOrderTableRenderer,),
                            # authentication=(UserLoggedInAuthentication,),
                            #  permissions=(IsAuthenticated,)
                        )),

                       (r'^related/orders/$', RelatedOrderStateView.as_view(
                           # resource=BaseResource,
                           # renderers=(RelatedOrderRenderer,BaseJsonRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),

                       (r'^refund/orders/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', RefundOrderView.as_view(
                           # resource=BaseResource,
                           # renderers=(BaseJsonRenderer,RefundOrderRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),

                       )
