import sys
import time
import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from shopapp.weixin.models import WXProductSku,WXProduct
from shopback.items.models import Product

def refresh_wxproduct():
    
    update_wxpids = set([])
    wx_skus = WXProductSku.objects.values('outer_id').distinct()
    
    for wx_sku in wx_skus:
        wx_outer_id = wx_sku['outer_id']
        print 'outer_id:',wx_outer_id
        products = Product.objects.filter(outer_id=wx_outer_id)
        if products.count() == 0:
            continue
        p = products[0]
        pskus = WXProductSku.objects.filter(outer_id=wx_outer_id)
        pskus.update(created=p.created,modified=p.modified)
        
        pskus = WXProductSku.objects.filter(outer_id=wx_outer_id).values('product').distinct()
        for product in pskus:
            
            product_id = product['product']
            if product_id in update_wxpids:
                continue
            
            update_wxpids.add(product_id)
            wx_prod = WXProduct.objects.get(product_id=product_id)
            wx_prod.created = p.created
            wx_prod.modified = p.modified
            wx_prod.save()
        
    
if __name__ == "__main__":
    
    if len(sys.argv) != 1:
        print >> sys.stderr, "usage: python *.py <outer_ids> "
    
    refresh_wxproduct()
    
    
