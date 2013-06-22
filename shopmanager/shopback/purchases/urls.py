from django.conf.urls.defaults import patterns, url
from shopback.purchases.views import PurchaseItemView,PurchaseInstanceView
from shopback.purchases.resources import PurchaseItemResource,PurchaseResource
from shopback.purchases.renderers import PurchaseItemHtmlRenderer,JSONRenderer,PurchaseHtmlRenderer


urlpatterns = patterns('shopback.purchases.views',
    
    (r'^(?P<id>\d+)/$',PurchaseItemView.as_view(
        resource=PurchaseItemResource,
        renderers=(PurchaseItemHtmlRenderer,JSONRenderer),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),
    (r'^add/$',PurchaseInstanceView.as_view(
        resource=PurchaseResource,
        renderers=(PurchaseHtmlRenderer,JSONRenderer),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),
)