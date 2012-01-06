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

            sign_value = getSignatureTaoBao(params,settings.APPSECRET)
            params['sign'] = sign_value

            url = settings.TAOBAO_API_ENDPOINT
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

@apis('taobao.user.get')
def taobao_user_get(nick=None,fields=API_FIELDS['taobao.user.get'],session=None):
    pass

@apis('taobao.users.get')
def taobao_users_get(nicks=None,fields=API_FIELDS['taobao.user.get'],session=None):
    pass

@apis('taobao.itemcats.authorize.get')
def taobao_itemcats_authorize_get(parent_cid=None,cids=None,fields=API_FIELDS['taobao.itemcats.authorize.get'],session=None):
    pass

@apis('taobao.itemcats.get')
def taobao_itemcats_get(parent_cid=None,cids=None,fields=API_FIELDS['taobao.itemcats.get'],session=None):
    pass

@apis('taobao.itemprops.get')
def taobao_itemcats_get(cid=None,pid=None,fields=API_FIELDS['taobao.itemprops.get'],session=None):
    pass
  