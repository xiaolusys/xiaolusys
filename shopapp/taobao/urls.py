from django.conf.urls import patterns, url
from django.contrib.auth.views import logout
from .views import request_taobao, login_taobao

urlpatterns = patterns('shopapp.taobao.views',

    url(r'login/$', request_taobao, name='request_taobao'),
    url(r'login/auth/$', login_taobao, name='top_auth2_redirect_uri'),
    url(r'^logout/$', logout, name='global_logout'),
    url(r'^test/api/$', 'test_api', name='test_api')

)