from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from views import logclicks
from views import StatsView

urlpatterns = patterns('',
    url(r'^stats/$',StatsView.as_view()),
    url(r'^(?P<linkid>\d+)/$',logclicks),
)
