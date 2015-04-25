from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from views import logclicks
from views import StatsView,MamaStatsView
from django.contrib.auth.decorators import login_required  

urlpatterns = patterns('',
    url(r'^$',MamaStatsView.as_view()),
    url(r'^stats/$',login_required(StatsView.as_view())),
    url(r'^(?P<linkid>\d+)/$',logclicks),
)
