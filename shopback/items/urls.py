# coding: utf-8

from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView

from shopback.items.views.views import (ProductListView,
                                        ProductItemView,
                                        ProductModifyView,
                                        ProductUpdateView,
                                        StockRedundanciesView,
                                        ProductSkuStatsTmpView,
                                        ProductSkuInstanceView,
                                        ProductSearchView,
                                        ProductDistrictView,
                                        ProductBarCodeView,
                                        ProductWarnMgrView,
                                        ProductNumAssignView,
                                        ProductOrSkuStatusMdView,
                                        ProductView,
                                        ProductSkuView,
                                        StatProductSaleView,
                                        StatProductSaleAsyncView,
                                        ProductScanView)
from .views.product_location import ProductLocationViewSet
from .views.sku import ProductSkuViewSet
from shopback.items.views.views_rest import ProductInvalidConfirmView
from .select_sale_time import change_Sale_Time
from shopback.items.views.views_add import AddItemView, GetCategory, GetSupplier, GetSkuDetail, PreviewSkuDetail, \
    BatchSetTime, \
    ProductScheduleView, ProductScheduleAPIView
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'product_location', ProductLocationViewSet)
router2 = routers.DefaultRouter(trailing_slash=False)
router2.register(r'sku', ProductSkuViewSet)

urlpatterns = patterns('shopback.items.views.views',
                       url('update/items/$', 'update_user_items', name='update_items'),
                       url('update/item/$', 'update_user_item', name='update_item'),
                       url('update/stock/$', 'update_product_stock', name='update_stock'),
                       url('district/query/$', 'deposite_district_query', name='query_district'),
                       url('invalid/$', ProductInvalidConfirmView.as_view(), name='invalid_product'),
                       url('product/district/delete/$', 'delete_product_district', name='delete_district'),
                       (r'^split/$', TemplateView.as_view(template_name="items/split_product_template.html")),
                       (r'^product/(?P<id>[0-9]+)/$', ProductView.as_view()),
                       (r'^product/(?P<pid>[0-9]+)/(?P<sku_id>[0-9]+)/$', ProductSkuView.as_view()),

                       (r'^product/$', ProductListView.as_view({'get': 'list'})),
                       (r'^product/item/(?P<outer_id>[\w^_]+)/$', ProductItemView.as_view()),
                       (r'^product/modify/(?P<outer_id>[\w^_]+)/$', ProductModifyView.as_view()),
                       (r'^product/update/(?P<outer_id>[\w^_]+)/$', ProductUpdateView.as_view()),
                       (r'^product/sku/(?P<sku_id>[\w^_]+)/$', ProductSkuInstanceView.as_view()),
                       (r'^query/$', ProductSearchView.as_view()),
                       (r'^product/barcode/$', ProductBarCodeView.as_view()),
                       (r'^product/district/(?P<id>[0-9]+)/$', ProductDistrictView.as_view()),
                       (r'^podorsku/status/$', ProductOrSkuStatusMdView.as_view()),
                       (r'^product/warn/$', ProductWarnMgrView.as_view()),
                       (r'^product/assign/$', ProductNumAssignView.as_view()),
                       (r'^product/sale/$', StatProductSaleView.as_view()),
                       (r'^product/sale_async/$', StatProductSaleAsyncView.as_view()),
                       (r'^product/scan/$', ProductScanView.as_view()),
                       url(r'^test/$', TemplateView.as_view(
                           template_name="items/product_sku_diff.html"),
                           name='test_diff'),
                       url(r'^select_sale_time/$', change_Sale_Time, name='select_sale_time'),
                       url(r'^add_item/$', AddItemView.as_view(), name='select_sale_time'),
                       url(r'^get_category/$', GetCategory.as_view(), name='get_category'),
                       url(r'^get_supplier/$', GetSupplier.as_view(), name='get_supplier'),
                       url(r'^get_sku/$', GetSkuDetail.as_view(), name='get_sku'),
                       url(r'^preview_sku/$', PreviewSkuDetail.as_view(), name='preview_sku'),
                       url(r'^batch_settime/$', BatchSetTime.as_view(), name='batch_settime'),
                       url(r'^product_schedule/$', ProductScheduleView.as_view(), name='product_schedule'),
                       url(r'^product_schedule/(?P<p>\d+)/$', ProductScheduleView.as_view(), name='product_schedule'),
                       url(r'^product_schedule_api/$', ProductScheduleAPIView.as_view(), name='product_schedule_api'),
                       url(r'redundancies', StockRedundanciesView.as_view(), name='redundancies_view'),
                       url(r'supplierfilter', ProductSkuStatsTmpView.as_view(), name='supplierfilter_view'),
                       url(r'^location/', include(router.urls, namespace='v2')),
                       url(r'^v2/', include(router2.urls, namespace='v2_sku')),
                       )
