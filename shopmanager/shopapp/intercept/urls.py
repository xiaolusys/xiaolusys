from django.conf.urls import patterns, include, url
# from core.options.renderers  import BaseJsonRenderer
# 
# from core.options.permissions import IsAuthenticated
from shopback.base.authentication import login_required_ajax

# from .resources import InterceptTradeResource
from .views import InterceptByCsvFileView

urlpatterns = patterns('',

                       (r'^trade/$', InterceptByCsvFileView.as_view(
                           # resource=InterceptTradeResource,
                           # renderers=(BaseJsonRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )), )
