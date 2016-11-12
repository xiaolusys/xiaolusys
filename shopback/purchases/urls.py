from django.conf.urls import url
from shopback.purchases.views import *
# from shopback.purchases.resources import PurchaseItemResource,PurchaseResource,PurchaseStorageResource,\
#     PurchaseStorageItemResource,PurchasePaymentResource
# from shopback.purchases.renderers import PurchaseItemHtmlRenderer,JSONRenderer,PurchaseHtmlRenderer,\
#     PurchaseStorageHtmlRenderer,StorageDistributeRenderer,PurchaseShipStorageRenderer,PurchasePaymentRenderer,PaymentDistributeRenderer
# from core.options.renderers  import BaseJsonRenderer
from django.views.decorators.csrf import csrf_exempt
# from core.options.permissions import IsAuthenticated
from shopback.base.authentication import login_required_ajax

urlpatterns = [
    url(r'^add/$', csrf_exempt(PurchaseView.as_view(
       # resource=PurchaseResource,
       # renderers=(PurchaseHtmlRenderer,BaseJsonRenderer),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    ))),
    url(r'^(?P<id>\d{1,20})/$', csrf_exempt(PurchaseInsView.as_view(
       # resource=PurchaseResource,
       # renderers=(PurchaseHtmlRenderer,BaseJsonRenderer),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    ))),
    url(r'^item/$', csrf_exempt(PurchaseItemView.as_view(
       # resource=PurchaseItemResource,
       # renderers=(BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    ))),
    url(r'ship/(?P<id>\d{1,20})/$', PurchaseShipStorageView.as_view(
       # resource=PurchaseResource,
       # renderers=(BaseJsonRenderer,PurchaseShipStorageRenderer),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    )),

    url(r'^storage/add/$', csrf_exempt(PurchaseStorageView.as_view(
       # resource=PurchaseStorageResource,
       # renderers=(PurchaseStorageHtmlRenderer,BaseJsonRenderer),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    ))),
    url(r'^storage/(?P<id>\d{1,20})/$', csrf_exempt(PurchaseStorageInsView.as_view(
       # resource=PurchaseStorageResource,
       # renderers=(PurchaseStorageHtmlRenderer,BaseJsonRenderer),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    ))),
    url(r'^storage/item/$', csrf_exempt(PurchaseStorageItemView.as_view(
       # resource=PurchaseStorageItemResource,
       #  renderers=(BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    ))),
    url(r'storage/distribute/(?P<id>\d{1,20})/$', csrf_exempt(StorageDistributeView.as_view(
       #         resource=PurchaseStorageResource,
       #         renderers=(BaseJsonRenderer,StorageDistributeRenderer),
       #         authentication=(UserLoggedInAuthentication,),
       #         permissions=(IsAuthenticated,)
    ))),
    url(r'storage/confirm/$', csrf_exempt(ConfirmStorageView.as_view(
       # resource=PurchaseStorageResource,
       # renderers=(BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    ))),
    url(r'payment/$', csrf_exempt(PurchasePaymentView.as_view(
       #         resource=PurchasePaymentResource,
       #         renderers=(BaseJsonRenderer,PurchasePaymentRenderer),
       #         authentication=(UserLoggedInAuthentication,),
       #         permissions=(IsAuthenticated,)
       # )),name='purchase_payment'),
    ))),

    url(r'storage/refresh/(?P<id>\d{1,20})/$', refresh_purchasestorage_ship,
       name='refresh_storage_ship'),
    url(r'storage/csv/(?P<id>\d{1,20})/$', download_purchasestorage_file,
       name='purchasestorage_to_csv'),

    url(r'^upload/(?P<id>\d{1,20})/$', upload_purchase_file, name='upload_purchase_file'),
    url(r'^storage/upload/(?P<id>\d{1,20})/$', upload_purchase_storage_file,
       name='upload_purchase_storage_file'),

    url(r'storage/item/del/$', delete_purchasestorage_item, name='del_purchasestorage_item'),
    url(r'csv/(?P<id>\d{1,20})/$', download_purchase_file, name='purchase_to_csv'),
    url(r'item/del/$', delete_purchase_item, name='del_purchase_item'),

    url(r'^payment/distribute/(?P<id>\d{1,20})/$', PaymentDistributeView.as_view(
       #         resource=PurchasePaymentResource,
       #         renderers=(BaseJsonRenderer,PaymentDistributeRenderer),
       #         authentication=(UserLoggedInAuthentication,),
       #         permissions=(IsAuthenticated,)
    )),
    url(r'payment/confirm/$', confirm_payment_amount, name='payment_confirm')
]
