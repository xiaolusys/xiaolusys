# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from .views import FrozenScoreView

urlpatterns = [
    url(r'^frozen/$', FrozenScoreView.as_view()),
]
