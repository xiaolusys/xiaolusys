from django.conf.urls.defaults import patterns, url
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.views import ListOrCreateModelView,SimpleInstanceView
from shopback.base.permissions import IsAuthenticated
from shopback.task.resources import ItemTaskResource


urlpatterns = patterns('',
    url(r'^$', ListOrCreateModelView.as_view(resource=ItemTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,))),
    url(r'^(?P<pk>[^/]+)/$', SimpleInstanceView.as_view(resource=ItemTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,))),
)
  