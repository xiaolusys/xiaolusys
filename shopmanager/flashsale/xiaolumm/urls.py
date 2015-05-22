from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required  




from views import logclicks,StatsView,MamaStatsView,CashoutView,CashOutList,CarryLogList,landing,cash_Out_Verify,cash_modify,cash_reject,stats_summary
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
    url(r'^cashoutverify/$',cash_Out_Verify,name="cashout_verify"), 
    url(r'^cashmodify/(?P<data>\w+)/$',cash_modify), #
    url(r'^cashreject/(?P<data>\w+)/$',cash_reject), #
    url(r'^stats_summary/$',stats_summary,name="stats_summary"),
)
