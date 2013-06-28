__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from shopback.items.models import Product,ProductSku
from shopback.purchases.models import Purchase,PurchaseItem
from shopback.purchases.serializer import ProductSkuSerializer


class PurchaseItemResource(ModelResource):
    """ docstring for PurchaseItem ModelResource """

    model = Product
    fields = ('id','outer_id','name','outer_sku_id','properties_name','price','purchase_num') 
    exclude = ('url',)
    
    
class PurchaseResource(ModelResource):
    """ docstring for PurchaseResource ModelResource """

    model = Purchase
    fields = ('suppliers','deposites','purchase_types','id','purchase') 
    exclude = ('url',)