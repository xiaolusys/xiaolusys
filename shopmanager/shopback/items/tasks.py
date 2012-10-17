#-*- coding:utf8 -*-
import datetime
import time
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from auth.utils import format_datetime ,parse_datetime ,refresh_session
from shopback.items.models import Item,ProductSku,INSTOCK_STATUS,ONSALE_STATUS
from shopback.orders.models import Order,Trade,ORDER_SUCCESS_STATUS,ORDER_UNPAY_STATUS
from shopback.users.models import User
from shopback.base.models   import UNEXECUTE,EXECERROR,SUCCESS
from shopback.fenxiao.tasks import saveUserFenxiaoProductTask
from auth import apis
import logging

logger = logging.getLogger('items.handler')



@task()
def updateUserItemsTask(user_id):

    has_next = True
    cur_page = 1
    onsale_item_ids = []
    #更新出售中的商品
    try:
        while has_next:
          
            response_list = apis.taobao_items_onsale_get(page_no=cur_page,tb_user_id=user_id
                ,page_size=settings.TAOBAO_PAGE_SIZE,fields='num_iid,modified')
    
            item_list = response_list['items_onsale_get_response']
            if item_list['total_results']>0:
                items = item_list['items']['item']
                for item in items:
                    modified = parse_datetime(item['modified']) if item.get('modified',None) else None
                    item_obj,state    = Item.objects.get_or_create(num_iid = item['num_iid'])
                    if modified != item_obj.modified:
                        response = apis.taobao_item_get(num_iid=item['num_iid'],tb_user_id=user_id)
                        item_dict = response['item_get_response']['item']
                        item_dict['skus'] = json.dumps(item_dict.get('skus',{}))
                        Item.save_item_through_dict(user_id,item_dict)
                    onsale_item_ids.append(item['num_iid'])    
    
            total_nums = item_list['total_results']
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums<total_nums
            
            cur_page += 1
    except:
        logger.error('update user onsale items task error',exc_info=True)
    #更新库存中的商品
    try:
        has_next = True
        cur_page = 1    
        while has_next:
          
            response_list = apis.taobao_items_inventory_get(page_no=cur_page,tb_user_id=user_id
                ,page_size=settings.TAOBAO_PAGE_SIZE,fields='num_iid,modified')
    
            item_list = response_list['items_inventory_get_response']
            if item_list['total_results']>0:
                items = item_list['items']['item']
                for item in item_list['items']['item']:
                    modified = parse_datetime(item['modified']) if item.get('modified',None) else None
                    item_obj,state    = Item.objects.get_or_create(num_iid = item['num_iid'])
                    if modified != item_obj.modified:
                        response = apis.taobao_item_get(num_iid=item['num_iid'],tb_user_id=user_id)
                        item_dict = response['item_get_response']['item']
                        item_dict['skus'] = json.dumps(item_dict.get('skus',{}))
                        Item.save_item_through_dict(user_id,item_dict)
                    onsale_item_ids.append(item['num_iid'])
                
            total_nums = item_list['total_results']
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums<total_nums
            cur_page += 1
    except:
        logger.error('update user inventory items task error',exc_info=True)
   
    Item.objects.filter(user__visitor_id=user_id).exclude(num_iid__in=onsale_item_ids).update(approve_status=INSTOCK_STATUS)
   
    return len(onsale_item_ids)




@task()
def updateAllUserItemsTask():
    users = User.objects.all()

    for user in users:
        subtask(updateUserItemsTask).delay(user.visitor_id)




@task()
def updateUserProductSkuTask(user_id):

    user  = User.objects.get(visitor_id=user_id)
    items = user.items.all()

    num_iids = []
    for index,item in enumerate(items):
        num_iids.append(item.num_iid)

        if len(num_iids)>=40 or index+1 ==len(items):
            sku_dict = {}
            try:
                num_iids_str = ','.join(num_iids)
                response = apis.taobao_item_skus_get(num_iids=num_iids_str,tb_user_id=user_id)
                if response['item_skus_get_response'].has_key('skus'):
                    skus     = response['item_skus_get_response']['skus']
    
                    for sku in skus.get('sku'):
                        
                        if sku_dict.has_key(sku['num_iid']):
                            sku_dict[sku['num_iid']].append(sku)
                        else:
                            sku_dict[sku['num_iid']] = [sku]
                            
                        sku_outer_id = sku.get('outer_id',None)
                        item  = Item.objects.get(num_iid=sku['num_iid'])
                        
                        psku,state = ProductSku.objects.get_or_create(outer_id=sku_outer_id,product=item.product)
                        if state:
                            for key,value in sku.iteritems():
                                hasattr(psku,key) and setattr(psku,key,value)
                            psku.properties_name = psku.properties_values
                            psku.prod_outer_id   = item.outer_id
                            psku.save()
            except Exception,exc:
                logger.error('update product sku error!',exc_info=True)
            finally:
                for num_iid,sku_list in sku_dict.items():
                    item = Item.objects.get(num_iid=num_iid)
                    item.skus = json.dumps({'sku':sku_list})
                    item.save()
                num_iids = []
                


@task()
def updateAllUserProductSkuTask():

    users = User.objects.all()
    for user in users:

        subtask(updateUserProductSkuTask).delay(user.visitor_id)



@task()
def updateUserItemsEntityTask(user_id):

    updateUserItemsTask(user_id)

    subtask(updateUserProductSkuTask).delay(user_id)


@task()
def updateAllUserItemsEntityTask():

    users = User.objects.all()
    for user in users:

        subtask(updateUserItemsEntityTask).delay(user.visitor_id)

@task()
def updateUserItemSkuFenxiaoProductTask(user_id):
    updateUserItemsTask(user_id)
    updateUserProductSkuTask(user_id)
    saveUserFenxiaoProductTask(user_id)

  