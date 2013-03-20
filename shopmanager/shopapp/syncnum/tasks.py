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
from shopback.items.tasks import updateUserItemsTask,updateUserProductSkuTask,updateProductWaitPostNumTask
from shopback.orders.models import Order,Trade
from shopback.trades.models import MergeOrder
from shopback.users.models import User
from shopapp.syncnum.models import ItemNumTaskLog
from auth.utils import get_yesterday_interval_time
from auth import apis
import logging

logger = logging.getLogger('syncnum.handler')

@transaction.commit_on_success
def updateItemNum(user_id,num_iid):
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
    
    outer_id = product.outer_id
    skus = json.loads(item.skus) if item.skus else None
    if skus:
        for sku in skus.get('sku',[]):
            
            outer_sku_id = sku.get('outer_id','')
            if sku['status'] != pcfg.NORMAL or not outer_sku_id:
                continue
            product_sku  = product.prod_skus.get(outer_id=outer_sku_id)
            
            order_nums  = 0
            wait_nums   = product_sku.wait_post_num>0 and product_sku.wait_post_num or 0
            remain_nums = product_sku.remain_num or 0
            real_num    = product_sku.quantity
            sync_num    = real_num - wait_nums - remain_nums
            
            #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
            if  sync_num != sku['quantity'] and sync_num > product_sku.warn_num:
                product_sku.is_assign = False
            elif sync_num >0 and sync_num <= product_sku.warn_num:
                user_order_num,total_num = MergeOrder.get_yesterday_orders_totalnum(item.user.id,outer_id,outer_sku_id)
                if total_num>0 and user_order_num>0:
                    sync_num = round(float(user_order_num/total_num)*sync_num)
                elif total_num == 0:
                    item_count = Item.objects.filter(outer_id=outer_id,approve_status=pcfg.ONSALE_STATUS).count() or 1
                    sync_num = sync_num/item_count or sync_num
                else:
                    sync_num = 2
            else:
                sync_num = 0
                
            if sync_num >0 and product_sku.sync_stock:
                sync_num = int(sync_num)
                response = apis.taobao_item_quantity_update\
                        (num_iid=item.num_iid,quantity=sync_num,outer_id=outer_sku_id,tb_user_id=user_id)
                item_dict = response['item_quantity_update_response']['item']
                Item.objects.filter(num_iid=item_dict['num_iid']).update(modified=item_dict['modified'],num=item_dict['num'])

                product_sku.save()
                ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                             outer_id=product.outer_id,
                                             sku_outer_id= outer_sku_id,
                                             num=sync_num,
                                             start_at= item.last_num_updated,
                                             end_at=datetime.datetime.now())
            
    else:
        order_nums    = 0
        outer_sku_id  = ''
        wait_nums  = product.wait_post_num >0 and product.wait_post_num or 0
        remain_nums = product.remain_num or 0
        real_num   = product.collect_num
        sync_num   = real_num - wait_nums - remain_nums

        #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if sync_num != product.collect_num and sync_num > product.warn_num:
            product.is_assign = False
        elif sync_num >0 and sync_num <= product.warn_num:
            user_order_num,total_num = MergeOrder.get_yesterday_orders_totalnum(item.user.id,outer_id,outer_sku_id)
            if total_num>0 and user_order_num>0:
                sync_num = round(float(user_order_num/total_num)*sync_num)
            elif total_num == 0:
                item_count = Item.objects.filter(outer_id=outer_id,approve_status=pcfg.ONSALE_STATUS).count() or 1
                sync_num = sync_num/item_count or sync_num
            else:
                sync_num = 2
        else:
            sync_num = 0    
            
        if sync_num > 0 and product.sync_stock: 
            sync_num = int(sync_num)   
            response = apis.taobao_item_update(num_iid=item.num_iid,num=sync_num,tb_user_id=user_id)
            item_dict = response['item_update_response']['item']
            Item.objects.filter(num_iid=item_dict['num_iid']).update(modified=item_dict['modified'],num=item_dict['num'])

            product.save()
            
            ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                             outer_id=product.outer_id,
                                             num=sync_num,
                                             start_at= item.last_num_updated,
                                             end_at=datetime.datetime.now())
  
    
    Item.objects.filter(num_iid=item.num_iid).update(last_num_updated=datetime.datetime.now())


@task()
def updateUserItemNumTask(user_id):
    
    updateUserItemsTask(user_id)
    updateUserProductSkuTask(user_id)
        
    items = Item.objects.filter(user__visitor_id=user_id,approve_status=pcfg.ONSALE_STATUS)
    for item in items:
        try:
            updateItemNum(user_id,item.num_iid)
        except Exception,exc :
            logger.error('%s'%exc,exc_info=True)
        

@task()
def updateAllUserItemNumTask():
    
    updateProductWaitPostNumTask()

    users = User.objects.all()
    for user in users:
        updateUserItemNumTask(user.visitor_id)
        
        