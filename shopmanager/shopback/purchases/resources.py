__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from shopback.items.models import Product,ProductSku
from shopback.purchases.serializer import ProductSkuSerializer

class PurchaseItemResource(ModelResource):
    """ docstring for PurchaseItem ModelResource """

    model = Product
    fields = (('purchase_item',ProductSkuSerializer),'layer_table') 
    exclude = ('url',)