from django.conf.urls.defaults import patterns, include, url
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.permissions import IsAuthenticated
from shopback.base.renderers  import ChartJSONRenderer
from shopback.asynctask.views import AsyncCategoryView,AsyncOrderView
from shopback.asynctask.resources import AsyncTaskResource


urlpatterns = patterns('',

   (r'^category/(?P<cids>[^/]+)/$',AsyncCategoryView.as_view(
        resource=AsyncTaskResource,
        renderers=(ChartJSONRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^orders/(?P<start_dt>[^/]+)/(?P<end_dt>[^/]+)/$',AsyncOrderView.as_view(
        resource=AsyncTaskResource,
        renderers=(ChartJSONRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    url(r'^djcelery/',include('djcelery.urls'),name="task_state"),
                       
)
