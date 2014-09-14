# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from .views import WeixinExamView,WeixinExamShareView

urlpatterns = patterns('',
    url(r'^$',csrf_exempt(WeixinExamView.as_view())),
    url(r'^share/$',csrf_exempt(WeixinExamShareView.as_view())),
)


