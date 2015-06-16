#-*- coding:utf8 -*-
import time
import datetime
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings

from common.utils import update_model_fields, replace_utf8mb4
from .models import WeiXinUser,WXOrder,WXProduct,WXProductSku,WXLogistic,WeixinUnionID
from .service import WxShopService
from .weixin_apis import WeiXinAPI,WeiXinRequestException

@task(max_retry=3,default_retry_delay=60)
def task_Update_Weixin_Userinfo(openId,unionId=None):
    
    try:  
        _wx_api = WeiXinAPI()
        userinfo =  _wx_api.getUserInfo(openId)
        
        wx_user,state = WeiXinUser.objects.get_or_create(openid=openId) 
        pre_subscribe_time = wx_user.subscribe_time
        
        pre_nickname = wx_user.nickname
        for k, v in userinfo.iteritems():
            if hasattr(wx_user, k) :
                setattr(wx_user, k, v or getattr(wx_user, k))
        
        wx_user.nickname = pre_nickname or replace_utf8mb4(wx_user.nickname.decode('utf8'))
        wx_user.unionid  = wx_user.unionid or unionId or ''
        subscribe_time   = userinfo.get('subscribe_time', None)
        if subscribe_time:
            wx_user.subscribe_time = pre_subscribe_time or datetime.datetime\
                .fromtimestamp(int(subscribe_time))
        
        key_list = ['openid','sex','language','headimgurl','country','province','nickname','unionid','subscribe_time','sceneid']
        update_model_fields(wx_user,update_fields=key_list)
        
        if not wx_user.unionid:
            return 
        
        app_key = _wx_api._wx_account.app_id
        WeixinUnionID.objects.get_or_create(openid=openId,app_key=app_key,unionid=wx_user.unionid)
    except Exception, exc:
        raise task_Update_Weixin_Userinfo.retry(exc=exc)


@task(max_retry=3,default_retry_delay=60)
def task_Mod_Merchant_Product_Status(outer_ids,status):
    
    from shopback.items.models import Product
    from shopback import signals 
    
    update_wxpids   = set([])
    _wx_api         = WeiXinAPI()
    
    try:  
        for outer_id in outer_ids:
            
            wx_skus = WXProductSku.objects.filter(outer_id=outer_id).values('product').distinct()
            wx_prodids = [p['product'] for p in wx_skus]
            
            wx_prods = WXProduct.objects.filter(product_id__in=wx_prodids).order_by('-modified')
            if wx_prods.count() == 0 :
                continue
            
            wx_product = wx_prods[0]
            wxproduct_id = wx_product.product_id
            if wxproduct_id not in update_wxpids:
                update_wxpids.add(wxproduct_id)
                #_wx_api.modMerchantProductStatus(wxproduct_id, status)
            
            product = Product.objects.get(outer_id=outer_id)
            if status == WXProduct.UP_ACTION:
                product.shelf_status = Product.UP_SHELF
                #发送商品上架消息
                signals.signal_product_upshelf.send(sender=Product,product_list=[product])
            else:
                product.shelf_status = Product.DOWN_SHELF
            product.save()
            
    except WeiXinRequestException, exc:
        raise task_Mod_Merchant_Product_Status.retry(exc=exc)
    

@task
def pullWXProductTask():
    
    _wx_api = WeiXinAPI()
    products = _wx_api.getMerchantByStatus(0)
    up_shelf_ids = []
    
    for product in products:
        
        WXProduct.objects.createByDict(product)
        up_shelf_ids.append(product['product_id'])
        
    WXProduct.objects.exclude(product_id__in=up_shelf_ids)\
        .update(status=WXProduct.DOWN_SHELF)
    
@task
def pullWaitPostWXOrderTask(begintime,endtime):
    
    update_status=[#WXOrder.WX_WAIT_PAY,
                   WXOrder.WX_WAIT_SEND,
                   WXOrder.WX_WAIT_CONFIRM,
                   WXOrder.WX_FINISHED]
    
    _wx_api = WeiXinAPI()
    
    if not begintime and _wx_api._wx_account.order_updated:
        begintime = int(time.mktime(_wx_api._wx_account.order_updated.timetuple()))
    
    dt        = datetime.datetime.now()
    endtime   = endtime and endtime or int(time.mktime(dt.timetuple()))
    
    for status in update_status:
        orders = _wx_api.getOrderByFilter(status,begintime,endtime)
        
        for order_dict in orders:
            
            order = WxShopService.createTradeByDict(_wx_api._wx_account.account_id,
                                                    order_dict)
            
            WxShopService.createMergeTrade(order)
        
    _wx_api._wx_account.changeOrderUpdated(dt)
        
@task
def pullFeedBackWXOrderTask(begintime,endtime):
    
    _wx_api = WeiXinAPI()
    
    if not begintime and _wx_api._wx_account.refund_updated:
        begintime = int(time.mktime(_wx_api._wx_account.refund_updated.timetuple()))
    
    dt        = datetime.datetime.now()
    endtime   = endtime and endtime or int(time.mktime(dt.timetuple()))
    
    orders = _wx_api.getOrderByFilter(WXOrder.WX_FEEDBACK,begintime,endtime)
    
    for order_dict in orders:
        
        order = WxShopService.createTradeByDict(_wx_api._wx_account.account_id,
                                                order_dict)
        
        WxShopService.createMergeTrade(order)
        
    _wx_api._wx_account.changeRefundUpdated(dt)
    
    
@task
def syncStockByWxShopTask(wx_product):
    
    from shopback.items.models import Product,ProductSku,ItemNumTaskLog
    from shopback.trades.models import MergeOrder
    from shopback.users.models import User
    
    if not isinstance(wx_product,WXProduct):
        wx_product = WXProduct.objects.get(product_id=wx_product)
        
    if not wx_product.sync_stock:
        return
    
    wx_api = WeiXinAPI()
    
    wx_openid = wx_api.getAccountId()
    wx_user = User.objects.get(visitor_id=wx_openid)
    
    user_percent = wx_user.stock_percent
    
    skus  =  wx_product.sku_list or []

    for sku in skus:
        
        if not sku.get('product_code',None):
            continue
        
        try:
            outer_id,outer_sku_id = Product.objects.trancecode('',
                                                               sku['product_code'],
                                                               sku_code_prior=True)
            
            #特卖商品暂不同步库存
            if outer_id.startswith(('1','8','9')) and len(outer_id) >= 9:
                continue
            
            product      = Product.objects.get(outer_id=outer_id)
            product_sku  = ProductSku.objects.get(outer_id=outer_sku_id,
                                                  product__outer_id=outer_id)
        except:
            continue
        
        if not (wx_user.sync_stock and product.sync_stock and product_sku.sync_stock):
            continue
        
        wait_nums   = (product_sku.wait_post_num>0 and
                       product_sku.wait_post_num or 0)
        remain_nums = product_sku.remain_num or 0
        real_num    = product_sku.quantity
        sync_num    = real_num - wait_nums - remain_nums
        
        #如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if sync_num>0 and user_percent>0:
            sync_num = int(user_percent*sync_num)
            
        elif sync_num >0 and sync_num <= product_sku.warn_num:
            total_num,user_order_num = MergeOrder.get_yesterday_orders_totalnum(wx_user.id,
                                                                                outer_id,
                                                                                outer_sku_id)
            if total_num>0 and user_order_num>0:
                sync_num = int(float(user_order_num)/float(total_num)*sync_num)
                
            else:
                sync_num = (real_num - wait_nums)>10 and 2 or 0 
                
        elif sync_num > 0:
            product_sku.is_assign = False
            
            update_model_fields(product_sku,update_fields=['is_assign'])
        else:
            sync_num = 0
    
#        #针对小小派，测试线上库存低量促销效果
#        if product.outer_id == '3116BG7':
#            sync_num = product_sku.warn_num > 0 and min(sync_num,product_sku.warn_num+10) or min(sync_num,15)
#    
        if product_sku.is_assign:
            sync_num = 0
            
        #同步库存数不为0，或者没有库存警告，同步数量不等于线上库存，并且店铺，商品，规格同步状态正确
        if (sync_num != sku['quantity']):
            
            vector_num = sync_num - sku['quantity']
            
            if vector_num > 0:
                wx_api.addMerchantStock(wx_product.product_id,
                                        vector_num,
                                        sku_info=sku['sku_id'])
            else:
                wx_api.reduceMerchantStock(wx_product.product_id,
                                        abs(vector_num),
                                        sku_info=sku['sku_id'])

            ItemNumTaskLog.objects.get_or_create(user_id=wx_user.user.id,
                                                 outer_id=outer_id,
                                                 sku_outer_id='wx%s'%outer_sku_id,
                                                 num=sync_num,
                                                 end_at=datetime.datetime.now())
    
@task
def syncWXProductNumTask():
    
    pullWXProductTask()
    
    wx_products = WXProduct.objects.filter(status=WXProduct.UP_SHELF)
    
    for wx_product in wx_products:
        
        syncStockByWxShopTask(wx_product)

