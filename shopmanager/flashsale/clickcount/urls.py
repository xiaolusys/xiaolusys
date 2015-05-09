# coding=utf-8
__author__ = 'linjie'
from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
                       url(r'^clickcount/$', views.clickcount, name=u'flashsale_clickconut'),  # 界面显示

                       url(r'^clickcount/bydate/$', views.bydate, name=u"flashsale_bydate"),  # 根据日期选择要显示的统计记录
                       )
