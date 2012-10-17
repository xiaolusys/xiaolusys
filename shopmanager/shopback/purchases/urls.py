from django.conf.urls.defaults import patterns, url
from shopback.purchases.views import PurchaseItemView
from shopback.purchases.resources import PurchaseItemResource
from shopback.purchases.renderers import PurchaseItemHtmlRenderer,JSONRenderer


urlpatterns = patterns('shopback.purchases.views',
    
    (r'^(?P<id>\d+)/$',PurchaseItemView.as_view(
        resource=PurchaseItemResource,
        renderers=(PurchaseItemHtmlRenderer,JSONRenderer),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),

)