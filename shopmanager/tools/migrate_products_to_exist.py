import re
from shopback.items.models import Product,ProductSku,ProductLocation as PL

def copy_location(fm_outer_id,fm_sku_id,to_outer_id,to_sku_id):
    
    fm_loc = PL.objects.get(outer_id=fm_outer_id,outer_sku_id=fm_sku_id)
    to_loc,state = PL.objects.get_or_create(outer_id=to_outer_id,
                                          outer_sku_id=to_sku_id,
                                          district=fm_loc.district)
    to_loc.name            = fm_loc.name
    to_loc.properties_name = fm_loc.properties_name
    to_loc.save()
    
    print 'district:',fm_outer_id,fm_sku_id,fm_loc.district \
        ,'=====>',to_outer_id,to_sku_id,to_loc.district


def reverse_migrate(from_id,to_id,reg='[\w]*O$'):
    #根据已合并的商品规格编码将原商品的规格条码，库位，库存等信息覆盖更新
    fskus = Product.objects.get(outer_id=from_id).pskus
    tskus = Product.objects.get(outer_id=to_id).pskus
    
    c  = re.compile(reg)
    for sku in fskus:
        if not c.match(sku.outer_id): continue
        
        to_sku_id = sku.outer_id[0:-1]
        
        to_sku = ProductSku.objects.get(product__outer_id=to_id,outer_id=to_sku_id)
        
        sku.quantity       = to_sku.quantity
        sku.warn_num       = to_sku.warn_num
        sku.remain_num     = to_sku.remain_num
        sku.wait_post_num  = to_sku.wait_post_num
        
        sku.cost = to_sku.cost
        sku.std_sale_price   = to_sku.std_sale_price
        
        sku.post_check = to_sku.post_check
        sku.barcode   = to_sku.barcode
        
        sku.save()
        try:
            copy_location(to_id,to_sku.outer_id,from_id,sku.outer_id)
        except Exception,exc:
            print 'reverse product location',exc.message
            

def map_migrate(from_id,to_id,SKU_MAP={}):
    #根据已合并的商品规格编码将原商品的规格条码，库位，库存等信息覆盖更新
    fskus = Product.objects.get(outer_id=from_id).pskus
    tskus = Product.objects.get(outer_id=to_id).pskus
    
    for sku in fskus:
        if not SKU_MAP.has_key(sku.outer_id):continue
        
        to_sku_id = SKU_MAP.get(sku.outer_id)
        
        to_sku = ProductSku.objects.get(product__outer_id=to_id,outer_id=to_sku_id)
        
        sku.quantity       = to_sku.quantity
        sku.warn_num       = to_sku.warn_num
        sku.remain_num     = to_sku.remain_num
        sku.wait_post_num  = to_sku.wait_post_num
        
        sku.cost = to_sku.cost
        sku.std_sale_price   = to_sku.std_sale_price
        
        sku.post_check = to_sku.post_check
        sku.barcode   = to_sku.barcode
        
        sku.save()
        try:
            copy_location(to_id,to_sku.outer_id,from_id,sku.outer_id)
        except Exception,exc:
            print 'reverse product location',exc.message
            
            
def copy_migrate(from_id,to_id,suffix='O'):
    #将原编码的商品规格编码，及库存，库位等信息更新至新编码
    fskus = Product.objects.get(outer_id=from_id).pskus
    tskus = Product.objects.get(outer_id=to_id).pskus
    
    c  = re.compile(reg)
    for sku in fskus:
        
        if not sku.outer_id:continue
        to_sku_id = sku.outer_id+suffix
        
        to_sku,state = ProductSku.objects.get_or_create(product__outer_id=to_id,
                                                  outer_id=to_sku_id)
        
        to_sku.properties_name  = sku.properties_name
        to_sku.properties_alias = sku.properties_alias
        to_sku.quantity       = sku.quantity
        to_sku.warn_num       = sku.warn_num
        to_sku.remain_num     = sku.remain_num
        to_sku.wait_post_num  = sku.wait_post_num
        
        to_sku.cost = sku.cost
        to_sku.std_sale_price   = sku.std_sale_price
        
        to_sku.post_check = sku.post_check
        to_sku.barcode   = sku.barcode
        
        to_sku.save()
        try:
            copy_location(from_id,sku.outer_id,to_id,to_sku_id)
        except Exception,exc:
            print 'copy product location',exc.message
        
        
        
    