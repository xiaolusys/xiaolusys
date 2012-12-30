#-*- coding:utf8 -*-
import datetime
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Sum
from django.db import transaction
from auth.utils import format_datetime ,parse_datetime
from shopback import paramconfig as pcfg
from shopback.items.models import Item
from shopback.items.tasks import updateUserItemsTask,updateUserProductSkuTask
from shopback.orders.models import Order,Trade
from shopback.users.models import User
from shopapp.syncnum.models import ItemNumTaskLog
from auth import apis
import logging

logger = logging.getLogger('syncnum.handler')

@transaction.commit_on_success
def updateItemNum(user_id,num_iid,update_time):
    """
    taobao_item_quantity_update response:
    {'iid': '21557036378',
    'modified': '2012-12-26 12:51:16',
    'num': 24,
    'num_iid': 21557036378,
    'skus': {'sku': ({'modified': <type 'str'>,
                      'quantity': <type 'int'>,
                      'sku_id': <type 'int'>},
                     {'modified': <type 'str'>,
                      'quantity': <type 'int'>,
                      'sku_id': <type 'int'>})}}
    """
    item = Item.objects.get(num_iid=num_iid)
    product = item.product
    if not product:
        return
    
    skus = json.loads(item.skus) if item.skus else None
    if skus:
        for sku in skus.get('sku',[]):
            outer_sku_id = sku.get('outer_id','')
            product_sku  = product.prod_skus.get(outer_id=outer_sku_id)
            
            order_nums = 0
            if product.modified < update_time:     
                wait_nums = Order.objects.filter(outer_id=product.outer_id,outer_sku_id=outer_sku_id,status=pcfg.WAIT_SELLER_SEND_GOODS)\
                    .aggregate(sale_nums=Sum('num')).get('sale_nums')
                wait_nums   = wait_nums or 0
                remain_nums = product_sku.remain_num or 0
                real_num   = product_sku.quantity
                sync_num   = real_num - wait_nums - remain_nums
            else:
                real_num = product_sku.quantity
                sync_num = real_num
            
            #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
            if product_sku.sync_stock and sync_num != sku['quantity']:
                response = apis.taobao_item_quantity_update\
                        (num_iid=item.num_iid,quantity=real_num,outer_id=outer_sku_id,tb_user_id=user_id)
                item_dict = response['item_quantity_update_response']['item']
                Item.objects.filter(num_iid=item_dict['num_iid']).update(modified=item_dict['modified'],num=item_dict['num'])
                
                product_sku.quantity = real_num
                product_sku.save()
                ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                             outer_id=product.outer_id,
                                             sku_outer_id= outer_sku_id,
                                             num=sync_num,
                                             start_at= item.last_num_updated,
                                             end_at=update_time )
    else:
        order_nums = 0
        if product.modified < update_time:
            wait_nums = Order.objects.filter(outer_id=product.outer_id,status=pcfg.WAIT_SELLER_SEND_GOODS)\
                    .aggregate(sale_nums=Sum('num')).get('sale_nums')

            wait_nums  = wait_nums or 0
            remain_nums = product.remain_num or 0
            real_num   = product.collect_num
            sync_num   = real_num - wait_nums - remain_nums
        else:
            real_num = product.collect_num
            sync_num = real_num
        #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if product.sync_stock and sync_num != product.collect_num:
            response = apis.taobao_item_quantity_update(num_iid=item.num_iid,quantity=sync_num,tb_user_id=user_id)
            item_dict = response['item_update_response']['item']
            Item.objects.filter(num_iid=item_dict['num_iid']).update(modified=item_dict['modified'],num=item_dict['num'])
        
            product.collect_num = real_num
            product.save()
            
            ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                             outer_id=product.outer_id,
                                             num=sync_num,
                                             start_at= item.last_num_updated,
                                             end_at=update_time )
    
    Item.objects.filter(num_iid=item.num_iid).update(last_num_updated=update_time)


@task()
def updateUserItemNumTask(user_id,update_time):
    
    updateUserItemsTask(user_id)
    updateUserProductSkuTask(user_id)

    items = Item.objects.filter(user__visitor_id=user_id,approve_status=pcfg.ONSALE_STATUS)
    for item in items:
        try:
            updateItemNum(user_id,item.num_iid,update_time)
        except Exception,exc :
            logger.error('%s'%exc,exc_info=True)
        

@task()
def updateAllUserItemNumTask():
    
    dt = datetime.datetime.now()
    users = User.objects.all()
    for user in users:
        updateUserItemNumTask(user.visitor_id,dt)
        
        