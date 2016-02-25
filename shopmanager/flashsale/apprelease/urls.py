# coding=utf-8

from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
                       url(r'^add/$', views.addNewReleaseView.as_view(), name="add_new_release"),
                       )