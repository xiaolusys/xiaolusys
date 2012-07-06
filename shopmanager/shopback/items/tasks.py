import datetime
import time
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.base.aggregates import ConcatenateDistinct
from auth.utils import format_datetime ,parse_datetime ,refresh_session
from shopback.items.models import Item,ProductSku
from shopback.orders.models import Order,Trade,ORDER_SUCCESS_STATUS,ORDER_UNPAY_STATUS
from shopback.users.models import User
from shopapp.syncnum.models import ItemNumTask
from shopback.base.models   import UNEXECUTE,EXECERROR,SUCCESS
from auth.apis.exceptions import RemoteConnectionException,AppCallLimitedException,UserFenxiaoUnuseException,\
    APIConnectionTimeOutException,ServiceRejectionException,TaobaoRequestException
from auth import apis
import logging

logger = logging.getLogger('items.handler')



@task()
def updateUserItemsTask(user_id):

    has_next = True
    cur_page = 1
    update_nums = 0

    while has_next:
      
        response_list = apis.taobao_items_onsale_get(page_no=cur_page,tb_user_id=user_id
            ,page_size=settings.TAOBAO_PAGE_SIZE,fields='num_iid,cid,outer_id,num,price,title,delist_time,list_time')

        item_list = response_list['items_onsale_get_response']
        if item_list['total_results']>0:
            items = item_list['items']['item']
            for item in items:
                Item.save_item_through_dict(user_id,item)
            update_nums += len(items)    

        total_nums = item_list['total_results']
        cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
        has_next = cur_nums<total_nums
        
        cur_page += 1
    
    has_next = True
    cur_page = 1    
    while has_next:
      
        response_list = apis.taobao_items_inventory_get(page_no=cur_page,tb_user_id=user_id
            ,page_size=settings.TAOBAO_PAGE_SIZE,fields='num_iid,cid,outer_id,num,price,title,delist_time,list_time')

        item_list = response_list['items_inventory_get_response']
        if item_list['total_results']>0:
            items = item_list['items']['item']
            for item in item_list['items']['item']:
                Item.save_item_through_dict(user_id,item)
            update_nums += len(items)
            
        total_nums = item_list['total_results']
        cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
        has_next = cur_nums<total_nums
        cur_page += 1
   
   
    return update_nums




@task()
def updateAllUserItemsTask():
    users = User.objects.all()

    for user in users:
        subtask(updateUserItemsTask).delay(user.visitor_id)




@task(max_retries=3)
def saveUserItemsInfoTask(user_id):

    user  = User.objects.get(visitor_id=user_id)
    items = user.items.all()
    for item in items:

        response = apis.taobao_item_get(num_iid=item.num_iid,tb_user_id=user_id)
        item_dict = response['item_get_response']['item']
        item_dict['skus'] = json.dumps(item_dict.get('skus',{}))
        

        Item.save_item_through_dict(user_id,item_dict)




@task()
def updateAllUserItemsInfoTask():

    users = User.objects.all()
    for user in users:

        subtask(saveUserItemsInfoTask).delay(user.visitor_id)



@task()
def updateUserProductSkuTask(user_id):

    user  = User.objects.get(visitor_id=user_id)
    items = user.items.all()

    num_iids = []
    for index,item in enumerate(items):
        num_iids.append(item.num_iid)

        if len(num_iids)>=40 or index+1 ==len(items):
            try:
                num_iids_str = ','.join(num_iids)
                response = apis.taobao_item_skus_get(num_iids=num_iids_str,tb_user_id=user_id)
                skus     = response['item_skus_get_response']['skus']['sku']

                for sku in skus:
                    sku_outer_id = sku.get('outer_id',None)
                    item  = Item.objects.get(num_iid=sku['num_iid'])
                    psku,state = ProductSku.objects.get_or_create(outer_id=sku_outer_id,product=item.product)
                    if state:
                        for key,value in sku.iteritems():
                            hasattr(psku,key) and setattr(psku,key,value)
                        psku.save()
                num_iids = []
            except Exception,exc:
                logger.error('update product sku error!',exc_info=True)




@task()
def updateAllUserProductSkuTask():

    users = User.objects.all()
    for user in users:

        subtask(updateUserProductSkuTask).delay(user.visitor_id)



@task()
def updateUserItemsEntityTask(user_id):

    updateUserItemsTask(user_id)

    subtask(saveUserItemsInfoTask).delay(user_id)

    subtask(updateUserProductSkuTask).delay(user_id)


@task()
def updateAllUserItemsEntityTask():

    users = User.objects.all()
    for user in users:

        subtask(updateUserItemsEntityTask).delay(user.visitor_id)



  