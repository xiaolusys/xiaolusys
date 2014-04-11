from shopback.items.models import Product,ProductSku,ProductLocation


def md_identity():
    
    plocs = ProductLocation.objects.all()
    invalid_set = set()
    for pl in plocs:
        outer_id  = pl.outer_id
        outer_sku_id = pl.outer_sku_id
        try:
            prod = Product.objects.get(outer_id=outer_id)
            prod_sku = None
            if outer_sku_id:
                prod_sku = ProductSku.objects.get(outer_id=outer_sku_id,product=prod)
        except (Product.DoesNotExist,ProductSku.DoesNotExist):
            invalid_set.add(pl.id)
            continue
        
        pl.product_id = prod.id
        pl.sku_id     = prod_sku.id
        pl.save()
        
    print 'invalid ids:',invalid_set
    print 'delete rows:',ProductLocation.objects.filter(id__in=invalid_set).delete()
    
    