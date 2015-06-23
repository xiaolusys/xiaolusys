# coding=utf-8
# __author__ = 'linjie'
from django.conf.urls.defaults import patterns, include, url
from .view import popularize_Cost

urlpatterns = patterns('',
                       url(r'^popu_cost/', popularize_Cost, name="popularize_Cost"),
                       )
