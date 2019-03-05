from django.conf.urls import include, url

from games.fund.views import FundAccountMgrView

urlpatterns = [
    url(r'^fundmgr/$', FundAccountMgrView.as_view(), name='fund_mgr'),
]