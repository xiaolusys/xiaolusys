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

import datetime            
from django.db import models
from shopback.trades.models import MergeTrade,MergeOrder

def splitOrderByProducts():

     sdt = datetime.datetime(2015,5,4,9)
     morders = MergeOrder.objects.filter(pay_time__gt=sdt,outer_id='10102'
         ,merge_trade__sys_status__in=('WAIT_AUDIT','WAIT_PREPARE_SEND','REGULAR_REMAIN'))
     outer_ids = [['3112BK7','71I',522],['3112BK7','71J',247],['3112BK7','71I2',230]]
     mtids = set([o.merge_trade.id for o in morders])
     print 'merge trade length: %s'%len(mtids)
     cnt = 0
     
     merge_trades = MergeTrade.objects.filter(id__in=mtids).order_by('pay_time')

     for t in merge_trades[10:1100]:
         print 'tid:',t.tid
         order_num = t.merge_orders.filter(outer_id='10102',sys_status='IN_EFFECT').aggregate(total_num=models.Sum('num')).get('total_num')
         if not order_num or order_num == 0:continue

         for tp in outer_ids:
             if tp[2] <= 0 or tp[2] < order_num:continue
             MergeOrder.gen_new_order(t.id,tp[0],tp[1],order_num,
                       gift_type=6,
                       status='WAIT_SELLER_SEND_GOODS',
                       is_reverse=False,payment='0',
                       created=None,
                       pay_time=None)

             cnt += order_num
             tp[2] = tp[2] - order_num
             break
         
         t.buyer_nick = '[L%s]%s'%(cnt,t.buyer_nick)
         t.save()

         if cnt % 100 == 0:
             print 'cnt:',cnt


            
            
