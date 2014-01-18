from django.db import transaction
from shopback.purchases.models import PurchaseItem,PurchaseStorageItem,\
    PurchaseStorageRelationship,PurchasePaymentItem
from shopback.items.models import Product,ProductSku

@transaction.commit_on_success
def repair_purchase_item():
    
    items = PurchaseItem.objects.all()
    for item in items:
        
        product     = None
        product_sku = None
        try:
            product = Product.objects.get(outer_id=item.outer_id)
            if item.outer_sku_id or product.prod_skus.count()>0:
                product_sku = ProductSku.objects.get(outer_id=item.outer_sku_id,product=product)
            item.product_id = product.id
            item.sku_id     = product_sku and product_sku.id or None
            item.save()
        except Exception,exc:
            print  'purchase:',item.purchase.id,item.outer_id,item.outer_sku_id,exc.message
        
@transaction.commit_on_success   
def repair_storage_item():
    
    items = PurchaseStorageItem.objects.all()
    for item in items:
        product     = None
        product_sku = None
        try:
            product = Product.objects.get(outer_id=item.outer_id)
            if item.outer_sku_id or product.prod_skus.count()>0:
                product_sku = ProductSku.objects.get(outer_id=item.outer_sku_id,product=product)
            item.product_id = product.id
            item.sku_id     = product_sku and product_sku.id or None
            item.save()
        except Exception,exc:
            print 'storage:',item.purchase_storage.id,item.outer_id,item.outer_sku_id,exc.message
            
            
@transaction.commit_on_success    
def repair_relationship_item():
    
    items = PurchaseStorageRelationship.objects.all()
    for item in items:
        
        product     = None
        product_sku = None
        try:
            product = Product.objects.get(outer_id=item.outer_id)
            if item.outer_sku_id or product.prod_skus.count()>0:
                product_sku = ProductSku.objects.get(outer_id=item.outer_sku_id,product=product)
            item.product_id = product.id
            item.sku_id     = product_sku and product_sku.id or None
            item.save()
        except Exception,exc:
            print 'relationship:',item.purchase_id,item.storage_id,item.outer_id,item.outer_sku_id,exc.message
    
@transaction.commit_on_success    
def repair_payment_item():
    
    items = PurchasePaymentItem.objects.all()
    for item in items:
        
        product     = None
        product_sku = None
        try:
            product = Product.objects.get(outer_id=item.outer_id)
            if item.outer_sku_id or product.prod_skus.count()>0:
                product_sku = ProductSku.objects.get(outer_id=item.outer_sku_id,product=product)
            item.product_id = product.id
            item.sku_id     = product_sku and product_sku.id or None
            item.save()
        except Exception,exc:
            print 'payment:',item.purchase_id,item.storage_id,item.outer_id,item.outer_sku_id,exc.message

if __name__ == '__main__':
    
    repair_purchase_item()
    repair_storage_item()
    repair_relationship_item()
    repair_payment_item()
    
