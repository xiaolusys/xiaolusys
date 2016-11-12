# coding=utf-8
from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt
from rest_framework import routers
from django.contrib.admin.views.decorators import staff_member_required
from shopback.warehouse.views import *
from shopback.warehouse.views_receipt import ReceiptGoodsViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'receipt', ReceiptGoodsViewSet)

urlpatterns = [
    url(r'^scancheck/$', csrf_exempt(PackageScanCheckView.as_view())),
    url(r'^scanweight/$', csrf_exempt(PackageScanWeightView.as_view())),
    url(r'^express_order/$', csrf_exempt(PackagOrderExpressView.as_view())),
    url(r'^operate/$', csrf_exempt(PackagOrderOperateView.as_view())),
    url(r'^revert/$', csrf_exempt(PackagOrderRevertView.as_view())),
    url(r'^print_express/$', csrf_exempt(PackagePrintExpressView.as_view())),
    url(r'^print_picking/$', csrf_exempt(PackagePrintPickingView.as_view())),
    url(r'^print_post/$', csrf_exempt(PackagePrintPostView.as_view())),
    url(r'^revieworder/(?P<id>\d{1,20})/$', staff_member_required(staff_member_required(PackageReviewView.as_view()))),
    url(r'^clear_redo_sign/$', csrf_exempt(PackageClearRedoView.as_view())),
]
urlpatterns += router.urls
