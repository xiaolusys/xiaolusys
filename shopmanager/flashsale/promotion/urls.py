# -*- coding:utf8 -*-

from django.conf.urls import patterns, url
from .views import XLSampleapplyView, APPDownloadView, XlSampleOrderView, PromotionResult

urlpatterns = patterns('',
   url(r'^xlsampleapply/$', XLSampleapplyView.as_view(), name="xlsampleapply_view"),
   url(r'^appdownload/$', APPDownloadView.as_view(), name="app_download_view"),
   url(r'^xlsampleorder/$', XlSampleOrderView.as_view(), name="xlsampleorder_view"),
   url(r'^pmt_res/$', PromotionResult.as_view(), name="pmt_res_view"),
)
