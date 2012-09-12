from django.conf.urls.defaults import patterns, include, url
from shopback.orders.views import UserHourlyOrderView
from shopback.base.resources import ChartsResource
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.permissions import IsAuthenticated
from shopback.base.renderers  import ChartJSONRenderer,ChartTemplateRenderer
from shopback.orders.renderers import OrderNumPiovtChartHtmlRenderer


urlpatterns = patterns('shopback.orders.views',

    url('update/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_finish_trade_amount',name='finish_trade_amount'),
)






