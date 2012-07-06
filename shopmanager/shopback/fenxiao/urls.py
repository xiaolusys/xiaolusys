from django.conf.urls.defaults import patterns, include, url


__author__ = 'meixqhi'
  
  
urlpatterns = patterns('shopback.fenxiao.views',

    url('update/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_interval_purchases',name='interval_purchases'),

)