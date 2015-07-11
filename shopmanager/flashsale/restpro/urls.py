from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from django.http import HttpResponse

from rest_framework import routers
from . import views
from flashsale.pay.views import OrderBuyReview

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'product', views.ProductViewSet)
router.register(r'shopping-cart', views.ShoppingCartViewSet)
router.register(r'trade', views.SaleTradeViewSet)
router.register(r'refund', views.SaleRefundViewSet)
router.register(r'address', views.UserAddressViewSet)
router.register(r'district', views.DistrictViewSet)

router_urls = router.urls

router_urls += patterns('',
         url(r'^order/buy/', OrderBuyReview.as_view(), name="order_buy")
    )

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="rest_base.html")),
    url(r'^v1/', include(router_urls,namespace='v1')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
)