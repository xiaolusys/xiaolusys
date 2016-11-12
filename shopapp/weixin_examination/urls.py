# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from .views import WeixinExamView, WeixinExamShareView

urlpatterns = [
    url(r'^(?P<userpk>\d+)/$', WeixinExamView.as_view()),
    url(r'^share/(?P<userpk>\d+)/$', csrf_exempt(WeixinExamShareView.as_view())),
]
