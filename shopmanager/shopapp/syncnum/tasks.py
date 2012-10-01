#-*- coding:utf8 -*-
import datetime
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Sum
from django.db import transaction
from auth.utils import format_datetime ,parse_datetime
from shopback.items.models import Item,ONSALE_STATUS
from shopback.items.tasks import updateUserItemsTask,updateUserProductSkuTask
from shopback.orders.models import Order,Trade,ORDER_SUCCESS_STATUS,ORDER_UNPAY_STATUS,ORDER_POST_STATUS,WAIT_SELLER_SEND_GOODS
from shopback.users.models import User
from shopapp.syncnum.models import ItemNumTaskLog
from auth import apis
import logging

logger = logging.getLogger('syncnum.handler')

@transaction.commit_on_success
def updateItemNum(num_iid,update_time):
    
    item = Item.objects.get(num_iid=num_iid)
    product = item.product
    if not product:
        return
    
    skus = json.loads(item.skus) if item.skus else None
    if skus:
        for sku in skus.get('sku',[]):
            outer_sku_id = sku.get('outer_id','')
            product_sku = product.prod_skus.get(outer_id=outer_sku_id)
            
            order_nums = 0
            if product.modified < update_time:
                order_nums = Order.objects.filter(outer_id=product.outer_id,outer_sku_id=outer_sku_id,status__in=ORDER_POST_STATUS)\
                    .filter(consign_time__gte=item.last_num_updated,consign_time__lt=update_time)\
                    .aggregate(sale_nums=Sum('num')).get('sale_nums')
                       
                wait_nums = Order.objects.filter(outer_id=product.outer_id,outer_sku_id=outer_sku_id,status=WAIT_SELLER_SEND_GOODS)\
                    .aggregate(sale_nums=Sum('num')).get('sale_nums')
                order_nums  = order_nums or 0
                wait_nums   = wait_nums or 0
                remain_nums = product_sku.remain_num or 0
                real_num   = product_sku.quantity - order_nums 
                sync_num   = real_num - wait_nums - remain_nums
            else:
                real_num = product_sku.quantity
            
            #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
            if product_sku.sync_stock and sync_num != sku['quantity']:
                response = apis.taobao_item_quantity_update\
                        (num_iid=item.num_iid,quantity=real_num,sku_id=outer_sku_id,tb_user_id=user_id)
                item_dict = response['item_quantity_update_response']['item']
                Item.save_item_through_dict(user_id,item_dict)
                
                product_sku.setQuantity(real_num)
                ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                             outer_id=product.outer_id,
                                             sku_outer_id= outer_sku_id,
                                             num=sync_num,
                                             start_at= item.last_num_updated,
                                             end_at=update_time )
            #如果不同步
            elif not product_sku.sync_stock and order_nums > 0:
                product_sku.setQuantity(real_num)
    else:
        order_nums = 0
        if product.modified < update_time:
            order_nums = Order.objects.filter(outer_id=product.outer_id,status__in=ORDER_POST_STATUS)\
                    .filter(consign_time__gte=item.last_num_updated,consign_time__lt=update_time)\
                    .aggregate(sale_nums=Sum('num')).get('sale_nums')
            
            wait_nums = Order.objects.filter(outer_id=product.outer_id,status=WAIT_SELLER_SEND_GOODS)\
                    .aggregate(sale_nums=Sum('num')).get('sale_nums')
                    
            order_nums = order_nums or 0  
            wait_nums  = wait_nums or 0
            remain_nums = product.remain_num or 0
            real_num   = product.collect_num - order_nums
            sync_num   = real_num - wait_nums - remain_nums
        else:
            real_num = product.collect_num
        #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if product.sync_stock and sync_num != product.collect_num:
            response = apis.taobao_item_update(num_iid=item.num_iid,num=sync_num,tb_user_id=user_id)
            item_dict = response['item_update_response']['item']
            Item.save_item_through_dict(user_id,item_dict)
        
            product.collect_num = real_num
            product.save()
            
            ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                             outer_id=product.outer_id,
                                             num=sync_num,
                                             start_at= item.last_num_updated,
                                             end_at=update_time )
        elif not product.sync_stock and order_nums > 0:
            product.collect_num = real_num
            product.save()
    
    Item.objects.filter(num_iid=item.num_iid).update(last_num_updated=update_time)


@task()
def updateUserItemNumTask(user_id,update_time):
    
    updateUserItemsTask(user_id)
    updateUserProductSkuTask(user_id)

    items = Item.objects.filter(user__visitor_id=user_id,approve_status=ONSALE_STATUS)
    for item in items:
        try:
            updateItemNum(item.num_iid,update_time)
        except Exception,exc :
            logger.error('%s'%exc,exc_info=True)
        

@task()
def updateAllUserItemNumTask():
    
    dt = datetime.datetime.now()
    users = User.objects.all()
    for user in users:
        updateUserItemNumTask(user.visitor_id,dt)
        
        