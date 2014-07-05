import time
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from .models import WXOrder,WXProduct,WXLogistic
from .service import WxShopService
from .weixin_apis import WeiXinAPI

@task
def pullWXProductTask():
    
    _wx_api = WeiXinAPI()
    products = _wx_api.getMerchantByStatus(0)
    
    for product in products:
        
        WXProduct.objects.createByDict(product)
    
    
    
@task
def pullWaitPostWXOrderTask(status,begintime,endtime):
    
    
    _wx_api = WeiXinAPI()
    
    if not begintime and _wx_api._wx_account.order_updated:
        begintime = int(time.mktime(_wx_api._wx_account.order_updated.timetuple()))
    
    dt        = datetime.datetime.now()
    endtime   = endtime and endtime or int(time.mktime(dt.timetuple()))
    
    orders = _wx_api.getOrderByFilter(status,begintime,endtime)
    
    
    for order_dict in orders:
        
        order = WxShopService.createTradeByDict(_wx_api._wx_account.account_id,
                                                order_dict)
        
        WxShopService.createMergeTrade(order)
        
    _wx_api._wx_account.changeOrderUpdated(dt)
        
@task
def pullFeedBackWXOrderTask(begintime,endtime):
    
    _wx_api = WeiXinAPI()
    
    if not begintime and _wx_api._wx_account.order_updated:
        begintime = time.mktime(_wx_api._wx_account.refund_updated.timetuple())
        
    endtime   = endtime and endtime or int(time.time())
    
    orders = _wx_api.getOrderByFilter(WXOrder.WX_FEEDBACK,begintime,endtime)
    
    for order_dict in orders:
        
        order = WxShopService.createTradeByDict(_wx_api._wx_account.account_id,
                                                order_dict)
        
        WxShopService.createMergeTrade(order)
        
    _wx_api._wx_account.changeRefundUpdated(dt)
    
    
