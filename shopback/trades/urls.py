# coding=utf-8
from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

from rest_framework import routers
# from djangorestframework.views import InstanceModelView

from shopback.trades.views import (StatisticMergeOrderView,
                                   CheckOrderView,
                                   OrderPlusView,
                                   ReviewOrderView,
                                   ExchangeOrderView,
                                   OutStockOrderProductView,
                                   TradeSearchView,
                                   DirectOrderView,
                                   OrderListView,
                                   TradeLogisticView,
                                   change_trade_addr,
                                   change_trade_order,
                                   delete_trade_order,
                                   change_logistic_and_outsid,
                                   change_package_ware_by,
                                   review_order,
                                   update_sys_memo,
                                   change_order_stock_status,
                                   regular_trade,
                                   ExchangeOrderInstanceView,
                                   DirectOrderInstanceView,
                                   RelatedOrderStateView,
                                   ImprovePriorityView,
                                   replay_trade_send_result,
                                   replay_package_send_result,
                                   change_package_logistic_and_outsid,
                                   countFenxiaoAcount,
                                   showFenxiaoDetail,
                                   PackageScanCheckView,
                                   PackageScanWeightView,
                                   InstanceModelView_new,
                                   StatisticMergeOrderAsyncView,
                                   DirtyOrderListAPIView,
                                   DirtyOrderListView,
                                   DirtyOrderViewSet
                                   )
from shopback.trades.views import detail, search_trade, manybeizhu, beizhu, test, select_Stock
# from core.options.renderers  import BaseJsonRenderer
# from shopback.trades.renderers import (CheckOrderRenderer,
#                                        ReviewOrderRenderer,
#                                        ExchangeOrderRender,
#                                        DirectOrderRender,
#                                        StatisticMergeOrderRender,
#                                        StatisticOutStockRender,
#                                        OrderListRender,
#                                        TradeLogisticRender,
#                                        RelatedOrderRenderer)
# from shopback.trades.resources import (BaseResource,
#                                        TradeResource,
#                                        OrderPlusResource,
#                                        ExchangeOrderResource,
#                                        MergeTradeResource,
#                                        StatisticMergeOrderResource)
# from core.options.permissions import IsAuthenticated
from shopback.base.authentication import login_required_ajax

from shopback.trades import views_product_analysis
from shopback.trades import views_new_check_order

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'dirty_orders2', DirtyOrderViewSet, 'dirty_orders')

urlpatterns = patterns('shopback.trades.views',

                       (r'address/$', csrf_exempt(login_required_ajax(change_trade_addr))),
                       (r'order/update/(?P<id>\d{1,20})/$', csrf_exempt(login_required_ajax(change_trade_order))),
                       (r'order/delete/(?P<id>\d{1,20})/$', csrf_exempt(login_required_ajax(delete_trade_order))),
                       (r'^order/outstock/(?P<id>\d{1,20})/$',
                        csrf_exempt(login_required_ajax(change_order_stock_status))),
                       (
                       r'^replaysend/(?P<id>\d{1,20})/$', csrf_exempt(staff_member_required(replay_trade_send_result))),
                       (r'^replay_package_send/(?P<id>\d{1,20})/$', csrf_exempt(staff_member_required(replay_package_send_result))),

                       (r'review/(?P<id>\d{1,20})/$', csrf_exempt(login_required_ajax(review_order))),
                       (r'change_logistic/$', csrf_exempt(login_required_ajax(change_package_logistic_and_outsid))),
                       (r'change_ware_by/$', csrf_exempt(login_required_ajax(change_package_ware_by))),
                       (r'logistic/$', csrf_exempt(login_required_ajax(change_logistic_and_outsid))),
                       (r'^memo/$', csrf_exempt(login_required_ajax(update_sys_memo))),
                       (r'^priority/(?P<id>\d{1,20})/', ImprovePriorityView.as_view(
                           # resource=MergeTradeResource,
                           # renderers=(BaseJsonRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),
                       (r'^regular/(?P<id>\d{1,20})/$', csrf_exempt(login_required_ajax(regular_trade))),

                       (r'^trade/(?P<id>\d{1,20})/$', InstanceModelView_new.as_view(
                           #         resource=MergeTradeResource,
                           #         renderers=(BaseJsonRenderer,CheckOrderRenderer),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^checkorder/(?P<id>\d{1,20})/$', csrf_exempt(CheckOrderView.as_view(
                           #         resource=TradeResource,
                           #         renderers=(BaseJsonRenderer,CheckOrderRenderer),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       ))),
                       (r'^orderplus/$', OrderPlusView.as_view(
                           # resource=OrderPlusResource,
                           # renderers=(BaseJsonRenderer,),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       )),

                       (r'^revieworder/(?P<id>\d{1,20})/$', staff_member_required(ReviewOrderView.as_view(
                           # resource=OrderPlusResource,
                           # renderers=(BaseJsonRenderer,ReviewOrderRenderer),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       ))),
                       (r'^exchange/$', staff_member_required(ExchangeOrderView.as_view(
                           # resource=ExchangeOrderResource,
                           # renderers=(BaseJsonRenderer,ExchangeOrderRender),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       ))),
                       url(r'^exchange/(?P<id>\d{1,20})/$',
                           staff_member_required(ExchangeOrderInstanceView.as_view(
                               # resource=ExchangeOrderResource,
                               # renderers=(BaseJsonRenderer,ExchangeOrderRender),from django.http import HttpResponse, Http404
                               # authentication=(UserLoggedInAuthentication,),
                               # permissions=(IsAuthenticated,)
                           )), name="exchange_order_instance"),
                       (r'^direct/$', staff_member_required(DirectOrderView.as_view(
                           #         resource=ExchangeOrderResource,
                           #         renderers=(BaseJsonRenderer,DirectOrderRender),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       ))),
                       url(r'^direct/(?P<id>\d{1,20})/$',
                           staff_member_required(DirectOrderInstanceView.as_view(
                               #             resource=ExchangeOrderResource,
                               #             renderers=(BaseJsonRenderer,DirectOrderRender),
                               #             authentication=(UserLoggedInAuthentication,),
                               #             permissions=(IsAuthenticated,)
                           )), name="direct_order_instance"),

                       (r'^tradeplus/$', TradeSearchView.as_view(
                           #         resource=OrderPlusResource,
                           #         renderers=(BaseJsonRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^order/statistic/$', StatisticMergeOrderView.as_view(
                           #         resource=StatisticMergeOrderResource,
                           #         renderers=(BaseJsonRenderer,StatisticMergeOrderRender),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),
                       (r'^order/statistic_async/$', StatisticMergeOrderAsyncView.as_view()),
                       (r'^order/outstock/$', OutStockOrderProductView.as_view(
                           #         resource=StatisticMergeOrderResource,
                           #         renderers=(BaseJsonRenderer,StatisticOutStockRender),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),

                       (r'^order/list/(?P<id>\d{1,20})/$', OrderListView.as_view(
                           #         resource=OrderPlusResource,
                           #         renderers=(BaseJsonRenderer,OrderListRender),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),

                       (r'^related/orders/$', RelatedOrderStateView.as_view(
                           #         resource=BaseResource,
                           #         renderers=(RelatedOrderRenderer,BaseJsonRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),

                       (r'^logistic/query/$', TradeLogisticView.as_view(
                           #         resource=MergeTradeResource,
                           #         renderers=(BaseJsonRenderer,TradeLogisticRender),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       )),

                       (r'fenxiao/count/$', csrf_exempt(countFenxiaoAcount)),

                       (r'fenxiao/count/detail/$', staff_member_required(showFenxiaoDetail)),

                       (r'^scancheck/$', csrf_exempt(PackageScanCheckView.as_view())),
                       (r'^scanweight/$', csrf_exempt(PackageScanWeightView.as_view())),

                       (r'^detail/$', csrf_exempt(login_required_ajax(detail))),
                       (r'^manybeizhu/$', csrf_exempt(login_required_ajax(manybeizhu))),
                       (r'^search_trade/$', csrf_exempt(login_required_ajax(search_trade))),
                       (r'^chai_trade/$', views_new_check_order.ChaiTradeView.as_view()),
                       # url (r'^check_order/(?P<trade_id>\d+)$',views_new_check_order.check_order,name="check_order"),
                       #     url (r'^check_order/(?P<id>\d+)$',csrf_exempt(CheckOrderView.as_view(
                       #         resource=TradeResource,
                       #         renderers=(BaseJsonRenderer,CheckOrderRenderer),
                       #         authentication=(UserLoggedInAuthentication,),
                       #         permissions=(IsAuthenticated,)
                       #     ))),
                       # linjie add in here
                       # 产品的销售件数，金额，退货率，次品率
                       url(r'^product_analysis/$', views_product_analysis.product_Analysis, name="product_Analysis"),
                       # 小鹿妈妈的订单情况
                       url(r'^xlmm_product_analysis/$', views_product_analysis.xlmm_Product_Analysis,
                           name="xlmm_Product_Analysis"),

                       url(r'^product_analysis_top100/$', views_product_analysis.product_Top100_By_Week,
                           name="xlmm_Product_Analysis"),
                       url(r'^product_analysis_collect_top100/$', views_product_analysis.product_Collect_Topp100,
                           name="product_Collect_Topp100"),
                       url(r'^select_stock/$', select_Stock, name='select_Stock'),

                       url(r'^beizhu/$', beizhu, name='beizhu'),
                       url(r'^test/$', test, name="test"),
                       url(r'^open_trade/$', views_product_analysis.open_trade_time, name="open_trade"),
                       url(r'^list_trade/$', views_product_analysis.list_trade_time, name="list_trade"),
                       url(r'^dirty_orders_api/$', DirtyOrderListAPIView.as_view()),
                       url(r'^dirty_orders/$', DirtyOrderListView.as_view()),
                       )
urlpatterns += router.urls
