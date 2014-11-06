from django.conf.urls.defaults import patterns, include, url
from shopback.base.renderers  import BaseJsonRenderer

from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication,login_required_ajax

from .resources import InterceptTradeResource
from .views import InterceptByCsvFileView

urlpatterns = patterns('',

     (r'^trade/$',InterceptByCsvFileView.as_view(
        resource=InterceptTradeResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )), )