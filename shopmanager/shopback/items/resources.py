__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from shopback.items.models import Product,ProductSku,Item
from shopback.items.serializer import ProductSerializer,ItemSerializer

class ProductListResource(ModelResource):
    """ docstring for ProductList ModelResource """

    model = Product
    fields = ('id','outer_id','name','category','collect_num','warn_num','price','modified','sync_stock','out_stock'
               ,('pskus','ProductSerializer'),'purchase_product','status') 
    exclude = ('url',)
    
class ProductResource(ModelResource):
    """ docstring for ProductList ModelResource """

    model = Product
    fields = ('outer_id','name','category','collect_num','warn_num','price','modified','sync_stock','out_stock'
               ,('prod_skus','ProductSerializer'),'purchase_product','status') 
    exclude = ('url',)
    
class ProductItemResource(ModelResource):
    """ docstring for ProductItem ModelResource """

    model = Item
    fields = (('itemobjs','ItemSerializer'),'layer_table','updates_num') 
    exclude = ('url',)
    
class ProductSkuResource(ModelResource):
    """ docstring for ProductItem ModelResource """

    model = ProductSku
    fields = ('outer_id','prod_outer_id','product','purchase_product_sku','quantity','warn_num','remain_num','properties_name'
              ,'out_stock','sync_stock','is_assign','status','layer_table') 
    exclude = ('url',)
    