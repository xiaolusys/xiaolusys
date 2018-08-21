from django.conf.urls import include, url
from shopback.amounts.views import update_finish_trade_amount
# from core.options.resources import ChartsResource
# from core.options.authentication import UserLoggedInAuthentication
# from core.options.permissions import IsAuthenticated
# from core.options.renderers  import ChartJSONRenderer,ChartTemplateRenderer
# from shopback.orders.renderers import OrderNumPiovtChartHtmlRenderer


urlpatterns = [
    url('update/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', update_finish_trade_amount,
       name='finish_trade_amount'),
]
