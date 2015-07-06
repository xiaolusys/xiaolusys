from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'saletrades', views.SaleTradeViewSet)

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="rest_base.html")),
    url(r'^api/', include(router.urls,namespace='api'),name="xiaolumm_api"),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
)