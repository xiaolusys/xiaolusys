__author__ = 'yann'
from django.conf.urls.defaults import patterns, url
from .views import StatisticTongJi
urlpatterns = patterns('',
    url(r'^shopstats/$',StatisticTongJi.as_view())
)