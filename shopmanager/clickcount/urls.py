# coding=utf-8
__author__ = 'linjie'
from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
                       url(r'^clickcount/$', views.clickcount),  # 界面显示
                       url(r'^clickcount/writeall/$', views.write_all_user_click),  # 统计所有用户的数据写到数据库统计表中
                       url(r'^clickcount/showall/$', views.show_all),  # 显示所有记录
                       url(r'^clickcount/bydate/$', views.bydate),  # 根据日期选择要显示的统计记录
                       )
