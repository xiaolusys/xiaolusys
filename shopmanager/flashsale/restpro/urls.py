from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from django.http import HttpResponse

from rest_framework import routers
from . import views
from . import views_user
from flashsale.pay.views import OrderBuyReview

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'register', views_user.RegisterViewSet)
router.register(r'users', views_user.CustomerViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'carts', views.ShoppingCartViewSet)
router.register(r'trades', views.SaleTradeViewSet)
router.register(r'refunds', views.SaleRefundViewSet)
router.register(r'address', views.UserAddressViewSet)
router.register(r'districts', views.DistrictViewSet)

router_urls = router.urls

router_urls += patterns('',
         url(r'^order/buy/', OrderBuyReview.as_view(), name="order_buy")
    )

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="rest_base.html")),
    url(r'^v1/', include(router_urls,namespace='v1')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
)