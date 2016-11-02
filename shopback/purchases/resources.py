# __author__ = 'meixqhi'
# from djangorestframework.resources import ModelResource
# from shopback.items.models import Product,ProductSku
# from shopback.purchases.models import Purchase,PurchaseItem,PurchaseStorage,PurchaseStorageItem,PurchasePayment
# from shopback.purchases.serializer import ProductSkuSerializer
# 
# 
# class PurchaseItemResource(ModelResource):
#     """ docstring for PurchaseItem ModelResource """
# 
#     model = PurchaseItem
#     fields = ('id','origin_no','supplier_item_id','product_id','sku_id','outer_id','name',
#               'outer_sku_id','properties_name','std_price','price','purchase_num','total_fee') 
#     exclude = ('url',)
#     
#     
# class PurchaseResource(ModelResource):
#     """ docstring for PurchaseResource ModelResource """
# 
#     model = Purchase
#     fields = ('suppliers','deposites','purchase_types','perms','id','purchase',
#               'unfinish_purchase_items','ship_storages','status') 
#     exclude = ('url',)
#     
#     
# class PurchaseStorageItemResource(ModelResource):
#     """ docstring for PurchaseStorageItemResource ModelResource """
# 
#     model = PurchaseStorageItem
#     fields = ('id','origin_no','supplier_item_id','product_id','sku_id','outer_id','name',
#               'outer_sku_id','properties_name','storage_num') 
#     exclude = ('url',)
#     
#     
# class PurchaseStorageResource(ModelResource):
#     """ docstring for PurchaseStorageResource ModelResource """
# 
#     model = PurchaseStorage
#     fields = ('suppliers','origin_no','deposites','id','status','perms','purchase_storage','undist_storage_items','ship_purchases') 
#     exclude = ('url',)
#     
# 
# class PurchasePaymentResource(ModelResource):
#     """ docstring for PurchasePaymentResource ModelResource """
# 
#     model = PurchasePayment
#     fields = ('purchases','storages','error_msg','purchase_payment','perms','extra_info') 
#     exclude = ('url',)
#     
#
