#-*- coding:utf8 -*-
__author__ = 'meixqhi'
import re
import types
import inspect
import copy
import time
import datetime
import json
import urllib
import urllib2
from django.conf import settings
from django.core.cache import cache
from celery.task import task
from celery.app.task import BaseTask
from auth.utils import getSignatureTaoBao,format_datetime,format_date,refresh_session
from auth.apis.exceptions import TaobaoRequestException,RemoteConnectionException,UserFenxiaoUnuseException,\
    AppCallLimitedException,APIConnectionTimeOutException,ServiceRejectionException

import logging
logger = logging.getLogger('auth.apis')

reject_regex = re.compile(r'^isv.\w+-service-rejection$')


API_FIELDS = {
    'taobao.user.get':'user_id,uid,nick,sex,buyer_credit,seller_credit,location,created,last_visit,birthday,type,has_more_pic,item_img_num'
         +',item_img_size,prop_img_num,prop_img_size,auto_repost,promoted_type,status,alipay_bind,consumer_protection,alipay_account,alipay_no',
    'taobao.itemcats.authorize.get':'brand.vid, brand.name, item_cat.cid, item_cat.name, item_cat.status,item_cat.sort_order,item_cat.parent_cid,item_cat.is_parent'
         +',xinpin_item_cat.cid, xinpin_item_cat.name, xinpin_item_cat.status, xinpin_item_cat.sort_order, xinpin_item_cat.parent_cid, xinpin_item_cat.is_parent',
    'taobao.itemcats.get':'cid,parent_cid,name,is_parent,status,sort_order',
    'taobao.itemcats.authorize.get':'brand.vid,brand.name,item_cat.cid,item_cat.name,item_cat.status,item_cat.sort_order,item_cat.parent_cid,item_cat.is_parent'
         +',xinpin_item_cat.cid,xinpin_item_cat.name,xinpin_item_cat.status,xinpin_item_cat.sort_order,xinpin_item_cat.parent_cid,xinpin_item_cat.is_parent',
    'taobao.itemprops.get':'pid, name, must, multi, prop_values',
    'taobao.itempropvalues.get':'cid,pid,prop_name,vid,name,name_alias,status,sort_order',
    'taobao.item.get':'has_showcase,detail_url,num_iid,title,outer_id,price,approve_status,delist_time,list_time,modified,num,props_name,skus'
         +',nick,type,cid,pic_url,num,props,valid_thru,price,has_discount,has_invoice,has_warranty,postage_id,seller_cids',
    'taobao.items.list.get':'item',
    'taobao.products.get':'product_id,tsc,cat_name,name',
    'taobao.items.get':'num_iid,title,nick,pic_url,cid,price,type,delist_time,post_fee,volume,score,location',
    'taobao.items.search':'iid,num_iid,title,nick,pic_url,cid,price,type,delist_time,post_fee',
    'taobao.item.skus.get':'sku_id,num_iid,created,modified,num_iid,outer_id,price,properties,quantity,sku_id,status',
    'taobao.products.get':'product_id,outer_id,name,inner_name,created,modified,cid,cat_name,tsc,props,props_str,binds,binds_str,sale_props'
         +',sale_props_str,collect_num,price,desc,pic_url,product_imgs,product_prop_imgs,pic_path,vertical_market,customer_props,property_alias,level,status',
    'taobao.products.search':'product_id,name,pic_url,cid,props,price,tsc',
    'taobao.items.inventory.get':'approve_status,num_iid,title,nick,type,cid,pic_url,num,props,valid_thru,list_time'
        +',price,has_discount,has_invoice,has_warranty,has_showcase, modified,delist_time,postage_id,seller_cids,outer_id',
    'taobao.items.onsale.get':'approve_status,num_iid,title,nick,type,cid,pic_url,num,props,valid_thru,list_time,price,has_discount,has_invoice,has_warranty'
        +',has_showcase,modified,delist_time,postage_id,seller_cids,outer_id,skus,props_name',
    'taobao.trades.sold.get':'seller_nick,buyer_nick,title,type,created,tid,status,modified,payment,discount_fee,adjust_fee,post_fee,total_fee,received_payment,commission_fee,buyer_obtain_point_fee'
        +',point_fee,real_point_fee,pic_path,pay_time,end_time,consign_time,num_iid,num,price,shipping_type,receiver_name,receiver_state,receiver_city,receiver_district,receiver_address,receiver_zip'
        +',receiver_mobile,receiver_phone,orders.title,orders.pic_path,orders.price,orders.num,orders.num_iid,orders.sku_id,orders.refund_status'
        +',orders.status,orders.oid,orders.total_fee,orders.payment,orders.discount_fee,orders.adjust_fee,orders.sku_properties_name'
        +',orders.item_meal_name,orders.item_meal_id,orders.buyer_rate,orders.seller_rate,orders.outer_iid,orders.outer_sku_id,orders.refund_id,orders.seller_type',
    'taobao.trade.fullinfo.get':'seller_nick,buyer_nick,title,type,created,tid,status,modified,payment,received_payment,adjust_fee,post_fee,total_fee,commission_fee,discount_fee'
        +',buyer_obtain_point_fee,pic_path,buyer_email,seller_alipay_no,num_iid,num,price,orders',
    'taobao.trade.amount.get':'tid,alipay_no,created,pay_time,end_time,total_fee,payment,post_fee,cod_fee,commission_fee,buyer_obtain_point_fee,order_amounts,promotion_details',
    'taobao.logistics.companies.get':'id,code,name,reg_mail_no',
    'taobao.logistics.orders.detail.get':'tid,order_code,is_quick_cod_order,out_sid,company_name,seller_id,seller_nick,buyer_nick,item_title,delivery_start,delivery_end'
        +',receiver_name,receiver_phone,receiver_mobile,location,type,created,modified,seller_confirm,company_name,is_success,freight_payer,status',
    'taobao.logistics.orders.get':'tid,seller_nick,buyer_nick,delivery_start, delivery_end,out_sid,item_title,receiver_name, created,modified,status,type,freight_payer,seller_confirm,company_name',
    'taobao.refunds.receive.get':'refund_id,tid,title,buyer_nick,num_iid,seller_nick,total_fee,status,created,refund_fee,oid,good_status,company_name,sid,payment,reason,desc,has_good_return,modified,order_status',
    'taobao.fenxiao.products.get':'skus,images',
}


def single_instance_task(timeout,prefix=''):
    def task_exc(func):
        def delay(self, *args, **kwargs):
            return self.apply(args, kwargs)

        def decorate(*args, **kwargs):
#            if settings.DEBUG:
#                return func(*args, **kwargs)

            lock_id = "celery-single-instance-" + func.__name__
            acquire_lock = lambda: cache.add(lock_id, "true", timeout)
            release_lock = lambda: cache.delete(lock_id)
            if acquire_lock() :
                try:
                    return func(*args, **kwargs)
                finally:
                    release_lock()
            else :
                logger.error('the task %s is executing.'%func.__name__)
        result = task(name='%s%s' % (prefix,func.__name__))(decorate)
        if settings.DEBUG:
            result.delay = types.MethodType(delay, result)
        return result
    return task_exc


def raise_except_or_ret_json(content):
    content = json.loads(content)

    if not isinstance(content,(dict,)):
        raise exc.ContentNotRightException(sub_msg=content)
    elif content.has_key('error_response'):
        content = content['error_response']
        code     = content.get('code',None)
        sub_code = content.get('sub_code',None)
        msg      = content.get('msg',None)
        sub_msg  = content.get('sub_msg','')

        if code == 520 and sub_code == u'isp.remote-connection-error':
            raise RemoteConnectionException(
                    code=code,msg=msg,sub_code=sub_code,sub_msg=sub_msg)
        elif code == 520 and sub_code == u'isp.remote-service-timeout':
            raise APIConnectionTimeOutException(
                code=code,msg=msg,sub_code=sub_code,sub_msg=sub_msg)
        elif code == 520 and  reject_regex.match(sub_code):
            raise ServiceRejectionException(
                code=code,msg=msg,sub_code=sub_code,sub_msg=sub_msg)
        elif code == 670 or code == 15 and sub_code == u'isv.invalid-parameter:user_id_num':
            raise UserFenxiaoUnuseException(
                    code=code,msg=msg,sub_code=sub_code,sub_msg=sub_msg)
        elif code == 7 and sub_code == u'accesscontrol.limited-by-app-access-count':
            raise AppCallLimitedException(
                    code=code,msg=msg,sub_code=sub_code,sub_msg=sub_msg)
        else :
            raise TaobaoRequestException(
                    code=code,msg=msg,sub_code=sub_code,sub_msg=sub_msg)
    return content


def apis(api_method,method='GET',max_retry=3,limit_rate=0.5):
    """ docstring for tengxun apis """
    def decorator(func):
        """ docstring for decorator """
        
        def retry_func(fn):
            def wrap(*args,**kwargs):
                acquire_lock = lambda: cache.add(api_method, "true", limit_rate)
                try_times = 0
                for i in xrange(0,max_retry):
                    if not acquire_lock():
                        time.sleep(limit_rate)
                    try:
                        return fn(*args,**kwargs)
                    except RemoteConnectionException,e:
                        try_times += 1
                        if try_times >= max_retry:
                            logger.error('remote connect error：%s ,retry：%d'%
                                         (response_list,try_times))
                            raise e    
                    except APIConnectionTimeOutException,e:
                        try_times += 1
                        if try_times >= max_retry:
                            logger.error('connect error：%s ,retry：%d'%
                                         (response_list,try_times))
                            raise e
                        time.sleep(settings.API_TIME_OUT_SLEEP)
                    except ServiceRejectionException,e:
                        try_times += 1
                        if try_times >= max_retry:
                            logger.error('request over limit times per minute：%s ,retry：%d'%
                                         (response_list,try_times))
                            raise e
                        time.sleep(settings.API_OVER_LIMIT_SLEEP)
            return wrap
                    
        
        func_args = copy.copy(inspect.getargspec(func).args)
        func_defaults = copy.copy(inspect.getargspec(func).defaults)
        def decorate(*args,**kwargs):
            """ docstring for decorate """
            
            timestamp = format_datetime(datetime.datetime.now())
            params = {
                'method':api_method,
                'timestamp':timestamp,
                'format':'json',
                'app_key':settings.APPKEY,
                'v':'2.0',
                'sign_method':'md5'}

            if func_defaults:
                params.update(dict(zip(reversed(func_args), reversed(list(func_defaults)))))
            params.update(dict(zip(func_args, args)))
            params.update(kwargs)

            from shopback.users.models import User
            #refresh user taobao session
            tb_user_id = params.pop('tb_user_id')
            user       = User.objects.get(visitor_id=tb_user_id)

            refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)
            #remove the field with value None

            params['session'] = user.top_session
            params_copy = dict(params)
            for k,v in params_copy.iteritems():
                if not v:
                    params.pop(k)
                elif type(v) == unicode:
                    params[k] = v.encode('utf8')
                elif type(v) == datetime.datetime:
                    params[k] = format_datetime(v)
                elif type(v) == datetime.date:
                    params[k] = format_date(v)

            params_copy = None

            sign_value = getSignatureTaoBao(params,settings.APPSECRET)
            params['sign'] = sign_value

            url = settings.TAOBAO_API_ENDPOINT
            if method == 'GET':
                uri = '%s?%s'%(url,urllib.urlencode(params))
                req = urllib2.urlopen(uri)
                content = req.read()
            else:
                req = urllib2.urlopne(url,body=urllib.urlencode(params))
                content = req.read()

            return raise_except_or_ret_json(content)
        
        return retry_func(decorate)

    return decorator

############# user apis ###################
@apis('taobao.user.get')
def taobao_user_get(nick=None,fields=API_FIELDS['taobao.user.get'],tb_user_id=None):
    pass

@apis('taobao.users.get')
def taobao_users_get(nicks=None,fields=API_FIELDS['taobao.user.get'],tb_user_id=None):
    pass


############# itemcats apis ###################
@apis('taobao.itemcats.authorize.get')
def taobao_itemcats_authorize_get(parent_cid=None,cids=None,fields=API_FIELDS['taobao.itemcats.authorize.get'],tb_user_id=None):
    pass

@apis('taobao.itemcats.get')
def taobao_itemcats_get(parent_cid=None,cids=None,fields=API_FIELDS['taobao.itemcats.get'],tb_user_id=None):
    pass

@apis('taobao.itemprops.get')
def taobao_itemprops_get(cid=None,pid=None,fields=API_FIELDS['taobao.itemprops.get'],tb_user_id=None):
    pass

@apis('taobao.itempropvalues.get')
def taobao_itempropvalues_get(cid=None,pvs=None,fields=API_FIELDS['taobao.itempropvalues.get'],tb_user_id=None):
    pass

############# items apis ###################

@apis('taobao.item.get')
def taobao_item_get(num_iid=None,fields=API_FIELDS['taobao.item.get'],tb_user_id=None):
    pass

@apis('taobao.item.update')
def taobao_item_update(num_iid=None,num=None,tb_user_id=None):
    pass

@apis('taobao.item.quantity.update')
def taobao_item_quantity_update(num_iid=None,quantity=None,sku_id=None,type=1,tb_user_id=None):
    pass

@apis('taobao.item.update.delisting')
def taobao_item_update_delisting(num_iid=None,tb_user_id=None):
    pass

@apis('taobao.item.update.listing')
def taobao_item_update_listing(num_iid=None,num=0,tb_user_id=None):
    pass

@apis('taobao.items.list.get')
def taobao_items_list_get(num_iids=None,fields=API_FIELDS['taobao.items.list.get'],tb_user_id=None):
    pass

@apis('taobao.products.get')
def taobao_products_get(nick=None,page_no=1,page_size=20,fields=API_FIELDS['taobao.products.get'],tb_user_id=None):
    pass

@apis('taobao.items.search')
def taobao_items_search(q=None,cid=None,nicks=None,props=None,product_id=None,order_by=None,page_no=None,
                        page_size=None,fields=API_FIELDS['taobao.items.search'],tb_user_id=None):
    pass

@apis('taobao.items.get')
def taobao_items_get(q=None,cid=None,nicks=None,props=None,product_id=None,order_by=None,page_no=None,
                     page_size=None,fields=API_FIELDS['taobao.items.get'],tb_user_id=None):
    pass

@apis('taobao.item.skus.get')
def taobao_item_skus_get(num_iids=None,fields=API_FIELDS['taobao.item.skus.get'],tb_user_id=None):
    pass

@apis('taobao.products.get')
def taobao_products_get(nick=None,page_no=None,page_size=None,fields=API_FIELDS['taobao.products.get'],tb_user_id=None):
    pass

@apis('taobao.products.search')
def taobao_products_search(q=None,cid=None,props=None,fields=API_FIELDS['taobao.products.search'],tb_user_id=None):
    pass

@apis('taobao.items.inventory.get')
def taobao_items_inventory_get(q=None,banner=None,cid=None,seller_cids=None,page_no=None,page_size=None,
                               fields=API_FIELDS['taobao.items.inventory.get'],tb_user_id=None):
    pass

@apis('taobao.items.onsale.get')
def taobao_items_onsale_get(q=None,banner=None,cid=None,seller_cids=None,page_no=None,page_size=None,
                            fields=API_FIELDS['taobao.items.onsale.get'],tb_user_id=None):
    pass

@apis('taobao.item.recommend.add')
def taobao_item_recommend_add(num_iid=None,tb_user_id=None):
    pass

############# trades apis ###################

@apis('taobao.trades.sold.get',max_retry=20,limit_rate=10)
def taobao_trades_sold_get(start_created=None,end_created=None,page_no=None,page_size=None,use_has_next=None,
                           fields=API_FIELDS['taobao.trades.sold.get'],tb_user_id=None):
    pass

@apis('taobao.trades.sold.increment.get',max_retry=20,limit_rate=10)
def taobao_trades_sold_increment_get(start_modified=None,end_modified=None,page_no=None,page_size=None,use_has_next=None,
                                     fields=API_FIELDS['taobao.trades.sold.get'],tb_user_id=None):
    pass

@apis('taobao.trade.fullinfo.get')
def taobao_trade_fullinfo_get(tid=None,fields=API_FIELDS['taobao.trade.fullinfo.get'],tb_user_id=None):
    pass

@apis('taobao.topats.trades.fullinfo.get')
def taobao_topats_trades_fullinfo_get(tids=None,fields=API_FIELDS['taobao.trade.fullinfo.get'],tb_user_id=None):
    pass

@apis('taobao.trade.amount.get',max_retry=5,limit_rate=1)
def taobao_trade_amount_get(tid=None,fields=API_FIELDS['taobao.trade.amount.get'],tb_user_id=None):
    pass

@apis('taobao.trade.memo.update')
def taobao_trade_memo_update(tid=None,memo=None,flag=None,reset=None,tb_user_id=None):
    pass

@apis('taobao.trade.memo.add')
def taobao_trade_memo_add(tid=None,memo=None,flag=None,tb_user_id=None):
    pass

############# itemcats apis ################

@apis('taobao.itemcats.get')
def taobao_itemcats_get(parent_cid=None,cids=None,fields=API_FIELDS['taobao.itemcats.get'],tb_user_id=None):
    pass

@apis('taobao.itemcats.authorize.get')
def taobao_itemcats_authorize_get(fields=API_FIELDS['taobao.itemcats.authorize.get'],tb_user_id=None):
    pass

############# post apis ###################
@apis('taobao.logistics.companies.get')
def taobao_logistics_companies_get(fields=API_FIELDS['taobao.logistics.companies.get'],tb_user_id=None):
    pass

@apis('taobao.logistics.orders.detail.get',max_retry=10,limit_rate=5)
def taobao_logistics_orders_detail_get(tid=None,seller_confirm='yes',start_created=None,end_created=None,page_no=None,page_size=None,
                                       fields=API_FIELDS['taobao.logistics.orders.detail.get'],tb_user_id=None):
    pass

@apis('taobao.logistics.orders.get')
def taobao_logistics_orders_get(tid=None,seller_confirm='yes',start_created=None,end_created=None,page_no=None,page_size=None,
                                fields=API_FIELDS['taobao.logistics.orders.get'],tb_user_id=None):
    pass

@apis('taobao.logistics.online.send')
def taobao_logistics_online_send(tid=None,out_sid=None,company_code=None,sender_id=None,cancel_id=None,feature=None,tb_user_id=None):
    pass

@apis('taobao.logistics.online.confirm')
def taobao_logistics_online_confirm(tid=None,out_sid=None,tb_user_id=None):
    pass


###############  fengxiao apis  ##################
@apis('taobao.fenxiao.orders.get',max_retry=20,limit_rate=20)
def taobao_fenxiao_orders_get(start_created=None,end_created=None,time_type=None,purchase_order_id=None,
                              page_no=None,page_size=None,status=None,tb_user_id=None):
    pass

@apis('taobao.fenxiao.products.get',max_retry=20,limit_rate=20)
def taobao_fenxiao_products_get(outer_id=None,productcat_id=None,status=None,pids=None,item_ids=None,start_modified=None,end_modified=None,
                                page_no=None,page_size=None,fields=API_FIELDS['taobao.fenxiao.products.get'],tb_user_id=None):
    pass
################  refund apis  ##################
@apis('taobao.refunds.receive.get',max_retry=20,limit_rate=20)
def taobao_refunds_receive_get(status=None,start_modified=None,end_modified=None,type='guarantee_trade,auto_delivery,fenxiao',
                               page_no=None,page_size=None,fields=API_FIELDS['taobao.refunds.receive.get'],tb_user_id=None):
    pass
