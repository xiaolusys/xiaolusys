# -*- coding:utf8 -*-

from django.conf.urls import patterns, url
from flashsale.pay.decorators import weixin_xlmm_auth
from flashsale.pay import sale_settings
from .views import XLSampleapplyView, APPDownloadView, XlSampleOrderView


urlpatterns = patterns('',
   url(r'^xlsampleapply/$', XLSampleapplyView.as_view(), name="xlsampleapply_view"),
   url(r'^appdownload/$', APPDownloadView.as_view(), name="app_download_view"),
   url(r'^xlsampleorder/$', 
       weixin_xlmm_auth(redirecto=sale_settings.MALL_LOGIN_URL)(XlSampleOrderView.as_view()), 
       name="xlsampleorder_view"
    ),
)