from django.conf.urls.defaults import patterns, url
from shopback.items.views import ProductListView
from shopback.items.resources import ProductListResource,ProductItemResource
from shopback.items.renderers import ProductListHtmlRenderer,JSONRenderer


urlpatterns = patterns('shopback.items.views',

    url('update/items/$','update_user_items',name='update_items'),
    url('update/item/$','update_user_item',name='update_item'),
    
    (r'^product/$',ProductListView.as_view(
        resource=ProductListResource,
        renderers=(ProductListHtmlRenderer,JSONRenderer),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),
    (r'^product/item/(?P<outer_id>[\w^_]+)/$',ProductListView.as_view(
        resource=ProductItemResource,
        renderers=(JSONRenderer,),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),
)
