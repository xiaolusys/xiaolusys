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
from common.utils import getSignatureTaoBao,format_datetime,format_date,refresh_session
from auth.apis.exceptions import ContentNotRightException,RemoteConnectionException,APIConnectionTimeOutException,\
    ServiceRejectionException,UserFenxiaoUnuseException,AppCallLimitedException,InsufficientIsvPermissionsException,\
    SessionExpiredException,LogisticServiceBO4Exception,TaobaoRequestException,LogisticServiceB60Exception

import logging
logger = logging.getLogger('django.request')

reject_regex = re.compile(r'^isv.\w+-service-rejection$')


API_FIELDS = {
    'taobao.user.seller.get':'user_id,uid,nick,sex,buyer_credit,seller_credit,location,created,last_visit,'
    
}



def raise_except_or_ret_json(content):
    content = json.loads(content)

    return content


def apis(api_method,method='GET',max_retry=3,limit_rate=0.5):
    """ docstring for tengxun apis """
    def decorator(func):
        """ docstring for decorator """
        
        def retry_func(fn):
            def wrap(*args,**kwargs):
                return fn(*args,**kwargs)
            return wrap
        
        func_args = copy.copy(inspect.getargspec(func).args)
        func_defaults = copy.copy(inspect.getargspec(func).defaults)
        def decorate(*args,**kwargs):
            """ docstring for decorate """
            
            params = {
                'method':api_method,
                'format':'json',
                'v':'2.0',}

            if func_defaults:
                params.update(dict(zip(reversed(func_args), reversed(list(func_defaults)))))
            params.update(dict(zip(func_args, args)))
            params.update(kwargs)

            from shopback.users.models import User
            #refresh user taobao session
            tb_user_id = params.pop('tb_user_id')
            user       = User.objects.get(visitor_id=tb_user_id)
            #refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)
            #remove the field with value None
            params['access_token'] = user.top_session
            params_copy = dict(params)
            for k,v in params_copy.iteritems():
                if v == None:
                    params.pop(k)
                elif type(v) == bool:
                    params[k] = v and 'true' or 'false'
                elif type(v) == unicode:
                    params[k] = v.encode('utf8')
                elif type(v) == datetime.datetime:
                    params[k] = format_datetime(v)
                elif type(v) == datetime.date:
                    params[k] = format_date(v)
                    
            params_copy = None
            url = settings.TAOBAO_API_ENDPOINT
            if method == 'GET':
                uri = '%s?%s'%(url,urllib.urlencode(params))
                req = urllib2.urlopen(uri)
                content = req.read()
            else:
                rst = urllib2.Request(absolute_url)
                req = urllib2.urlopen(rst,urllib.urlencode(params))
                content = req.read()

            return raise_except_or_ret_json(content)
        
        return retry_func(decorate)

    return decorator
