from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt

from .decorators import sale_buyer_required
from . import views
from views_login import flashsale_login

urlpatterns = (
    url(r'^charge/$', csrf_exempt(views.PINGPPChargeView.as_view())),
    url(r'^callback/$', csrf_exempt(views.PINGPPCallbackView.as_view())),
    url(r'^cancel/$', csrf_exempt(views.PINGPPCallbackView.as_view())),
    
    #############weixin config############
    url(r'^wxwarn/$', csrf_exempt(views.WXPayWarnView.as_view())),
    
    url(r'^plist/$', views.ProductList.as_view(),name="sale_list"),
    url(r'^p/(?P<pk>[0-9]+)/$', views.ProductDetail.as_view()),
    url(r'^orderbuy/$',sale_buyer_required(views.OrderBuyReview.as_view())),
    
    url(r'^login/$', flashsale_login,name="flashsale_login"),
)
