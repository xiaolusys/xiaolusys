from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required  




from views import logclicks,StatsView,MamaStatsView,CashoutView,CashOutList,CarryLogList,landing
from .views import chargeWXUser,XiaoluMamaModelView

urlpatterns = patterns('',
    url(r'^$',landing),
    url(r'^m/$',MamaStatsView.as_view()),
    url(r'^stats/$',login_required(StatsView.as_view())),
    url(r'^cashout/$',CashoutView.as_view()),
    url(r'^cashoutlist/$',CashOutList.as_view()),
    url(r'^carrylist/$',CarryLogList.as_view()),
    url(r'^(?P<linkid>\d+)/$',logclicks),    
    url(r'^charge/(?P<pk>\d+)/$',chargeWXUser),
    url(r'^xlmm/(?P<pk>\d+)/$', XiaoluMamaModelView.as_view()),
)
