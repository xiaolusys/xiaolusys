from django.conf.urls import url
from shopapp.jingdong.views import *

urlpatterns = [
    url(r'login/$', loginJD, name='login_jd'),
    url(r'login/auth/$', loginAuthJD, name='login_auth_jd'),
]
