# coding=utf-8
from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from django.contrib.admin.views.decorators import staff_member_required
from .decorators import sale_buyer_required
from . import views
from rest_framework import routers
from flashsale.pay.views import refund

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'salerefund', refund.SaleRefundViewSet)

router_urls = router.urls

urlpatterns = patterns('',
                       url(r'^v1/', include(router_urls, namespace='flashsale_pay_v1')),
                       )

urlpatterns += (
    url(r'^callback/$', csrf_exempt(views.PINGPPCallbackView.as_view())),
    url(r'^cancel/$', csrf_exempt(views.PINGPPCallbackView.as_view())),
    url(r'^wxwarn/$', csrf_exempt(views.WXPayWarnView.as_view())),

    # product urls
    url(r'^plist/$', views.productlist_redirect, name="sale_home"),

    url(r'^locknum/$', sale_buyer_required(views.productsku_quantity_view), name="skuquantity_lock"),
    url(r'^pdetail/(?P<pk>[0-9]+)/$', views.ProductDetailView.as_view(), name="pdetail_for_phone"),

    # order urls
    url(r'^orderbuy/pay.htm$', cache_page(24 * 60 * 60)(TemplateView.as_view(template_name="pay/pay.html"))),
    url(r'^payresult/$', sale_buyer_required(views.PayResultView.as_view()), name="user_payresult"),

    # address urls
    url(r'^addr/list/$', sale_buyer_required(views.AddressList.as_view()), name="address_list"),
    url(r'^addr/$', sale_buyer_required(views.UserAddressDetail.as_view()), name="address_ins"),
    url(r'^addr/area/$', cache_page(24 * 60 * 60)(views.DistrictList.as_view()), name="address_area"),

    # envelop urls
    url(r'^envelop/confirm/$', sale_buyer_required(views.EnvelopConfirmSendView.as_view()), name="envelop_confirm"),

    # profile urls
    url(r'^login/$', views.flashsale_login, name="flashsale_login"),

    url(r'^order_flashsale/$', views.order_flashsale, name="order_flashsale"),
    url(r'^time_rank/(?P<time_id>\d+)/$', views.time_rank, name="time_rank"),
    url(r'^sale_state/(?P<state_id>\d+)/$', views.sale_state, name="sale_state"),
    url(r'^refund_state/(?P<state_id>\d+)/$', views.refund_state, name="refund_state"),
    url(r'^refunding_state/(?P<state_id>\d+)/$', views.refunding_state, name="refunding_state"),

    url(r'^preorder_flashsale/$', views.preorder_flashsale, name="preorder_flashsale"),
    url(r'^nextorder_flashsale/$', views.nextorder_flashsale, name="nextorder_flashsale"),
    url(r'^search_flashsale/$', views.search_flashsale, name="search_flashsale"),
    url(r'^aggregeta_product/$', csrf_exempt(views.AggregateProductView.as_view()), name="aggregate_product"),
    url(r'^chuantu/$', csrf_exempt(views.ChuanTuAPIView.as_view()), name="chuantu"),
    url(r'^check_product/$', csrf_exempt(views.AggregateProductCheckView.as_view()), name="check_product"),
    url(r'^add_aggregeta/$', staff_member_required(views.ModelProductView.as_view()), name="add_aggregate"),
    url(r'^checkmodelexist/$', csrf_exempt(views.CheckModelExistView.as_view()), name="check_model_exist"),

    url(r'^zone_analysis/$', csrf_exempt(views.show_Zone_Page), name="show_Zone_Page"),
    url(r'^zone_analysis/province/$', csrf_exempt(views.by_zone_Province), name="show_Zone_Page"),
    url(r'^zone_analysis/city/$', csrf_exempt(views.by_zone_City), name="by_zone_City"),
    url(r'^qiniu/$', views.QiniuAPIView.as_view()),
    url(r'^ref_reason/$', csrf_exempt(views.RefundReason.as_view())),
    url(r'^change_model_name_api/$', views.ModelChangeAPIView.as_view()),
    url(r'^post_poster/$', csrf_exempt(views.PostGoodShelf.as_view())),
    url(r'^change_sku_item/$', csrf_exempt(views.change_sku_item), name="change_sku_item"),
    url(r'^sent_sku_item_again/$', csrf_exempt(views.sent_sku_item_again), name="sent_sku_item_again"),
    url(r'^get_mrgid/$', csrf_exempt(views.get_mrgid), name="get_mrgid"),
    url(r'^refund_fee/$', csrf_exempt(views.refund_fee), name="refund_fee"),
    url(r'^update_memo/$', csrf_exempt(views.update_memo), name="update_memo"),
)
