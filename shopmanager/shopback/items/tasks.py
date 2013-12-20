#-*- coding:utf-8 -*-
import datetime
import time
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Sum
from django.db import transaction
from django.db.models.query import QuerySet
from shopback import paramconfig as pcfg
from shopback.items.models import Item,Product,ProductSku,SkuProperty,ItemNumTaskLog
from shopback.orders.models import Order, Trade
from shopback.trades.models import MergeOrder, MergeTrade
from shopback.users.models import User
from shopback.fenxiao.tasks import saveUserFenxiaoProductTask
from shopback import paramconfig as pcfg
from auth import apis
from common.utils import format_datetime,parse_datetime,get_yesterday_interval_time
import logging

logger = logging.getLogger('items.handler')



@task()
def updateUserItemsTask(user_id):
    """ 更新淘宝线上商品信息入库 """
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
    """ 更新所有用户商品信息任务 """
    users = User.objects.all()

    for user in users:
        subtask(updateUserItemsTask).delay(user.visitor_id)



@task()
def updateUserProductSkuTask(user_id=None,outer_ids=None,force_update_num=False):
    """ 更新用户商品SKU规格信息任务 """
    
    user = User.objects.get(visitor_id=user_id)
    items = user.items.filter(status=pcfg.NORMAL)
    if outer_ids:
        items = items.filter(outer_id__in=outer_ids)
    
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
                            
                        item = Item.objects.get(num_iid=sku['num_iid'])
                        
                        sku_property = SkuProperty.save_or_update(sku.copy())
                        sku_outer_id = sku.get('outer_id', None) or sku_property.outer_id
                        
                        if not item.user.is_primary or not item.product or not sku_outer_id:
                            continue
                        sku_prop_dict = dict([('%s:%s' % (p.split(':')[0], p.split(':')[1]), p.split(':')[3]) for p in sku['properties_name'].split(';') if p])
                        
                        psku, state = ProductSku.objects.get_or_create(outer_id=sku_outer_id, product=item.product)
                        if state:
                            for key, value in sku.iteritems():
                                hasattr(psku, key) and setattr(psku, key, value)
                        else:
                            psku.properties_name = psku.properties_name or sku['properties_name']
                            if force_update_num:
                                wait_post_num = psku.wait_post_num >= 0 and psku.wait_post_num or 0
                                psku.quantity = sku['quantity'] + wait_post_num
                                
                        psku.std_sale_price =  float(sku['price'])
                        properties = ''
                        props = sku['properties'].split(';')
                        for prop in props:
                            if prop :
                                properties += prop_dict[sku['num_iid']].get(prop, '') or sku_prop_dict.get(prop,'') 
                                psku.properties_name = properties
                        psku.status = pcfg.NORMAL
                        psku.save()
			                
            except Exception, exc:
                logger.error('update product sku error!', exc_info=True)
            finally:
                for num_iid, sku_list in sku_dict.items():
                    item = Item.objects.get(num_iid=num_iid)
                    item.skus = sku_list and json.dumps({'sku':sku_list}) or item.skus
                    item.save()
                num_iids = []
                prop_dict = {}
    

@task()
def updateProductWaitPostNumTask():
    """ 更新商品待发数任务 """
    products = Product.objects.filter(status=pcfg.NORMAL)
    for prod in products:
        
        outer_id  = prod.outer_id 
        prod_skus = prod.pskus
        if prod_skus.count()>0:
            for sku in prod_skus:
                outer_sku_id = sku.outer_id
                wait_post_num = MergeTrade.get_trades_wait_post_prod_num(outer_id,outer_sku_id)
                sku.wait_post_num = wait_post_num
                sku.save()

        else:
            outer_sku_id = ''
            wait_post_num = MergeTrade.get_trades_wait_post_prod_num(outer_id,outer_sku_id)
            prod.wait_post_num = wait_post_num
            prod.save()


@task()
def updateProductWarnNumTask():
    """ 更新商品警告数任务 """
    st_f,st_t = get_yesterday_interval_time()
    products = Product.objects.filter(status=pcfg.NORMAL)
    for prod in products:
        
        outer_id  = prod.outer_id 
        prod_skus = prod.pskus
        if prod_skus.count()>0:
            for sku in prod_skus:
                outer_sku_id = sku.outer_id
                lastday_pay_num = MergeOrder.objects.filter(outer_id=outer_id,outer_sku_id=outer_sku_id
                    ,merge_trade__pay_time__gte=st_f,merge_trade__pay_time__lte=st_t,sys_status=pcfg.IN_EFFECT)\
                    .aggregate(sale_nums=Sum('num')).get('sale_nums')
                sku.warn_num = lastday_pay_num or 0
                sku.save()
        else:
            outer_sku_id = ''
            lastday_pay_num = MergeOrder.objects.filter(outer_id=outer_id,outer_sku_id=outer_sku_id
                ,merge_trade__pay_time__gte=st_f,merge_trade__pay_time__lte=st_t,sys_status=pcfg.IN_EFFECT)\
                .aggregate(sale_nums=Sum('num')).get('sale_nums')
            sku.warn_num = lastday_pay_num or 0
            sku.save()

@task()
def updateAllUserProductSkuTask():
    """ 更新所有用户SKU信息任务 """
    users = User.objects.filter(is_primary=True)
    for user in users:

        subtask(updateUserProductSkuTask).delay(user.visitor_id)


@task()
def updateUserItemsEntityTask(user_id):
    """ 更新用户商品及SKU信息任务 """
    updateUserItemsTask(user_id)

    subtask(updateUserProductSkuTask).delay(user_id)


@task()
def updateAllUserItemsEntityTask():
    """ 更新所有用户商品及SKU信息任务 """
    users = User.objects.all()
    for user in users:

        subtask(updateUserItemsEntityTask).delay(user.visitor_id)

@task()
def updateUserItemSkuFenxiaoProductTask(user_id):
    """ 更新用户商品信息，SKU信息及分销商品信息任务 """
    updateUserItemsTask(user_id)
    updateUserProductSkuTask(user_id)
    saveUserFenxiaoProductTask(user_id)

###########################################################  商品库存管理  ########################################################

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
    user = item.user
    product = item.product
    if not product or not item.sync_stock:
        return
    
    user_percent = user.stock_percent
    outer_id = product.outer_id
    skus = json.loads(item.skus) if item.skus else None
    if skus:
        for sku in skus.get('sku',[]):
            try:
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
                if sync_num>0 and user_percent>0:
                    sync_num = round(user_percet*sync_num)
                elif sync_num > product_sku.remain_num:
                    product_sku.is_assign = False
                elif sync_num >0 and sync_num <= product_sku.warn_num:
                    total_num,user_order_num = MergeOrder.get_yesterday_orders_totalnum(item.user.id,outer_id,outer_sku_id)
                    if total_num>0 and user_order_num>0:
                        sync_num = round(float(user_order_num)/float(total_num)*sync_num)
                    elif total_num == 0:
                        item_count = Item.objects.filter(outer_id=outer_id,approve_status=pcfg.ONSALE_STATUS).count() or 1
                        sync_num = sync_num/item_count or sync_num
                    else:
                        sync_num = (real_num - wait_nums)>10 and 2 or 0 
                else:
                    sync_num = 0
                #当前同步库存值，与线上拍下未付款商品数，哪个大取哪个 
                sync_num = max(sync_num,sku.get('with_hold_quantity',0))   
#                #针对小小派，测试线上库存低量促销效果
#                if product.outer_id == '3116BG7':
#                    sync_num = product_sku.warn_num > 0 and min(sync_num,product_sku.warn_num+10) or min(sync_num,15)
                    
                #同步库存数不为0，或者没有库存警告，同步数量不等于线上库存，并且店铺，商品，规格同步状态正确
                if not (sync_num == 0 and product_sku.is_assign) and sync_num != sku['quantity'] \
                    and user.sync_stock and product.sync_stock and product_sku.sync_stock:
                    sync_num = int(sync_num)
                    response = apis.taobao_item_quantity_update\
                            (num_iid=item.num_iid,quantity=sync_num,outer_id=outer_sku_id,tb_user_id=user_id)
                    item_dict = response['item_quantity_update_response']['item']
                    Item.objects.filter(num_iid=item_dict['num_iid']).update(modified=item_dict['modified'],num=sync_num)
    
                    product_sku.save()
                    ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                                 outer_id=product.outer_id,
                                                 sku_outer_id= outer_sku_id,
                                                 num=sync_num,
                                                 start_at= item.last_num_updated,
                                                 end_at=datetime.datetime.now())
            except Exception,exc:
                logger.error('sync sku num error!', exc_info=True)
                
    else:
        order_nums    = 0
        outer_sku_id  = ''
        wait_nums  = product.wait_post_num >0 and product.wait_post_num or 0
        remain_nums = product.remain_num or 0
        real_num   = product.collect_num
        sync_num   = real_num - wait_nums - remain_nums

        #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if sync_num>0 and user_percent>0:
            sync_num = round(user_percet*sync_num)
        elif sync_num > product.remain_num:
            product.is_assign = False
        elif sync_num >0 and sync_num <= product.warn_num:
            total_num,user_order_num = MergeOrder.get_yesterday_orders_totalnum(item.user.id,outer_id,outer_sku_id)
            if total_num>0 and user_order_num>0:
                sync_num = round(float(user_order_num)/float(total_num)*sync_num)
            elif total_num == 0:
                item_count = Item.objects.filter(outer_id=outer_id,approve_status=pcfg.ONSALE_STATUS).count() or 1
                sync_num = sync_num/item_count or sync_num
            else:
                sync_num = (real_num - wait_nums)>10 and 2 or 0
        else:
            sync_num = 0    
            
        #当前同步库存值，与线上拍下未付款商品数，哪个大取哪个 
        sync_num = max(sync_num,item.with_hold_quantity)
        #同步库存数不为0，或者没有库存警告，同步数量不等于线上库存，并且店铺，商品同步状态正确
        if not (sync_num == 0 and product.is_assign) and sync_num != item.num and user.sync_stock and product.sync_stock: 
            sync_num = int(sync_num)   
            response = apis.taobao_item_update(num_iid=item.num_iid,num=sync_num,tb_user_id=user_id)
            item_dict = response['item_update_response']['item']
            Item.objects.filter(num_iid=item_dict['num_iid']).update(modified=item_dict['modified'],num=sync_num)

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
