from shopback.items.models import Product,ProductSku
from shopapp.memorule.models import ComposeRule,ComposeItem

def splitOrders(fouter_id,fsku_id,pouter_id,psku_id):
    
    prod = Product.objects.get(outer_id=fouter_id)
    prod_sku = None
    
    dsku     = ProductSku.objects.get(product__outer_id=pouter_id,outer_id=psku_id)
    
    if fsku_id:
        prod_sku = ProductSku.objects.get(product=prod,outer_id=fsku_id)
        
        rule = ComposeRule.objects.create(outer_id=prod.outer_id,
                                          outer_sku_id=prod_sku.outer_id,
                                          type='product',
                                          extra_info='%s+%s'%(prod.name,prod_sku.name))
        
        ComposeItem.objects.create(compose_rule=rule,
                                   outer_id=pouter_id,
                                   outer_sku_id=psku_id,
                                   num=1,
                                   extra_info=dsku.name)
        ComposeItem.objects.create(compose_rule=rule,
                                   outer_id=prod.outer_id,
                                   outer_sku_id=prod_sku.outer_id,
                                   num=1,
                                   extra_info=prod_sku.name)
    else:
        for prod_sku in prod.eskus:
            rule = ComposeRule.objects.create(outer_id=prod.outer_id,
                                              outer_sku_id=prod_sku.outer_id,
                                              type='product',
                                              extra_info='%s+%s'%(prod.name,prod_sku.name))
        
            ComposeItem.objects.create(compose_rule=rule,
                                       outer_id=pouter_id,
                                       outer_sku_id=psku_id,
                                       num=1,
                                       extra_info=dsku.name)
            ComposeItem.objects.create(compose_rule=rule,
                                       outer_id=prod.outer_id,
                                       outer_sku_id=prod_sku.outer_id,
                                       num=1,
                                       extra_info=prod_sku.name)
            
            
            