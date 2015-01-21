#-*- coding:utf-8 -*-
import datetime
import time
import json
from celery import Task
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Sum
from django.db   import transaction
from django.db.models.query import QuerySet

from shopback    import paramconfig as pcfg
from shopback.items.models import Item,Product,ProductSku,SkuProperty,\
    ItemNumTaskLog,ProductDaySale
from shopback.fenxiao.models import FenxiaoProduct
from shopback.orders.models import Order, Trade
from shopback.trades.models import MergeOrder, MergeTrade
from shopback.users import Seller
from shopback.fenxiao.tasks import saveUserFenxiaoProductTask
from shopback import paramconfig as pcfg
from auth     import apis
from common.utils import format_datetime,parse_datetime,get_yesterday_interval_time
import logging

logger = logging.getLogger('django.request')


PURCHASE_STOCK_PERCENT = 0.5

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
            
        #更新库存中的商品
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
    else:
        Item.objects.filter(user__visitor_id=user_id).exclude(num_iid__in=onsale_item_ids)\
            .update(approve_status=pcfg.INSTOCK_STATUS,status=False)
    
    return len(onsale_item_ids)



@task()
def updateAllUserItemsTask():
    """ 更新所有用户商品信息任务 """
    
    users = Seller.effect_users.all()
    for user in users:
        subtask(updateUserItemsTask).delay(user.visitor_id)


@task()
def updateUserProductSkuTask(user_id=None,outer_ids=None,force_update_num=False):
    """ 更新用户商品SKU规格信息任务 """
    
    user = Seller.getSellerByVisitorId(user_id)
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
                        sku_outer_id = sku.get('outer_id', '').strip() 
                        
                        if (not item.user.is_primary or not item.product 
                            or item.approve_status != pcfg.ONSALE_STATUS or
                            not sku_outer_id or sku['status'] != pcfg.NORMAL):
                            continue
                        sku_prop_dict = dict([('%s:%s' % (p.split(':')[0], p.split(':')[1]), 
                                               p.split(':')[3]) 
                                              for p in sku['properties_name'].split(';') if p])
                        
                        pskus = ProductSku.objects.filter(outer_id=sku_outer_id, 
                                                                       product=item.product)
                        if pskus.count() <= 0:
                            continue
                         
                        psku  = pskus[0]
                        psku.properties_name = psku.properties_name or sku['properties_name']
                        if force_update_num:
                            wait_post_num = psku.wait_post_num >= 0 and psku.wait_post_num or 0
                            psku.quantity = sku['quantity'] + wait_post_num
                                
                        #psku.std_sale_price =  float(sku['price'])
                        properties = ''
                        props = sku['properties'].split(';')
                        for prop in props:
                            if prop :
                                properties += (prop_dict[sku['num_iid']].get(prop, '') 
                                               or sku_prop_dict.get(prop,'')) 
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
                    
                    sku_ids = [sku['sku_id'] for sku in sku_list if sku]
                    if sku_ids:
                        SkuProperty.objects.filter(num_iid=num_iid)\
                            .exclude(sku_id__in=sku_ids).update(status=pcfg.DELETE)
                    
                num_iids = []
                prop_dict = {}
    

@task()
def updateProductWaitPostNumTask():
    """ 更新商品待发数任务 """
    products = Product.objects.filter(status=pcfg.NORMAL)
    for product in products:
        
        Product.objects.updateProductWaitPostNum(product)



class CalcProductSaleTask(Task):
    """ 更新商品销售数量任务 """
    
    def getYesterdayDate(self):
        dt = datetime.datetime.now() - datetime.timedelta(days=1)
        return dt.date()
    
    def getYesterdayStarttime(self,day_date):
        return datetime.datetime(day_date.year,day_date.month,day_date.day,0,0,0)
    
    def getYesterdayEndtime(self,day_date):
        return datetime.datetime(day_date.year,day_date.month,day_date.day,23,59,59)
    
    def getSourceList(self):
        return Product.objects.filter(status=pcfg.NORMAL)
        
    def getValidUser(self):
        return Seller.effect_users.all()
    
    def calcSaleByUserAndProduct(self,queryset,user,product,sku,yest_date):
        
        sale_dict = queryset.filter(merge_trade__user=user,
                                    outer_id=product.outer_id,
                                    outer_sku_id=sku and sku.outer_id or '')\
                    .aggregate(sale_num=Sum('num'),
                               sale_payment=Sum('payment'))
        if sale_dict['sale_num'] :
            pds,state = ProductDaySale.objects.get_or_create(
                                             day_date=yest_date,
                                             user_id=user.id,
                                             product_id=product.id,
                                             sku_id=sku and sku.id)
                                             
            pds.sale_num = sale_dict['sale_num'] or 0
            pds.sale_payment=sale_dict['sale_payment'] or 0
            pds.save()
        return sale_dict['sale_num'] or 0,sale_dict['sale_payment'] or 0
        
    def run(self,yest_date=None,*args,**kwargs):
        
        products = self.getSourceList()
        
        yest_date  = yest_date or self.getYesterdayDate()
        yest_start = self.getYesterdayStarttime(yest_date)
        yest_end   = self.getYesterdayEndtime(yest_date)
        
        sellers = self.getValidUser()
        
        queryset = MergeOrder.objects.filter(merge_trade__pay_time__gte=yest_start,
                                             merge_trade__pay_time__lte=yest_end,
                                             is_merge=False,
                                             gift_type__in=(pcfg.OVER_PAYMENT_GIT_TYPE,
                                                            pcfg.REAL_ORDER_GIT_TYPE,
                                                            pcfg.COMBOSE_SPLIT_GIT_TYPE),
                                             sys_status=pcfg.IN_EFFECT)\
                                             .exclude(merge_trade__sys_status='')
        for prod in products:
            
            for sku in prod.prod_skus.all():
                
                total_sale   = 0
                for user in sellers:
                    pds = self.calcSaleByUserAndProduct(queryset,user,prod,sku,yest_date)
                    total_sale   += pds[0]
                
                sku.warn_num = total_sale
                sku.save()
                
            if prod.prod_skus.count() == 0:
                
                total_sale   = 0
                for user in sellers:
                    pds = self.calcSaleByUserAndProduct(queryset,user,prod,None,yest_date)
                    total_sale   += pds[0]
                    
                prod.warn_num = total_sale
                prod.save()
                

@task()
def updateAllUserProductSkuTask():
    """ 更新所有用户SKU信息任务 """
    users = Seller.effect_users.filter(is_primary=True)
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
    users = Seller.effect_users.all()
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
    p_outer_id = product.outer_id
    skus = json.loads(item.skus) if item.skus else None
    if skus:
        for sku in skus.get('sku',[]):
            try:
                outer_sku_id = sku.get('outer_id','')
                outer_id,outer_sku_id = Product.objects.trancecode(p_outer_id,outer_sku_id)
                
                if sku['status'] != pcfg.NORMAL or not outer_sku_id:
                    continue
                product_sku  = product.prod_skus.get(outer_id=outer_sku_id)
                
                order_nums  = 0
                wait_nums   = max(product_sku.wait_post_num , 0)
                remain_nums = product_sku.remain_num or 0
                real_num    = product_sku.quantity
                sync_num    = real_num - wait_nums - remain_nums
                
                #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
                if sync_num>0 and user_percent>0:
                    sync_num = int(user_percent * sync_num)
                elif sync_num >0 and sync_num <= product_sku.warn_num:
                    total_num,user_order_num = MergeOrder.get_yesterday_orders_totalnum(item.user.id,
                                                                                        outer_id,
                                                                                        outer_sku_id)
                    if total_num>0 and user_order_num>0:
                        sync_num = int(float(user_order_num)/float(total_num)*sync_num)
                    elif total_num == 0:
                        item_count = Item.objects.filter(outer_id=outer_id,
                                                         approve_status=pcfg.ONSALE_STATUS).count() or 1
                        sync_num = int(sync_num/item_count) or sync_num
                    else:
                        sync_num = (real_num - wait_nums)>10 and 2 or 0 
                elif sync_num > 0:
                    product_sku.is_assign = False
                else:
                    sync_num = 0
                #当前同步库存值，与线上拍下未付款商品数，哪个大取哪个 
                sync_num = max(sync_num,sku.get('with_hold_quantity',0))   
#                #针对小小派，测试线上库存低量促销效果
#                if product.outer_id == '3116BG7':
#                    sync_num = product_sku.warn_num > 0 and min(sync_num,product_sku.warn_num+10) or min(sync_num,15)
                    
                #同步库存数不为0，或者没有库存警告，同步数量不等于线上库存，并且店铺，商品，规格同步状态正确
                if (not (sync_num == 0 and product_sku.is_assign) 
                    and sync_num != sku['quantity'] 
                    and user.sync_stock 
                    and product.sync_stock 
                    and product_sku.sync_stock):
                    response = apis.taobao_item_quantity_update(num_iid=item.num_iid,
                                                                quantity=sync_num,
                                                                outer_id=outer_sku_id,
                                                                tb_user_id=user_id)
                    item_dict = response['item_quantity_update_response']['item']
                    Item.objects.filter(num_iid=item_dict['num_iid']).update(modified=item_dict['modified'],
                                                                             num=sync_num)
    
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
        outer_id,outer_sku_id = Product.objects.trancecode(p_outer_id,'')
        
        wait_nums  = max( product.wait_post_num , 0)
        remain_nums = product.remain_num or 0
        real_num   = product.collect_num
        sync_num   = real_num - wait_nums - remain_nums

        #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if sync_num>0 and user_percent>0:
            sync_num = int(user_percent*sync_num)
        elif sync_num >0 and sync_num <= product.warn_num:
            total_num,user_order_num = MergeOrder.get_yesterday_orders_totalnum(
                                            item.user.id,
                                            outer_id,
                                            outer_sku_id)
            if total_num>0 and user_order_num>0:
                sync_num = int(float(user_order_num)/float(total_num)*sync_num)
            elif total_num == 0:
                item_count = Item.objects.filter(outer_id=outer_id,
                                approve_status=pcfg.ONSALE_STATUS).count() or 1
                sync_num = int(sync_num/item_count) or sync_num
            else:
                sync_num = (real_num - wait_nums)>10 and 2 or 0
        elif sync_num > 0:
            product.is_assign = False
        else:
            sync_num = 0    
            
        #当前同步库存值，与线上拍下未付款商品数，哪个大取哪个 
        sync_num = max(sync_num,item.with_hold_quantity)
        #同步库存数不为0，或者没有库存警告，同步数量不等于线上库存，并且店铺，商品同步状态正确
        if (not (sync_num == 0 and product.is_assign) 
            and sync_num != item.num 
            and user.sync_stock 
            and product.sync_stock): 
            response = apis.taobao_item_update(num_iid=item.num_iid,
                                               num=sync_num,
                                               tb_user_id=user_id)
            
            item_dict = response['item_update_response']['item']
            Item.objects.filter(num_iid=item_dict['num_iid']).update(
                                        modified=item_dict['modified'],
                                        num=sync_num)

            product.save()
            
            ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                             outer_id=product.outer_id,
                                             num=sync_num,
                                             start_at= item.last_num_updated,
                                             end_at=datetime.datetime.now())
  
    Item.objects.filter(num_iid=item.num_iid).update(last_num_updated=datetime.datetime.now())


def getPurchaseSkuNum(product,product_sku):
    
    wait_nums   = product_sku.wait_post_num>0 and product_sku.wait_post_num or 0
    remain_nums = product_sku.remain_num or 0
    real_num    = product_sku.quantity
    sync_num    = real_num - wait_nums - remain_nums
    
    if sync_num >0 and sync_num <= product_sku.warn_num:
        sync_num = int(sync_num * PURCHASE_STOCK_PERCENT / 2)
        
    elif sync_num > 0:
        sync_num = PURCHASE_STOCK_PERCENT * sync_num
        
    else:
        sync_num = 0
        
    return int(sync_num)


@transaction.commit_on_success
def updatePurchaseItemNum(user_id,pid):
    """
    {"fenxiao_sku": [{"outer_id": "10410", 
                      "name": "**", 
                      "quota_quantity": 0, 
                      "standard_price": "39.90", 
                      "reserved_quantity": 0, 
                      "dealer_cost_price": "78.32", 
                      "id": 2259034511371, 
                      "cost_price": "35.11", 
                      "properties": "**", 
                      "quantity": 110}]}
    """
    item    = FenxiaoProduct.objects.get(pid=pid)
    user    = item.user
    
    try:
        product = Product.objects.get(outer_id=item.outer_id)
    except Product.DoesNotExist:
        product = None
        
    if not product or not product.sync_stock:
        return
    
    outer_id     = product.outer_id
    skus         = json.loads(item.skus) if item.skus else None
    if skus:
        
        sku_tuple       = []
        for sku in skus.get('fenxiao_sku',[]):
            outer_sku_id = sku.get('outer_id','')
            try:
                product_sku = product.prod_skus.get(outer_id=outer_sku_id)
            except:
                continue
            
            sync_num = getPurchaseSkuNum(product,product_sku)   
            sku_tuple.append(('%d'%sku['id'],'%d'%sync_num,outer_sku_id))
        
        #同步库存数不为0，或者没有库存警告，同步数量不等于线上库存，并且店铺，商品，规格同步状态正确
        if ( sku_tuple and user.sync_stock and product.sync_stock):
            response = apis.taobao_fenxiao_product_update(pid=pid,
                                                          sku_ids=','.join([s[0] for s in sku_tuple]),
                                                          sku_quantitys=','.join([s[1] for s in sku_tuple]),
                                                          tb_user_id=user_id)
            
            item_dict = response['fenxiao_product_update_response']
            FenxiaoProduct.objects.filter(pid=item_dict['pid']
                                          ).update(modified=item_dict['modified'])
            
            for index,sku in enumerate(sku_tuple):
                ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                         outer_id=outer_id,
                                         sku_outer_id= 'fx%s'%sku[2],
                                         num=sku[1],
                                         start_at=item_dict['modified'],
                                         end_at=item_dict['modified'])
                
    else:
        order_nums    = 0
        wait_nums  = product.wait_post_num >0 and product.wait_post_num or 0
        remain_nums = product.remain_num or 0
        real_num   = product.collect_num
        sync_num   = real_num - wait_nums - remain_nums

        #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if sync_num >0 and sync_num <= product.warn_num:
            sync_num = int(sync_num * PURCHASE_STOCK_PERCENT / 2)
        elif sync_num > 0:
            sync_num = PURCHASE_STOCK_PERCENT * sync_num
        else:
            sync_num = 0    
        sync_num  =  int(sync_num)
        
        if (not (sync_num == 0 and product.is_assign) 
            and user.sync_stock and product.sync_stock):
             
            response = apis.taobao_fenxiao_product_update(pid=pid,
                                                          quantity=sync_num,
                                                          tb_user_id=user_id)
            item_dict = response['fenxiao_product_update_response']
            FenxiaoProduct.objects.filter(pid=item_dict['pid']).update(
                                        modified=item_dict['modified'])
            
            ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                             outer_id='',
                                             num=sync_num,
                                             start_at=item_dict['modified'],
                                             end_at=item_dict['modified'])


@task()
def updateUserItemNumTask(user_id):
    
    updateUserItemsTask(user_id)
    updateUserProductSkuTask(user_id)
        
    items = Item.objects.filter(user__visitor_id=user_id,approve_status=pcfg.ONSALE_STATUS)
    for item in items:
        try:
            updateItemNum(user_id,item.num_iid)
        except Exception,exc :
            logger.error(u'更新淘宝库存异常:%s'%exc,exc_info=True)


@task()
def updateUserPurchaseItemNumTask(user_id):
    
    saveUserFenxiaoProductTask(user_id)
    
    purchase_items = FenxiaoProduct.objects.filter(user__visitor_id=user_id,
                                         status=pcfg.UP_STATUS)
    for item in purchase_items:
        try:
            updatePurchaseItemNum(user_id,item.pid)
        except Exception,exc :
            logger.error(u'更新分销库存异常:%s'%exc.message,exc_info=True)
        

@task()
def updateAllUserItemNumTask():
    
    updateProductWaitPostNumTask()

    for user in Seller.effect_users.TAOBAO:
        updateUserItemNumTask(user.visitor_id)  
        
        
@task()
def updateAllUserPurchaseItemNumTask():
    
    updateProductWaitPostNumTask()

    users = Seller.effect_users.TAOBAO.filter(has_fenxiao=True)
    
    for user in users:
        updateUserPurchaseItemNumTask(user.visitor_id)  
