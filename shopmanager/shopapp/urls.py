__author__ = 'meixqhi'
from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('',

    (r'^memo/',include('shopapp.memorule.urls')),
    (r'^search/',include('shopapp.search.urls')),
    (r'^syncnum/',include('shopapp.syncnum.urls')),
    (r'^autolist/',include('shopapp.autolist.urls')),
)

