#-*- coding:utf8 -*-
__author__ = 'meixqhi'
import re
import inspect
import copy
import time
import datetime
import json
import urllib
import urllib2
from django.conf import settings
from celery.task import task
from celery.app.task import BaseTask
from common.utils import format_datetime,format_date
from shopapp.jingdong.utils import getJDSignature
from .exceptions import JDRequestException

API_FIELDS = {
    '360buy.order.search':'return_order,vender_remark,pin,balance_used,payment_confirm_time,'
        +'logistics_id,waybill,vat_invoice_info,parent_order_id,order_type',
    '360buy.order.get':'return_order,vender_remark,pin,balance_used,payment_confirm_time,'
        +'logistics_id,waybill,vat_invoice_info,parent_order_id,order_type'
}

def raise_except_or_ret_json(content):
    
    respc = json.loads(content)
    
    if respc.has_key('error_response'):
        error_resp = respc['error_response']
        raise JDRequestException(code=error_resp['code'],
                                 msg=error_resp['zh_desc'])
    
    return respc.items[0][1]


def apis(api_method,method='GET',max_retry=3,limit_rate=0.5):
    """ docstring for tengxun apis """
    def decorator(func):
        """ docstring for decorator """
        
        func_args = copy.copy(inspect.getargspec(func).args)
        func_defaults = copy.copy(inspect.getargspec(func).defaults)
        def decorate(*args,**kwargs):
            """ docstring for decorate """
            
            params = {
                    'method':api_method,
                    'app_key':settings.JD_APP_KEY,
                    'timestamp':format_datetime(datetime.datetime.now()),
                    'v':'2.0'}
            
            app_params = {}
            if func_defaults:
                app_params.update(dict(zip(reversed(func_args), 
                                           reversed(list(func_defaults)))))
            app_params.update(dict(zip(func_args, args)))
            app_params.update(kwargs)

            from shopback.users.models import User
            #refresh user taobao session
            jd_user_id = app_params.pop('jd_user_id')
            user       = User.objects.get(uid=jd_user_id)
            
            #remove the field with value None
            params['access_token'] = user.top_session
            params_copy = dict(app_params)
            for k,v in params_copy.iteritems():
                if v == None:
                    app_params.pop(k)
                elif type(v) == bool:
                    app_params[k] = v and 'true' or 'false'
                elif type(v) == unicode:
                    app_params[k] = v.encode('utf8')
                elif type(v) == datetime.datetime:
                    app_params[k] = format_datetime(v)
                elif type(v) == datetime.date:
                    app_params[k] = format_date(v)
                    
            params['360buy_param_json'] = json.dumps(app_params)
            params['sign'] = getJDSignature(params,
                                            settings.JD_APP_SECRET,
                                            both_side=True)
            params = urllib.urlencode(params)
            url = settings.JD_API_ENDPOINT
            
            if method == 'GET':
                uri = '%s?%s'%(url,params)
                req = urllib2.urlopen(uri)
                content = req.read()
            else:
                rst = urllib2.Request(url)
                req = urllib2.urlopen(rst,params)
                content = req.read()

            return raise_except_or_ret_json(content)
        
        return decorate

    return decorator


###################### 京东用户处理 ###################
@apis('jingdong.seller.vender.info.get')
def jd_seller_vender_info_get(jd_user_id=None):
    pass

@apis('jingdong.vender.shop.query')
def jd_vender_shop_query(jd_user_id=None):
    pass

###################### 京东订单处理 ###################
@apis('360buy.order.search',method='POST')
def jd_order_search(start_date=None,end_date=None,dateType=None,
                        order_state=None,page=None,page_size=None,sortType=None,
                        optional_fields='',jd_user_id=None):
    pass

@apis('360buy.order.get',method='POST')
def jd_order_get(order_id=None,order_state=None,
                     optional_fields=API_FIELDS['360buy.order.get'],jd_user_id=None):
    pass

