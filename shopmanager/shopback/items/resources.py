__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from shopback.items.models import Product,Item
from shopback.items.serializer import ProductSerializer,UserSerializer

class ProductListResource(ModelResource):
    """ docstring for ProductList ModelResource """

    model = Product
    fields = ('outer_id','name','category','collect_num','collect_num','warn_num','price','modified','sync_stock','out_stock'
               ,('prod_skus','ProductSerializer')) 
    exclude = ('url','status',)
    
    
class ProductItemResource(ModelResource):
    """ docstring for ProductItem ModelResource """

    model = Item
    fields = ('num_iid',('user','UserSerializer'),'category','type','outer_id','num','approve_status','valid_thru','price','postage_id','has_showcase','modified'
               ,'list_time','delist_time','has_discount','title','pic_url','detail_url','last_num_updated','status','sku_list') 
    exclude = ('url','skus')
    