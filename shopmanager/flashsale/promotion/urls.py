# -*- coding:utf8 -*-

from django.conf.urls import patterns, url
from .views import XLSampleapplyView, APPDownloadView, ActivationShareView

urlpatterns = patterns('',
                       url(r'^xlsampleapply/$', XLSampleapplyView.as_view(), name="xlsampleapply_view"),
                       url(r'^appdownload/$', APPDownloadView.as_view(), name="app_download_view"),
                       url(r'^activeshare/$', ActivationShareView.as_view(), name="active_share"),
                       )