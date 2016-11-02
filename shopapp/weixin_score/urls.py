# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt
from .views import FrozenScoreView

urlpatterns = patterns('',
                       url(r'^frozen/$', FrozenScoreView.as_view()),
                       )
