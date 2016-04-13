# coding: utf-8
from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt

import views

urlpatterns = patterns('',

                       url(r'^scan/$', views.scan_ruku, name="scan"),
                       url(r'^scan_sel/$', views.scan_select, name="scan_sel"),
                       url(r'^scan_list/$', views.scan_list, name="scan_list"),
                       url(r'^scan_save/$', views.scan_save, name="scan_save"),

                       url(r'^scan_new/$', views.SampleScanView.as_view(), name="scan_new"),
                       )
