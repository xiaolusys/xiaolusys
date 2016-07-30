__author__ = 'yan.huang'
# coding=utf-8
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from views import workorder

urlpatterns = [
    url(r'workorder/(?P<pk>[0-9]+)/$', workorder.wk, name='wk')
]

urlpatterns += format_suffix_patterns(urlpatterns)