#-*- coding:utf-8 -*-
import datetime
import time
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from auth.utils import format_datetime,parse_datetime
from shopback import paramconfig as pcfg
from shopback.items.models import Item,Product, ProductSku
from shopback.orders.models import Order, Trade
from shopback.users.models import User
from shopback.fenxiao.tasks import saveUserFenxiaoProductTask
from shopback import paramconfig as pcfg
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
            response_list = apis.taobao_items_onsale_get(page_no=cur_page, tb_user_id=user_id
                , page_size=settings.TAOBAO_PAGE_SIZE, fields='num_iid,modified')
            item_list = response_list['items_onsale_get_response']
            if item_list['total_results'] > 0:
                items = item_list['items']['item']
                for item in items:
                    modified = parse_datetime(item['modified']) if item.get('modified', None) else None
                    item_obj, state = Item.objects.get_or_create(num_iid=item['num_iid'])
                    if modified != item_obj.modified:
                        response = apis.taobao_item_get(num_iid=item['num_iid'], tb_user_id=user_id)
                        item_dict = response['item_get_response']['item']
                        item_dict['skus'] = json.dumps(item_dict.get('skus', {}))
                        Item.save_item_through_dict(user_id, item_dict)
                    onsale_item_ids.append(item['num_iid'])
                    
            total_nums = item_list['total_results']
            cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums < total_nums
            cur_page += 1
            
    except:
        logger.error('update user onsale items task error', exc_info=True)
    #更新库存中的商品
    try:
        has_next = True
        cur_page = 1    
        while has_next:
                
            response_list = apis.taobao_items_inventory_get(page_no=cur_page, tb_user_id=user_id
                , page_size=settings.TAOBAO_PAGE_SIZE, fields='num_iid,modified')
    
            item_list = response_list['items_inventory_get_response']
            if item_list['total_results'] > 0:
                items = item_list['items']['item']
                for item in item_list['items']['item']:
                    modified = parse_datetime(item['modified']) if item.get('modified', None) else None
                    item_obj, state = Item.objects.get_or_create(num_iid=item['num_iid'])
                    if modified != item_obj.modified:
                        response = apis.taobao_item_get(num_iid=item['num_iid'], tb_user_id=user_id)
                        item_dict = response['item_get_response']['item']
                        item_dict['skus'] = json.dumps(item_dict.get('skus', {}))
                        Item.save_item_through_dict(user_id, item_dict)
                    onsale_item_ids.append(item['num_iid'])
                
            total_nums = item_list['total_results']
            cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums < total_nums
            cur_page += 1
    except:
        logger.error('update user inventory items task error', exc_info=True)
   
    Item.objects.filter(user__visitor_id=user_id).exclude(num_iid__in=onsale_item_ids)\
        .update(approve_status=pcfg.INSTOCK_STATUS)
    
    return len(onsale_item_ids)




@task()
def updateAllUserItemsTask():
    users = User.objects.all()

    for user in users:
        subtask(updateUserItemsTask).delay(user.visitor_id)




@task()
def updateUserProductSkuTask(user_id,force_update_num=False):

    user = User.objects.get(visitor_id=user_id)
    items = user.items.filter(status=pcfg.NORMAL)
	
    num_iids = []
    prop_dict = {}
    for index, item in enumerate(items):
        num_iids.append(item.num_iid)
        prop_dict[int(item.num_iid)] = item.property_alias_dict
        if len(num_iids) >= 40 or index + 1 == len(items):
            sku_dict = {}
            try:
                num_iids_str = ','.join(num_iids)
                response = apis.taobao_item_skus_get(num_iids=num_iids_str, tb_user_id=user_id)
                if response['item_skus_get_response'].has_key('skus'):
                    skus = response['item_skus_get_response']['skus']
    
                    for sku in skus.get('sku'):
                        
                        if sku_dict.has_key(sku['num_iid']):
                            sku_dict[sku['num_iid']].append(sku)
                        else:
                            sku_dict[sku['num_iid']] = [sku]
                            
                        sku_outer_id = sku.get('outer_id', None)
                        item = Item.objects.get(num_iid=sku['num_iid'])
                        
                        sku_prop_dict = dict([ ('%s:%s' % (p.split(':')[0], p.split(':')[1]), p.split(':')[3]) for p in sku['properties_name'].split(';') if p])
                        if not item.product:
                            continue
                        psku, state = ProductSku.objects.get_or_create(outer_id=sku_outer_id, product=item.product)
                        if state:
                            for key, value in sku.iteritems():
                                hasattr(psku, key) and setattr(psku, key, value)
                            psku.prod_outer_id = item.outer_id
                        else:
                            psku.properties_name = sku['properties_name']
                            psku.properties = sku['properties']
                            psku.prod_outer_id = item.outer_id
                            if force_update_num:
                                psku.quantity = sku['quantity']

                        properties = ''
                        props = sku['properties'].split(';')
                        for prop in props:
                            if prop :
                                properties += prop_dict[sku['num_iid']].get(prop, '') or sku_prop_dict.get(prop, u'规格有误') 
                                psku.properties_name = properties or psku.properties_values
                        psku.save()
			                
            except Exception, exc:
                logger.error('update product sku error!', exc_info=True)
            finally:
                for num_iid, sku_list in sku_dict.items():
                    item = Item.objects.get(num_iid=num_iid)
                    item.skus = json.dumps({'sku':sku_list})
                    item.save()
                num_iids = []
                prop_dict = {}
    


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

  
