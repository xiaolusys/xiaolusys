from .models import ProductDaySale,Product

def updateProductDaySaleOuterid():
    
    pss = ProductDaySale.objects.all()
    product_ids = [p['product_id'] for p in pss.values('product_id').distinct()]
    cnt = 0
    print 'debug total:',len(product_ids)
    for pid in product_ids:
        try:
            product = Product.objects.get(id=pid)
        except:
            continue
        pss.filter(product_id=pid).update(outer_id=product.outer_id)
        
        cnt += 1
        if cnt % 1000 == 0:
            print cnt