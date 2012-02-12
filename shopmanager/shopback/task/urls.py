from django.conf.urls.defaults import patterns, url
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.views import InstanceModelView
from shopback.task.views import CreateListItemTaskModelView
from shopback.base.permissions import IsAuthenticated, PerUserThrottling
from shopback.task.resources import ItemListTaskResource
from shopback.task.views import direct_update_listing,direct_del_listing,ListItemTaskView


urlpatterns = patterns('',

    url(r'^update/(?P<num_iid>[^/]+)/(?P<num>[^/]+)/$',direct_update_listing,name='update_listing'),
    url(r'^delete/(?P<num_iid>[^/]+)/$',direct_del_listing,name='delete_listing'),
    url(r'^$', CreateListItemTaskModelView.as_view(resource=ItemListTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,),)),
    url(r'^(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=ItemListTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,))),
    url(r'^list/self/$', ListItemTaskView.as_view(resource=ItemListTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,),)),

)
  