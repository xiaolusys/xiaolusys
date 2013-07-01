from django.conf.urls.defaults import patterns, url
from shopback.purchases.views import PurchaseItemView,PurchaseView,PurchaseInsView
from shopback.purchases.resources import PurchaseItemResource,PurchaseResource
from shopback.purchases.renderers import PurchaseItemHtmlRenderer,JSONRenderer,PurchaseHtmlRenderer
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
    url(r'csv/(?P<id>\d{1,20})/','download_purchase_file',name='purchase_to_csv'),
    url(r'item/del/','delete_purchase_item',name='del_purchase_item')
)