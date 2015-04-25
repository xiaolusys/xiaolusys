from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page

from .decorators import sale_buyer_required
from . import views
from .views_login import flashsale_login
from .views_address import AddressList,UserAddressDetail,DistrictList
from .views_refund import RefundApply,RefundConfirm

urlpatterns = (
    url(r'^charge/$', csrf_exempt(views.PINGPPChargeView.as_view())),
    url(r'^callback/$', csrf_exempt(views.PINGPPCallbackView.as_view())),
    url(r'^cancel/$', csrf_exempt(views.PINGPPCallbackView.as_view())),
    
    #############product urls############
    url(r'^wxwarn/$', csrf_exempt(views.WXPayWarnView.as_view())),
    
    url(r'^plist/$', views.ProductList.as_view(),name="sale_home"),
    url(r'^p/(?P<pk>[0-9]+)/$', views.ProductDetail.as_view(),name="product_detail"),
    
    
    ##############order urls################
    url(r'^orderbuy/$',sale_buyer_required(views.OrderBuyReview.as_view())),
    url(r'^orderlist/$', sale_buyer_required(views.SaleOrderList.as_view()),name="user_orderlist"),
    url(r'^order/(?P<pk>[0-9]+)/$', sale_buyer_required(views.SaleOrderDetail.as_view()),name="user_orderdetail"),
    url(r'^payresult/$',sale_buyer_required(views.PayResultView.as_view()),name="user_payresult"),
    
    #############address urls############
    url(r'^addr/list/$',sale_buyer_required(AddressList.as_view()),name="address_list"),
    url(r'^addr/$', sale_buyer_required(UserAddressDetail.as_view()),name="address_ins"),
    url(r'^addr/area/$', cache_page(DistrictList.as_view(),24*60*60),name="address_area"),
    
    #############refund urls############
    url(r'^refund/$',sale_buyer_required(RefundApply.as_view()),name="refund_apply"),
    url(r'^refund/(?P<pk>[0-9]+)/$',sale_buyer_required(RefundConfirm.as_view()),name="refund_confirm"),
 
    #############profile urls############
    url(r'^profile/$',sale_buyer_required(views.UserProfile.as_view())),
    
    url(r'^login/$', flashsale_login,name="flashsale_login"),
    
    url(r'^test/$', TemplateView.as_view(
        template_name="pay/maddress.html")),
)
