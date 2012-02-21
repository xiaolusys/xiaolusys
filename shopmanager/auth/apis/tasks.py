import inspect
import copy
import urllib
import urllib2
import datetime
import json
from django.conf import settings
from auth.utils import getSignatureTaoBao,format_datetime


import logging
logger = logging.getLogger('auth.apis')


API_FIELDS = {
    'taobao.user.get':'user_id,uid,nick,sex,buyer_credit,seller_credit,location,created,last_visit,birthday,type,has_more_pic,item_img_num,'
         +'item_img_size,prop_img_num,prop_img_size,auto_repost,promoted_type,status,alipay_bind,consumer_protection,alipay_account,alipay_no',
    'taobao.itemcats.authorize.get':'brand.vid, brand.name, item_cat.cid, item_cat.name, item_cat.status,item_cat.sort_order,item_cat.parent_cid,item_cat.is_parent,'
         +' xinpin_item_cat.cid, xinpin_item_cat.name, xinpin_item_cat.status, xinpin_item_cat.sort_order, xinpin_item_cat.parent_cid, xinpin_item_cat.is_parent',
    'taobao.itemcats.get':'cid,parent_cid,name,is_parent,status,sort_order',
    'taobao.itemprops.get':'pid, name, must, multi, prop_values',
    'taobao.itempropvalues.get':'cid,pid,prop_name,vid,name,name_alias,status,sort_order',
    'taobao.item.get':'has_showcase,detail_url,num_iid,title,outer_id,price,approve_status,delist_time,list_time,modified,num,'
         +'sku.sku_id,sku.properties,sku.quantity,sku.price,sku.outer_id,sku.status',
    'taobao.items.list.get':'item',
    'taobao.products.get':'product_id,tsc,cat_name,name',
    'taobao.items.get':'num_iid,title,nick,pic_url,cid,price,type,delist_time,post_fee,volume,score,location',
    'taobao.items.search':'iid,num_iid,title,nick,pic_url,cid,price,type,delist_time,post_fee',
    'taobao.products.search':'product_id,name,pic_url,cid,props,price,tsc',
    'taobao.items.inventory.get':'approve_status,num_iid,title,nick,type,cid,pic_url,num,props,valid_thru,list_time,'
        +'price,has_discount,has_invoice,has_warranty,has_showcase, modified,delist_time,postage_id,seller_cids,outer_id',
    'taobao.items.onsale.get':'approve_status,num_iid,title,nick,type,cid,pic_url,num,props,valid_thru,list_time,price,has_discount,has_invoice,has_warranty'
        +',has_showcase,modified,delist_time,postage_id,seller_cids,outer_id',
    'taobao.trades.sold.get':'seller_nick, buyer_nick, title, type, created, tid, status, modified, payment, received_payment, commission_fee, pic_path,'
        +'num_iid, num, price,orders.title, orders.pic_path, orders.price, orders.num, orders.num_iid, orders.sku_id, orders.refund_status, '
        +'orders.status, orders.oid, orders.total_fee, orders.payment, orders.discount_fee, orders.adjust_fee, orders.sku_properties_name,'
        +' orders.item_meal_name,orders.item_meal_id, orders.buyer_rate, orders.seller_rate, orders.outer_iid, orders.outer_sku_id, orders.refund_id, orders.seller_type  ',
}



def apis(api_method,method='GET'):
    """ docstring for tengxun apis """
    def decorator(func):
        """ docstring for decorator """
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

            #remove the field with value None
            params_copy = dict(params)
            for k,v in params_copy.iteritems():
                if not v:
                    params.pop(k)
                elif type(v) == unicode:
                    params[k] = v.encode('utf8')

            params_copy = None

            sign_value = getSignatureTaoBao(params,settings.APPSECRET)
            params['sign'] = sign_value

            url = settings.TAOBAO_API_ENDPOINT
            content = 'null'
            if method == 'GET':
                try:
                    uri = '%s?%s'%(url,urllib.urlencode(params))
                    req = urllib2.urlopen(uri)
                    content = req.read()
                except Exception,exc:
                    logger.error('Error calling sina api: %s' % exc, exc_info=True)
            else:
                try:
                    req = urllib2.urlopne(url,body=urllib.urlencode(params))
                    content = req.read()
                except Exception,exc:
                    logger.error('Error calling sina api: %s' % exc, exc_info=True)

            return json.loads(content)

        return decorate

    return decorator

############# user apis ###################
@apis('taobao.user.get')
def taobao_user_get(nick=None,fields=API_FIELDS['taobao.user.get'],session=None):
    pass

@apis('taobao.users.get')
def taobao_users_get(nicks=None,fields=API_FIELDS['taobao.user.get'],session=None):
    pass


############# itemcats apis ###################
@apis('taobao.itemcats.authorize.get')
def taobao_itemcats_authorize_get(parent_cid=None,cids=None,fields=API_FIELDS['taobao.itemcats.authorize.get'],session=None):
    pass

@apis('taobao.itemcats.get')
def taobao_itemcats_get(parent_cid=None,cids=None,fields=API_FIELDS['taobao.itemcats.get'],session=None):
    pass

@apis('taobao.itemprops.get')
def taobao_itemprops_get(cid=None,pid=None,fields=API_FIELDS['taobao.itemprops.get'],session=None):
    pass

@apis('taobao.itempropvalues.get')
def taobao_itempropvalues_get(cid=None,pvs=None,fields=API_FIELDS['taobao.itempropvalues.get'],session=None):
    pass

############# items apis ###################

@apis('taobao.item.get')
def taobao_item_get(num_iid=None,fields=API_FIELDS['taobao.item.get'],session=None):
    pass

@apis('taobao.item.update')
def taobao_item_update(num_iid=None,num=None,session=None):
    pass

@apis('taobao.item.quantity.update')
def taobao_item_quantity_update(num_iid=None,quantity=None,sku_id=None,type=1,session=None):
    pass

@apis('taobao.item.update.delisting')
def taobao_item_update_delisting(num_iid=None,session=None):
    pass

@apis('taobao.item.update.listing')
def taobao_item_update_listing(num_iid=None,num=0,session=None):
    pass

@apis('taobao.items.list.get')
def taobao_items_list_get(num_iids=None,fields=API_FIELDS['taobao.items.list.get'],session=None):
    pass

@apis('taobao.products.get')
def taobao_products_get(nick=None,page_no=1,page_size=20,fields=API_FIELDS['taobao.products.get'],session=None):
    pass

@apis('taobao.items.search')
def taobao_items_search(q=None,cid=None,nicks=None,props=None,product_id=None,order_by=None,page_no=None,page_size=None,fields=API_FIELDS['taobao.items.search'],session=None):
    pass

@apis('taobao.items.get')
def taobao_items_get(q=None,cid=None,nicks=None,props=None,product_id=None,order_by=None,page_no=None,page_size=None,fields=API_FIELDS['taobao.items.get'],session=None):
    pass

@apis('taobao.products.search')
def taobao_products_search(q=None,cid=None,props=None,fields=API_FIELDS['taobao.products.search'],session=None):
    pass

@apis('taobao.items.inventory.get')
def taobao_items_inventory_get(q=None,banner=None,cid=None,seller_cids=None,page_no=None,page_size=None,fields=API_FIELDS['taobao.items.inventory.get'],session=None):
    pass

@apis('taobao.items.onsale.get')
def taobao_items_onsale_get(q=None,banner=None,cid=None,seller_cids=None,page_no=None,page_size=None,fields=API_FIELDS['taobao.items.onsale.get'],session=None):
    pass

@apis('taobao.item.recommend.add')
def taobao_item_recommend_add(num_iid=None,session=None):
    pass

############# trades apis ###################

@apis('taobao.trades.sold.get')
def taobao_trades_sold_get(start_created=None,end_created=None,page_no=None,page_size=None,use_has_next=None,fields=API_FIELDS['taobao.trades.sold.get'],session=None):
    pass

@apis('taobao.trades.sold.increment.get')
def taobao_trades_sold_increment_get(start_modified=None,end_modified=None,page_no=None,page_size=None,use_has_next=None,fields=API_FIELDS['taobao.trades.sold.get'],session=None):
    pass



############# items apis ###################

############# items apis ###################

  