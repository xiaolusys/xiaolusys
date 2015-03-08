from django.conf.urls.defaults import patterns, url
from django.views.generic import TemplateView
from shopback.items.views import (ProductListView,
                                  ProductItemView,
                                  ProductModifyView,
                                  ProductUpdateView,
                                  ProductSkuCreateView,
                                  ProductSkuInstanceView,
                                  ProductSearchView,
                                  ProductDistrictView,
                                  ProductBarCodeView,
                                  ProductWarnMgrView,
                                  ProductNumAssignView,
                                  ProductOrSkuStatusMdView,
                                  ProductView,
                                  ProductSkuView,
                                  StatProductSaleView,)
from shopback.items.resources import ProductListResource,ProductItemResource,ProductResource,\
    ProductSkuResource,ProductDistrictResource,ProductDaySaleResource
from shopback.items.renderers import (ProductListHtmlRenderer,
                                      JSONRenderer,
                                      ProductItemHtmlRenderer,
                                      ProductUpdateHtmlRenderer,
                                      ProductSkuHtmlRenderer,
                                      ProductDistrictHtmlRenderer,
                                      ProductHtmlRenderer,
                                      ProductBarcodeHtmlRenderer,
                                      ProductWarnHtmlRenderer,
                                      ProductSaleHtmlRenderer,)
from shopback.base.renderers  import BaseJsonRenderer
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication,login_required_ajax


urlpatterns = patterns('shopback.items.views',

    url('update/items/$','update_user_items',name='update_items'),
    url('update/item/$','update_user_item',name='update_item'),
    url('update/stock/$','update_product_stock',name='update_stock'),
    url('district/query/$','deposite_district_query',name='query_district'),
    url('product/district/delete/$','delete_product_district',name='delete_district'),
    (r'^split/$',TemplateView.as_view(template_name="items/split_product_template.html")),
    (r'^product/(?P<id>[0-9]+)/$',ProductView.as_view(
        resource=ProductResource,
        renderers=(ProductHtmlRenderer,BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^product/(?P<pid>[0-9]+)/(?P<sku_id>[0-9]+)/$',ProductSkuView.as_view(
        resource=ProductSkuResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
                       
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
    (r'^product/barcode/$',ProductBarCodeView.as_view(
        resource=ProductResource,
        renderers=(BaseJsonRenderer,ProductBarcodeHtmlRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^product/district/(?P<id>[0-9]+)/$',ProductDistrictView.as_view(
        resource=ProductDistrictResource,
        renderers=(BaseJsonRenderer,ProductDistrictHtmlRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^podorsku/status/$',ProductOrSkuStatusMdView.as_view(
        resource=ProductResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),                
    (r'^product/warn/$',ProductWarnMgrView.as_view(
        resource=ProductResource,
        renderers=(BaseJsonRenderer,ProductWarnHtmlRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),   
    (r'^product/assign/$',ProductNumAssignView.as_view(
        resource=ProductResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
     (r'^product/sale/$',StatProductSaleView.as_view(
        resource=ProductDaySaleResource,
        renderers=(BaseJsonRenderer,ProductSaleHtmlRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    
    url(r'^test/$', TemplateView.as_view(
        template_name="items/product_sku_diff.html"), 
        name='test_diff'),
    #(r'^product_lookup/$', 'shopback.items.views.json_lookup', product_lookup),
)
