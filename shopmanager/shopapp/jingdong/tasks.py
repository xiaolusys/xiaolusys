#-*- coding:utf8 -*-
import time
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from .models import JDShop,JDOrder,JDProduct,JDLogistic
from .service import JDShopService
from .apis import api

@task
def pullJDProductByVenderidTask(vender_id,ware_status=1):
    
    page = 1
    page_size = 100
    has_next  = True
    
    while has_next:
        
        ware_response = api.jd_wares_search(ware_status=ware_status,
                                            page=page,
                                            page_size=100,
                                            jd_user_id=vender_id)
        
        has_next = ware_response['total'] > page*page_size
        page += 1
        
        for ware in ware_response['ware_infos']:
            
            jd_product,state = JDProduct.objects.get_or_create(ware_id=ware['ware_id'])
            
            for k,v in ware.iteritems():
                hasattr(jd_product,k) and setattr(jd_product,k,v)
            
            jd_product.online_time = ware.get('online_time') or None
            jd_product.offline_time = ware.get('offline_time') or None
            jd_product.modified = ware.get('modified') or None
                
            jd_product.save()
        
        print 'ware',ware
    
@task
def pullJDLogisticByVenderidTask(vender_id):
    
    from shopback.users.models import User
    
    logistic_list = api.jd_delivery_logistics_get(jd_user_id=vender_id)
    
    for logistic in logistic_list['logistics_list']:
        
        jd_logistic,state = JDLogistic.objects.get_or_create(
                                logistics_id=logistic['logistics_id'])
        
        for k,v in logistic.iteritems():
            hasattr(jd_logistic,k) and setattr(jd_logistic, k, v)
            
        jd_logistic.save()
    
    
@task
def pullJDOrderByModifiedTask(jd_shop,status_list,begintime=None,endtime=None):
    
    page = 1
    page_size = 2
    has_next = True
    
    while has_next:
        response = api.jd_order_search(start_date=begintime,
                                       end_date=endtime,
                                       order_state=','.join(status_list),
                                       page=page,
                                       page_size=page_size,
                                       jd_user_id=jd_shop.vender_id)
        
        has_next      = response['order_total'] > page * page_size
        page += 1
        
        for order_dict in response['order_info_list']:
            
            jd_order = JDShopService.createTradeByDict(jd_shop.vender_id,
                                                       order_dict)
            
            JDShopService.createMergeTrade(jd_order)
            
    
@task
def pullAllJDShopOrderByModifiedTask(status_list=[JDOrder.ORDER_STATE_WSTO,
                                                  JDOrder.ORDER_STATE_FL,
                                                  JDOrder.ORDER_STATE_TC]):
    
    from shopback.users.models import User
    
    for user in User.effect_users.JINGDONG:
        
        jd_shop = JDShop.objects.get(vender_id=user.visitor_id)    
        
        if not jd_shop.order_updated:
            pullJDOrderByModifiedTask(jd_shop,status_list)   
            continue
        
        endtime = datetime.datetime.now()
        
        pullJDOrderByModifiedTask(jd_shop,
                                  status_list,
                                  begintime=jd_shop.order_updated,
                                  endtime=endtime) 
        
        jd_shop.updateOrderUpdated(endtime)
        
        
        
