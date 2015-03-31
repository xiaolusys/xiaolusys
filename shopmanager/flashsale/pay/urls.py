from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from . import views


urlpatterns = (
    url(r'^charge/$', csrf_exempt(views.PINGPPChargeView.as_view())),
    url(r'^callback/$', csrf_exempt(views.PINGPPCallbackView.as_view())),
    
    url(r'^plist/$', views.ProductList.as_view()),
    url(r'^p/(?P<pk>[0-9]+)/$', views.ProductDetail.as_view()),
    url(r'^orderbuy/$',views.OrderBuyReview.as_view()),
    
    url(r'^cancel/$', csrf_exempt(views.PINGPPCallbackView.as_view())),
)
