from django.conf.urls.defaults import patterns, url
from shopback.purchases.views import PurchaseItemView,PurchaseView,PurchaseInsView,\
    PurchaseStorageItemView,PurchaseStorageView,PurchaseStorageInsView,StorageDistributeView
from shopback.purchases.resources import PurchaseItemResource,PurchaseResource,PurchaseStorageResource,PurchaseStorageItemResource
from shopback.purchases.renderers import PurchaseItemHtmlRenderer,JSONRenderer,PurchaseHtmlRenderer,\
    PurchaseStorageHtmlRenderer,StorageDistributeRenderer
from shopback.base.renderers  import BaseJsonRenderer
from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns('shopback.purchases.views',
    
    (r'^add/$',csrf_exempt(PurchaseView.as_view(
        resource=PurchaseResource,
        renderers=(PurchaseHtmlRenderer,BaseJsonRenderer),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    ))),
    (r'^(?P<id>\d{1,20})/$',csrf_exempt(PurchaseInsView.as_view(
        resource=PurchaseResource,
        renderers=(PurchaseHtmlRenderer,BaseJsonRenderer),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    ))),
    (r'^item/$',csrf_exempt(PurchaseItemView.as_view(
        resource=PurchaseItemResource,
        renderers=(BaseJsonRenderer,),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    ))),
                       
    (r'^storage/add/$',csrf_exempt(PurchaseStorageView.as_view(
        resource=PurchaseStorageResource,
        renderers=(PurchaseStorageHtmlRenderer,BaseJsonRenderer),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    ))),
    (r'^storage/(?P<id>\d{1,20})/$',csrf_exempt(PurchaseStorageInsView.as_view(
        resource=PurchaseStorageResource,
        renderers=(PurchaseStorageHtmlRenderer,BaseJsonRenderer),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    ))),
    (r'^storage/item/$',csrf_exempt(PurchaseStorageItemView.as_view(
        resource=PurchaseStorageItemResource,
        renderers=(BaseJsonRenderer,),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    ))),
    (r'storage/distribute/(?P<id>\d{1,20})/',StorageDistributeView.as_view(
        resource=PurchaseStorageResource,
        renderers=(BaseJsonRenderer,StorageDistributeRenderer),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),
    
    url(r'storage/csv/(?P<id>\d{1,20})/','download_purchasestorage_file',name='purchasestorage_to_csv'),
    url(r'storage/item/del/','delete_purchasestorage_item',name='del_purchasestorage_item'),
   
    
    url(r'csv/(?P<id>\d{1,20})/','download_purchase_file',name='purchase_to_csv'),
    url(r'item/del/','delete_purchase_item',name='del_purchase_item'),
)