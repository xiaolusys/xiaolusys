# -*- coding:utf-8 -*-

from django.conf.urls import patterns, url
from django.views.decorators.cache import cache_page

from . import views 
from flashsale.pay.decorators import weixin_xlmm_auth
from flashsale.pay import constants


urlpatterns = patterns('',
    url(r'^xlsampleapply/$',views.XLSampleapplyView.as_view(), name="xlsampleapply_view"),
    url(r'^appdownload/$', views.APPDownloadView.as_view(), name="app_download_view"),
    url(r'^cus_cdt/$', views.CusApplyOrdersView.as_view(), name="cus_promote_condition"),
    url(r'^exchange_reds/$', views.ExchangeRedToCoupon.as_view(), name="cus_exchange_pmt_reds"),
    url(r'^result/(?P<batch>\d+)/(?P<page>\d+)/(?P<month>\d+)/$', 
       cache_page(views.PromotionResult.as_view(),24*60*60), 
       #views.PromotionResult.as_view(), 
       name="pmt_result"),
    url(r'^pmt_short_res/$', views.PromotionShortResult.as_view(), name="pmt_short_res_view"),
    url(r'^xlsampleorder/$', weixin_xlmm_auth(redirecto=constants.MALL_LOGIN_URL)(
                                views.XlSampleOrderView.as_view()
                            ), name="xlsampleorder_view"),
    url(r'^receive_award/$', views.ReceiveAwardView.as_view(), name="sample_award"),
    url(r'^ercode/$', views.QrCodeView.as_view(), name="qr_code_view")
)
