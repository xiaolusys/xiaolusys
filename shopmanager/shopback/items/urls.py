from django.conf.urls.defaults import patterns, url
from djangorestframework.views import ListOrCreateModelView
from shopback.items.views import ProductListView,ProductItemView,ProductModifyView,ProductUpdateView,ProductSkuCreateView,ProductSkuInstanceView
from shopback.items.resources import ProductListResource,ProductItemResource,ProductResource,ProductSkuResource
from shopback.items.renderers import ProductListHtmlRenderer,JSONRenderer,ProductItemHtmlRenderer,ProductUpdateHtmlRenderer,ProductSkuHtmlRenderer




urlpatterns = patterns('shopback.items.views',

    url('update/items/$','update_user_items',name='update_items'),
    url('update/item/$','update_user_item',name='update_item'),
    url('update/stock/$','update_product_stock',name='update_stock'),
    
    (r'^product/$',ProductListView.as_view(
        resource=ProductListResource,
        renderers=(ProductListHtmlRenderer,JSONRenderer),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),
    (r'^product/item/(?P<outer_id>[\w^_]+)/$',ProductItemView.as_view(
        resource=ProductItemResource,
        renderers=(ProductItemHtmlRenderer,JSONRenderer,),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),
    (r'^product/modify/(?P<outer_id>[\w^_]+)/$',ProductModifyView.as_view(
        resource=ProductItemResource,
        renderers=(JSONRenderer,),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),
    (r'^product/update/(?P<outer_id>[\w^_]+)/$',ProductUpdateView.as_view(
        resource=ProductResource,
        renderers=(ProductUpdateHtmlRenderer,JSONRenderer,),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),
    (r'^product/sku/(?P<sku_id>[\w^_]+)/$',ProductSkuInstanceView.as_view(
        resource=ProductSkuResource,
        renderers=(ProductSkuHtmlRenderer,JSONRenderer,),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    )),

    #(r'^product_lookup/$', 'shopback.items.views.json_lookup', product_lookup),
)
