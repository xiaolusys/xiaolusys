__author__ = 'meixqhi'
from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('',

    (r'^memo/',include('shopapp.memorule.urls')),
    (r'^search/',include('shopapp.collector.urls')),
    (r'^report/',include('shopapp.report.urls')),
    (r'^autolist/',include('shopapp.autolist.urls')),
    (r'^async/',include('shopapp.asynctask.urls')),
    (r'^calendar/',include('shopapp.calendar.urls')),
    (r'^comment/',include('shopapp.comments.urls')),
    (r'^yunda/',include('shopapp.yunda.urls')),
)

