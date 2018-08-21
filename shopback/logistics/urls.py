__author__ = 'meixqhi'
from django.conf.urls import include, url

# from core.options.authentication import UserLoggedInAuthentication
# from core.options.permissions import IsAuthenticated
from shopback.logistics.views import *


urlpatterns = [
    url('company/$', update_logistics_company, name='update_company'),
    url('update/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', update_interval_logistics,
       name='update_logistic'),
]
