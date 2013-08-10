from django.conf.urls.defaults import patterns, url
from djangorestframework.views import ListOrCreateModelView
from shopback.items.views import ProductListView,ProductItemView,ProductModifyView,ProductUpdateView,\
    ProductSkuCreateView,ProductSkuInstanceView,ProductSearchView,ProductDistrictView
from shopback.items.resources import ProductListResource,ProductItemResource,ProductResource,\
    ProductSkuResource,ProductDistrictResource
from shopback.items.renderers import ProductListHtmlRenderer,JSONRenderer,ProductItemHtmlRenderer,\
    ProductUpdateHtmlRenderer,ProductSkuHtmlRenderer,ProductDistrictHtmlRenderer
from shopback.base.renderers  import BaseJsonRenderer
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication,login_required_ajax

urlpatterns = patterns('shopback.items.views',

    url('update/items/$','update_user_items',name='update_items'),
    url('update/item/$','update_user_item',name='update_item'),
    url('update/stock/$','update_product_stock',name='update_stock'),
    url('district/query/$','deposite_district_query',name='query_district'),
    url('product/district/delete/$','delete_product_district',name='delete_district'),
    
    (r'^product/$',ProductListView.as_view(
        resource=ProductListResource,
        renderers=(ProductListHtmlRenderer,JSONRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^product/item/(?P<outer_id>[\w^_]+)/$',ProductItemView.as_view(
        resource=ProductItemResource,
        renderers=(ProductItemHtmlRenderer,JSONRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^product/modify/(?P<outer_id>[\w^_]+)/$',ProductModifyView.as_view(
        resource=ProductItemResource,
        renderers=(JSONRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^product/update/(?P<outer_id>[\w^_]+)/$',ProductUpdateView.as_view(
        resource=ProductResource,
        renderers=(ProductUpdateHtmlRenderer,JSONRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^product/sku/(?P<sku_id>[\w^_]+)/$',ProductSkuInstanceView.as_view(
        resource=ProductSkuResource,
        renderers=(ProductSkuHtmlRenderer,JSONRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^query/$',ProductSearchView.as_view(
        resource=ProductResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^product/district/(?P<id>[0-9]+)/$',ProductDistrictView.as_view(
        resource=ProductDistrictResource,
        renderers=(BaseJsonRenderer,ProductDistrictHtmlRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),              
    #(r'^product_lookup/$', 'shopback.items.views.json_lookup', product_lookup),
)
