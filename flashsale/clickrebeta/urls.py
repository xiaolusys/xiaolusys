__author__ = 'yann'
from django.conf.urls import url
from .views import StatisticTongJi
from flashsale.clickrebeta.views import *
urlpatterns = [
    url(r'^$', StatisticTongJi.as_view()),
    url(r'^addall/$', ShengChengAll),
]
