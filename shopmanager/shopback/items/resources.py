__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from shopback.items.models import Product,Item
from shopback.items.serializer import ProductSerializer,ItemSerializer

class ProductListResource(ModelResource):
    """ docstring for ProductList ModelResource """

    model = Product
    fields = ('outer_id','name','category','collect_num','collect_num','warn_num','price','modified','sync_stock','out_stock'
               ,('prod_skus','ProductSerializer')) 
    exclude = ('url','status',)
    
    
class ProductItemResource(ModelResource):
    """ docstring for ProductItem ModelResource """

    model = Item
    fields = (('items','ItemSerializer'),'layer_table') 
    exclude = ('url',)
    