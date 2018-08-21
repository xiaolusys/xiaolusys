# coding: utf-8
from django.conf.urls import include, url
from rest_framework import routers
from .views import stats
from .views import bill

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'bill_list', bill.BillViewSet, 'bill_list')
router_urls = router.urls

router_urls += ([
    url(r'^channel_pay_stats$', stats.FinanceChannelPayApiView.as_view(), name='v1-finance-channel-pay-stats'),
    url(r'^refund_stats$', stats.FinanceRefundApiView.as_view(), name='v1-finance-refund-status-stats'),
    url(r'^return_good_stats$', stats.FinanceReturnGoodApiView.as_view(), name='v1-finance-return-good-stats'),
    url(r'^deposit_stats$', stats.FinanceDepositApiView.as_view(), name='v1-finance-deposit-stats'),
    url(r'^cost_stats$', stats.FinanceCostApiView.as_view(), name='v1-finance-cost-stats'),
    url(r'^stock_stats$', stats.FinanceStockApiView.as_view(), name='v1-finance-stock-stats'),
    url(r'^mama_order_carry_stats$', stats.MamaOrderCarryStatApiView.as_view(), name='v1-finance-carry-stats'),
    url(r'^boutique_coupon_stat$', stats.BoutiqueCouponStatApiView.as_view(), name='v1-finance-boutique-coupon'),
])

urlpatterns = [
    url(r'^v1/', include(router_urls, namespace='finance_v1')),
]

urlpatterns += router.urls
