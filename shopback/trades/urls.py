# coding=utf-8
from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

from rest_framework import routers
from shopback.trades.views import *
from shopback.trades.views import detail, search_trade, manybeizhu, beizhu, test, select_Stock
from shopback.base.authentication import login_required_ajax

from shopback.trades import views_product_analysis
from shopback.trades import views_new_check_order
from shopback.trades.views_package import PackageOrderViewSet
from shopback.trades.views_arrival_time_analysis import ArrivalTimeViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'dirty_orders2', DirtyOrderViewSet, 'dirty_orders')
router.register(r'package_order', PackageOrderViewSet, 'package_order')
router.register(r'arrival_analysis', ArrivalTimeViewSet, 'arrival_analysis')

urlpatterns = [
    url(r'address/$', csrf_exempt(login_required_ajax(change_trade_addr))),
    url(r'order/update/(?P<id>\d{1,20})/$', csrf_exempt(login_required_ajax(change_trade_order))),
    url(r'order/delete/(?P<id>\d{1,20})/$', csrf_exempt(login_required_ajax(delete_trade_order))),
    url(r'^order/outstock/(?P<id>\d{1,20})/$', csrf_exempt(login_required_ajax(change_order_stock_status))),
    url(r'^replaysend/(?P<id>\d{1,20})/$', csrf_exempt(staff_member_required(replay_trade_send_result))),
    url(r'^replay_package_send/(?P<id>\d{1,20})/$', csrf_exempt(staff_member_required(replay_package_send_result))),

    url(r'review/(?P<id>\d{1,20})/$', csrf_exempt(login_required_ajax(review_order))),
    url(r'change_logistic/$', csrf_exempt(login_required_ajax(change_package_logistic_and_outsid))),
    url(r'change_ware_by/$', csrf_exempt(login_required_ajax(change_package_ware_by))),
    url(r'logistic/$', csrf_exempt(login_required_ajax(change_logistic_and_outsid))),
    url(r'^memo/$', csrf_exempt(login_required_ajax(update_sys_memo))),

    url(r'^priority/(?P<id>\d{1,20})/', ImprovePriorityView.as_view()),
    url(r'^regular/(?P<id>\d{1,20})/$', csrf_exempt(login_required_ajax(regular_trade))),

    url(r'^trade/(?P<id>\d{1,20})/$', InstanceModelView_new.as_view()),
    url(r'^checkorder/(?P<id>\d{1,20})/$', csrf_exempt(CheckOrderView.as_view())),
    url(r'^orderplus/$', OrderPlusView.as_view()),

    url(r'^revieworder/(?P<id>\d{1,20})/$', staff_member_required(ReviewOrderView.as_view())),
    url(r'^exchange/$', staff_member_required(ExchangeOrderView.as_view())),
    url(r'^exchange/(?P<id>\d{1,20})/$', staff_member_required(ExchangeOrderInstanceView.as_view()), name="exchange_order_instance"),
    url(r'^direct/$', staff_member_required(DirectOrderView.as_view())),
    url(r'^direct/(?P<id>\d{1,20})/$', staff_member_required(DirectOrderInstanceView.as_view()), name="direct_order_instance"),

    url(r'^tradeplus/$', TradeSearchView.as_view()),
    url(r'^order/statistic/$', StatisticMergeOrderView.as_view()),
    url(r'^order/statistic_async/$', StatisticMergeOrderAsyncView.as_view()),
    url(r'^order/outstock/$', OutStockOrderProductView.as_view()),
    url(r'^order/list/(?P<id>\d{1,20})/$', OrderListView.as_view()),
    url(r'^related/orders/$', RelatedOrderStateView.as_view()),
    url(r'^logistic/query/$', TradeLogisticView.as_view()),
    url(r'fenxiao/count/$', csrf_exempt(countFenxiaoAcount)),
    url(r'fenxiao/count/detail/$', staff_member_required(showFenxiaoDetail)),
    url(r'^scancheck/$', csrf_exempt(PackageScanCheckView.as_view())),
    url(r'^scanweight/$', csrf_exempt(PackageScanWeightView.as_view())),
    url(r'^detail/$', csrf_exempt(login_required_ajax(detail))),
    url(r'^manybeizhu/$', csrf_exempt(login_required_ajax(manybeizhu))),
    url(r'^search_trade/$', csrf_exempt(login_required_ajax(search_trade))),
    url(r'^chai_trade/$', views_new_check_order.ChaiTradeView.as_view()),
    # url (r'^check_order/(?P<trade_id>\d+)$',views_new_check_order.check_order,name="check_order"),
    # url (r'^check_order/(?P<id>\d+)$',csrf_exempt(CheckOrderView.as_view())),
    # linjie add in here
    # 产品的销售件数，金额，退货率，次品率
    url(r'^product_analysis/$', views_product_analysis.product_Analysis, name="product_Analysis"),
    # 小鹿妈妈的订单情况
    url(r'^xlmm_product_analysis/$', views_product_analysis.xlmm_Product_Analysis, name="xlmm_Product_Analysis"),

    url(r'^product_analysis_top100/$', views_product_analysis.product_Top100_By_Week, name="xlmm_Product_Analysis"),
    url(r'^product_analysis_collect_top100/$', views_product_analysis.product_Collect_Topp100, name="product_Collect_Topp100"),
    url(r'^select_stock/$', select_Stock, name='select_Stock'),

    url(r'^beizhu/$', beizhu, name='beizhu'),
    url(r'^test/$', test, name="test"),
    url(r'^open_trade/$', views_product_analysis.open_trade_time, name="open_trade"),
    url(r'^list_trade/$', views_product_analysis.list_trade_time, name="list_trade"),
    url(r'^dirty_orders_api/$', DirtyOrderListAPIView.as_view()),
    url(r'^dirty_orders/$', DirtyOrderListView.as_view()),
]

urlpatterns += router.urls
