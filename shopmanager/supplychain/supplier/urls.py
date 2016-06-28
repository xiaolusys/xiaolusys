# coding: utf-8

from django.conf.urls import patterns, include, url
from rest_framework.urlpatterns import format_suffix_patterns
from django.views.decorators.csrf import csrf_exempt

from . import views


urlpatterns = [
    url(r'^brand/$', views.SaleSupplierList.as_view()),
    url(r'^brand/(?P<pk>[0-9]+)/$', views.SaleSupplierDetail.as_view()),
    url(r'^brand/charge/(?P<pk>[0-9]+)/$', views.chargeSupplier),

    url(r'^brand/fetch/(?P<pk>[0-9]+)/$', views.FetchAndCreateProduct.as_view()),

    url(r'^product/$', views.SaleProductList.as_view()),
    url(r'^line_product/$', views.SaleProductAdd.as_view()),
    url(r'^product/(?P<pk>[0-9]+)/$', views.SaleProductDetail.as_view()),
    url(r'^buyer_group/$', csrf_exempt(views.BuyerGroupSave.as_view())),
    url(r'^qiniu/$', views.QiniuApi.as_view()),
    # select sale_time
    url(r'^select_sale_time/$', views.change_Sale_Time),
    url(r'^bdproduct/(?P<pk>[0-9]+)/$', views.AggregateProductView.as_view()),
    url(r'^addsupplier/$', views.AddSupplierView.as_view()),
    url(r'^checksupplier/$', views.CheckSupplierView.as_view()),
    url(r'^hotpro/$', views.HotProductView.as_view()),
    url(r'^manage_schedule/$', views.ScheduleManageView.as_view()),
    url(r'^schedule/detail/(?P<pk>[0-9]+)/$', views.SaleProductManageDetailView.as_view()),
    url(r'^schedule_detail/$', views.ScheduleDetailView.as_view()),
    url(r'^schedule_detail_api/$', views.ScheduleDetailAPIView.as_view()),
    url(r'^schedule_export/$', views.ScheduleExportView.as_view()),
    url(r'^collect_num_api/$', views.CollectNumAPIView.as_view()),
    url(r'^remain_num_api/$', views.RemainNumAPIView.as_view()),
    url(r'^sync_stock_api/$', views.SyncStockAPIView.as_view()),
    url(r'^compare_schedule/$', views.ScheduleCompareView.as_view()),

    url(r'^sale_product_api/$', views.SaleProductAPIView.as_view()),
    url(r'^approve_schedule_detail_api/$', views.ScheduleDetailApproveAPIView.as_view()),
    url(r'^change_list_fields/$', views.SupplierFieldsChange.as_view()),
    url(r'^product_change/([0-9]+)/$', views.SaleProductChange.as_view()),
    url(r'^schedule_batch_set/$', views.ScheduleBatchSetView.as_view()),
    url(r'^category_mapping/$', views.CategoryMappingView.as_view()),
    url(r'^saleproduct_schedule_date/$', views.SaleProductScheduleDateView.as_view()),
    url(r'^saleproduct_note/$', views.SaleProductNoteView.as_view()),
    url(r'^saleproduct_sale_date/$', views.SaleProductSaleQuantityView.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)
