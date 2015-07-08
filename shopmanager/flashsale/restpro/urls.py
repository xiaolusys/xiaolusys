from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page

from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'product', views.ProductViewSet)
router.register(r'cart', views.ShoppingCartViewSet)
router.register(r'trade', views.SaleTradeViewSet)
router.register(r'refund', views.SaleRefundViewSet)
router.register(r'address', views.UserAddressViewSet)
router.register(r'district', views.DistrictViewSet)

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="rest_base.html")),
    url(r'^v1/', include(router.urls,namespace='v1')),
    
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
)