from django.conf.urls.defaults import patterns, include, url
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.permissions import IsAuthenticated

__author__ = 'meixqhi'

urlpatterns = patterns('shopback.logistics.views',

    url('update/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_interval_logistics',name='update_logistic'),

)


