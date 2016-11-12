# coding=utf-8
from django.conf.urls import url, include
from django.views.decorators.cache import cache_page
from rest_framework import routers

from flashsale.pay import constants
from flashsale.pay.decorators import weixin_xlmm_auth

from . import views
from .views import activity as views_activity
from .views.activity_goods import ActivityGoodsViewSet
from .views.stock_sale import StockSaleViewSet
from .views.activity2 import ActivityViewSet


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'goods', ActivityGoodsViewSet)
router.register(r'stocksale', StockSaleViewSet)
router.register(r'activity', ActivityViewSet)

router_urls = router.urls
router_urls += ([])

urlpatterns = [
    url(r'^xlsampleapply/$', views.XLSampleapplyView.as_view(), name="xlsampleapply_view"),
    url(r'^appdownload/$', views.APPDownloadView.as_view(), name="app_download_view"),
    url(r'^cus_cdt/$', views.CusApplyOrdersView.as_view(), name="cus_promote_condition"),
    url(r'^exchange_reds/$', views.ExchangeRedToCoupon.as_view(), name="cus_exchange_pmt_reds"),
    url(r'^result/(?P<batch>\d+)/(?P<page>\d+)/(?P<month>\d+)/$',
       cache_page(24 * 60 * 60)(views.PromotionResult.as_view()), name="pmt_result"),
    url(r'^pmt_short_res/$', views.PromotionShortResult.as_view(), name="pmt_short_res_view"),
    url(r'^xlsampleorder/$', weixin_xlmm_auth(redirecto=constants.MALL_LOGIN_URL)(
       views.XlSampleOrderView.as_view()
    ), name="xlsampleorder_view"),
    url(r'^receive_award/$', views.ReceiveAwardView.as_view(), name="sample_award"),
    url(r'^ercode/$', views.QrCodeView.as_view(), name="qrcode_view"),
    url(r'^activity/', views_activity.ActivityView.as_view(), name="daily_activity"),
    url(r'^join/(?P<event_id>\d+)/', views_activity.JoinView.as_view(), name="join_activity"),
    url(r'^weixin_baseauth_join/(?P<event_id>\d+)/', views_activity.WeixinBaseAuthJoinView.as_view(),
       name="weixin_baseauth_join_activity"),
    url(r'^weixin_snsauth_join/(?P<event_id>\d+)/', views_activity.WeixinSNSAuthJoinView.as_view(),
       name="weixin_snsauth_join_activity"),
    url(r'^app_join/(?P<event_id>\d+)/', views_activity.AppJoinView.as_view(),
       name="app_join_activity"),
    url(r'^web_join/(?P<event_id>\d+)/', views_activity.WebJoinView.as_view(),
       name="web_join_activity"),
    url(r'^apply/(?P<event_id>\d+)/', views_activity.ApplicationView.as_view(),
       name="application_activity"),
    url(r'^activate/(?P<event_id>\d+)/', views_activity.ActivateView.as_view(),
       name="activate_activity"),
    url(r'^main/(?P<event_id>\d+)/', views_activity.MainView.as_view(), name="mainpage_activity"),
    url(r'^open_envelope/(?P<envelope_id>\d+)/', views_activity.OpenEnvelopeView.as_view(),
       name="open_envelope_activity"),
    url(r'^stats/(?P<event_id>\d+)/', views_activity.StatsView.as_view(), name="stats_activity"),
    url(r'^get_award/(?P<event_id>\d+)/', views_activity.GetAwardView.as_view(), name="get_award"),
    url(r'^promotion/', include(router_urls, namespace='promotion')),
]
