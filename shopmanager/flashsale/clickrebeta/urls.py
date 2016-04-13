__author__ = 'yann'
from django.conf.urls import patterns, url
from .views import StatisticTongJi

urlpatterns = patterns('',
                       url(r'^$', StatisticTongJi.as_view()),
                       url(r'^addall/$', "flashsale.clickrebeta.views.ShengChengAll")
                       )
