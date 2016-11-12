# coding=utf-8
from django.conf.urls import include, url
from rest_framework import routers
from . import views_apis

router = routers.DefaultRouter(trailing_slash=False)
router_urls = router.urls

router_urls += ([
    url(r'^channel_pay_stats$', views_apis.FinanceChannelPayApiView.as_view(), name='v1-finance-channel-pay-stats'),
    url(r'^refund_stats$', views_apis.FinanceRefundApiView.as_view(), name='v1-finance-refund-status-stats'),
    url(r'^return_good_stats$', views_apis.FinanceReturnGoodApiView.as_view(), name='v1-finance-return-good-stats'),
    url(r'^deposit_stats$', views_apis.FinanceDepositApiView.as_view(), name='v1-finance-deposit-stats'),
    url(r'^cost_stats$', views_apis.FinanceCostApiView.as_view(), name='v1-finance-cost-stats'),
    url(r'^stock_stats$', views_apis.FinanceStockApiView.as_view(), name='v1-finance-stock-stats'),
    url(r'^mama_order_carry_stats$', views_apis.MamaOrderCarryStatApiView.as_view(), name='v1-finance-carry-stats'),
])

urlpatterns = [
    url(r'^v1/', include(router_urls, namespace='finance_v1')),
]

