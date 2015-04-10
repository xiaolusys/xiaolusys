from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from .views import logclicks

urlpatterns = patterns('',
    url(r'^(?P<linkid>\d+)/$',logclicks),
)
