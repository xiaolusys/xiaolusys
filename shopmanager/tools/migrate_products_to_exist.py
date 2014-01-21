import re
from shopback.items.models import Product,ProductSku,ProductLocation

def copy_location(fm_outer_id,fm_sku_id,to_outer_id,to_sku_id):
    
    fm_loc = ProductLocation.objects.get(outer_id=fm_outer_id,outer_sku_id=fm_sku_id)
    to_loc,state = ProductLocation.objects.get_or_create(outer_id=to_outer_id,
                                          outer_sku_id=to_sku_id,
                                          district=fm_loc.district)
    to_loc.name            = fm_loc.name
    to_loc.properties_name = fm_loc.properties_name
    to_loc.save()
    
    print 'district:',fm_outer_id,fm_sku_id,fm_loc.district
    print 'to:',state,to_outer_id,to_sku_id,to_loc.district

def migrate(from_id,to_id,reg='[\w]*O$'):
    
    fskus = Product.objects.get(outer_id=from_id).pskus
    tskus = Product.objects.get(outer_id=to_id).pskus
    
    c  = re.compile(reg)
    for sku in fskus:
        if not c.match(sku.outer_id): continue
        
        to_sku_id = sku.outer_id[0:-1]
        
        to_sku = ProductSku.objects.get(product__outer_id=to_id,outer_id=to_sku_id)
        
        sku.quantity   = to_sku.quantity
        sku.warn_num   = to_sku.warn_num
        sku.remain_num = to_sku.remain_num
        sku.wait_post_num   = to_sku.wait_post_num
        
        sku.cost = to_sku.cost
        sku.std_sale_price   = to_sku.std_sale_price
        
        sku.post_check = to_sku.post_check
        sku.barcode   = to_sku.barcode
        
        sku.save()
        try:
            copy_location(to_id,to_sku.outer_id,from_id,sku.outer_id)
        except Exception,exc:
            print 'cp product location',exc.message
        
        
        
    