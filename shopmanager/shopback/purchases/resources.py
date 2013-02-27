__author__ = 'meixqhi'
from djangorestframework.resources import ModelResource
from shopback.items.models import PurchaseProduct,PurchaseProductSku
from shopback.purchases.serializer import PurchaseProductSkuSerializer

class PurchaseItemResource(ModelResource):
    """ docstring for PurchaseItem ModelResource """

    model = PurchaseProduct
    fields = (('purchase_item',PurchaseProductSkuSerializer),'layer_table') 
    exclude = ('url',)