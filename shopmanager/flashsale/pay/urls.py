from urlparse import urljoin
from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from django.contrib.admin.views.decorators import staff_member_required
from .decorators import sale_buyer_required,weixin_xlmm_auth
from . import views
from .views_login import flashsale_login,productlist_redirect
from .views_address import AddressList,UserAddressDetail,DistrictList
from .views_refund import RefundApply,RefundConfirm, RefundPopPageView
from .views_product import productsku_quantity_view
from .views_order import order_flashsale,time_rank,sale_state,refund_state,refunding_state,preorder_flashsale,nextorder_flashsale,search_flashsale

from .views_aggregate import AggregateProductView, ModelProductView, CheckModelExistView,\
    AggregateProductCheckView, ChuanTuAPIView, ModelChangeAPIView

from .views_coupon import RefundCouponView
from .views_ref_reason import RefundReason, RefundAnaList


from flashsale.pay.views_zoneanalysis import show_Zone_Page, by_zone_Province, by_zone_City
urlpatterns = (
    url(r'^charge/$', csrf_exempt(views.PINGPPChargeView.as_view())),
    url(r'^callback/$', csrf_exempt(views.PINGPPCallbackView.as_view())),
    url(r'^cancel/$', csrf_exempt(views.PINGPPCallbackView.as_view())),
    
    #############product urls############
    url(r'^wxwarn/$', csrf_exempt(views.WXPayWarnView.as_view())),
    
    url(r'^plist/$', 
#         views.ProductList.as_view(),
        productlist_redirect,
        name="sale_home"),
    url(r'^p/(?P<pk>[0-9]+)/$', views.ProductDetail.as_view(),name="product_detail"),
    url(r'^locknum/$', sale_buyer_required(productsku_quantity_view),name="skuquantity_lock"),
    
    ##############order urls################
    url(r'^orderbuy/$',sale_buyer_required(views.OrderBuyReview.as_view())),
    url(r'^orderbuy/pay.htm$',cache_page(TemplateView.as_view(template_name="pay/pay.html"),24*60*60)),
    url(r'^orderlist/$', sale_buyer_required(views.SaleOrderList.as_view()),name="user_orderlist"),
    url(r'^order/(?P<pk>[0-9]+)/$', sale_buyer_required(views.SaleOrderDetail.as_view()),name="user_orderdetail"),
    url(r'^payresult/$',sale_buyer_required(views.PayResultView.as_view()),name="user_payresult"),
    url(r'^logistic/(?P<pk>[0-9]+)/$',sale_buyer_required(cache_page(views.SaleTradeLogistic.as_view(),60*60)),name="order_logistic"),
    
    #############address urls############
    url(r'^addr/list/$',sale_buyer_required(AddressList.as_view()),name="address_list"),
    url(r'^addr/$', sale_buyer_required(UserAddressDetail.as_view()),name="address_ins"),
    url(r'^addr/area/$', cache_page(DistrictList.as_view(),24*60*60),name="address_area"),
    
    #############refund urls############
    url(r'^refund/$',sale_buyer_required(RefundApply.as_view()),name="refund_apply"),
    url(r'^refund/(?P<pk>[0-9]+)/$',sale_buyer_required(RefundConfirm.as_view()),name="refund_confirm"),
    
    ################envelop urls##################
    url(r'^envelop/confirm/$',sale_buyer_required(views.EnvelopConfirmSendView.as_view()),name="envelop_confirm"),
    
    
    #############profile urls############
    url(r'^profile/$',sale_buyer_required(views.UserProfile.as_view()),name="user_profile"),
    
    url(r'^login/$', flashsale_login,name="flashsale_login"),
    
    url(r'^test/$', TemplateView.as_view(template_name="pay/maddress.html")),
    ####fangkaineng  5-22
    url(r'^order_flashsale/$', order_flashsale,name="order_flashsale"),           
    url(r'^time_rank/(?P<time_id>\d+)/$',time_rank,name="time_rank"),
    url(r'^sale_state/(?P<state_id>\d+)/$',sale_state,name="sale_state"),
    url(r'^refund_state/(?P<state_id>\d+)/$',refund_state,name="refund_state"),  
    url(r'^refunding_state/(?P<state_id>\d+)/$',refunding_state,name="refunding_state"),
#
    url(r'^preorder_flashsale/$', preorder_flashsale,name="preorder_flashsale"),  
    url(r'^nextorder_flashsale/$', nextorder_flashsale,name="nextorder_flashsale"),
    url(r'^search_flashsale/$', search_flashsale,name="search_flashsale"),    
    url(r'^aggregeta_product/$', csrf_exempt(AggregateProductView.as_view()), name="aggregate_product"),
    url(r'^chuantu/$', csrf_exempt(ChuanTuAPIView.as_view()), name="chuantu"),
    url(r'^check_product/$', csrf_exempt(AggregateProductCheckView.as_view()), name="check_product"),
    url(r'^add_aggregeta/$', staff_member_required(ModelProductView.as_view()), name="add_aggregate"),
    url(r'^checkmodelexist/$', csrf_exempt(CheckModelExistView.as_view()), name="check_model_exist"),

    url(r'^zone_analysis/$', csrf_exempt(show_Zone_Page), name="show_Zone_Page"),
    # zone_analysis/province/
    url(r'^zone_analysis/province/$', csrf_exempt(by_zone_Province), name="show_Zone_Page"),
    # by_zone_City
    url(r'^zone_analysis/city/$', csrf_exempt(by_zone_City), name="by_zone_City"),
    url(r'^qiniu/$', views.QiniuApi.as_view()),
    url(r'^rsrc/$', csrf_exempt(RefundCouponView.as_view())),
    url(r'^ref_reason/$', csrf_exempt(RefundReason.as_view())),
    url(r'^pro_ref_list/$', csrf_exempt(RefundAnaList.as_view())),
    url(r'^refund_pop_page/$', csrf_exempt(RefundPopPageView.as_view())),
    url(r'^change_model_name_api/$', ModelChangeAPIView.as_view())
)
