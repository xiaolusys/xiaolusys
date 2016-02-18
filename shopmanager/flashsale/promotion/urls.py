# -*- coding:utf8 -*-

from django.conf.urls import patterns, url
from .views import XLSampleapplyView, APPDownloadView, XlSampleOrderView, PromotionResult, PromotionShortResult
from flashsale.pay.decorators import weixin_xlmm_auth
from flashsale.pay import sale_settings




urlpatterns = patterns('',
   url(r'^xlsampleapply/$', XLSampleapplyView.as_view(), name="xlsampleapply_view"),
   url(r'^appdownload/$', APPDownloadView.as_view(), name="app_download_view"),
   url(r'^pmt_res/(?P<batch>\d+)/(?P<page>\d+)/(?P<month>\d+)/$', PromotionResult.as_view(), name="pmt_res_view"),
   url(r'^pmt_short_res/$', PromotionShortResult.as_view(), name="pmt_short_res_view"),
   url(r'^xlsampleorder/$', weixin_xlmm_auth(redirecto=sale_settings.MALL_LOGIN_URL)(XlSampleOrderView.as_view()),
       name="xlsampleorder_view"),
)