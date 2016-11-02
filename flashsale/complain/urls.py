__author__ = 'yan.huang'
# coding=utf-8
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    url(r'complain/(?P<pk>[0-9]+)/$', views.ComplainsDetail.as_view()),
]

urlpatterns += format_suffix_patterns(urlpatterns)
