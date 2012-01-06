from django.conf.urls.defaults import patterns, url
from auth.accounts.views import request_taobo,login_taobo
from django.contrib.auth.views import logout

urlpatterns = patterns('',

    url(r'login/$', request_taobo, name='request_taobao'),
    url(r'login/taobao/$', login_taobo, name='login_taobao'),
    url(r'^logout/$', logout, name='global_logout'),

)
  