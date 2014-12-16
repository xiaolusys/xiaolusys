from django.conf.urls.defaults import patterns, include, url
from rest_framework.urlpatterns import format_suffix_patterns
from django.views.decorators.csrf import csrf_exempt
from . import views


urlpatterns = [
    url(r'^brand/$', views.SaleSupplierList.as_view()),
    url(r'^brand/(?P<pk>[0-9]+)/$', views.SaleSupplierDetail.as_view()),
    url(r'^product/$',views.SaleProductList.as_view()),
    url(r'^product/(?P<pk>[0-9]+)/$',views.SaleProductDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
