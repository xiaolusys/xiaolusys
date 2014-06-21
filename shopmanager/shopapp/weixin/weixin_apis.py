#-*- coding:utf8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import re
import inspect
import copy
import time
import datetime
import json
import urllib
import urllib2
from django.conf import settings
from shopapp.weixin.models import WeiXinAccount

class WeiXinRequestException(Exception):
    
    def __init__(self,code=None,msg=None):
        self.code = code
        self.msg  = msg
  
    def __str__(self):
        return u'微信API错误:(%s,%s)'%(str(self.code),self.msg)



class WeiXinAPI(object):
    
    _token_uri          = "/cgi-bin/token"
    _user_info_uri      = "/cgi-bin/user/info"
    _create_groups_uri  = "/cgi-bin/groups/create"
    _get_grounps_uri    = "/cgi-bin/groups/get"
    _get_user_group_uri = "cgi-bin/groups/getid"
    _update_group_uri   = "/cgi-bin/groups/update"
    _update_group_member_uri  = "/cgi-bin/groups/members/update"
    _get_user_info_uri  = "/cgi-bin/user/info"
    _get_followers_uri  = "/cgi-bin/user/get"
    _create_menu_uri    = "/cgi-bin/menu/create"
    _get_menu_uri       = "/cgi-bin/menu/get"
    _detele_menu_uri    = "/cgi-bin/menu/delete"
    _create_qrcode_uri  = "/cgi-bin/qrcode/create"
    
    #微信小店接口
    _merchant_get_uri   = "/merchant/get"
    _merchant_getbystatus_uri   = "/merchant/getbystatus"
    _merchant_stock_add_uri   = "/merchant/stock/add"
    _merchant_stock_reduce_uri   = "/merchant/stock/reduce"
    _merchant_order_getbyid_uri   = "/merchant/order/getbyid"
    _merchant_order_getbyfilter_uri   = "/merchant/order/getbyfilter"
    _merchant_order_setdelivery_uri   = "/merchant/order/setdelivery"
    
    def __init__(self):
        self._wx_account = WeiXinAccount.getAccountInstance()
        
    def getAbsoluteUrl(self,uri,token):
        url = settings.WEIXIN_API_HOST+uri
        return token and '%s?access_token=%s'%(url,self.getAccessToken()) or url+'?'
        
    def handleRequest(self,uri,params={},method="GET",token=True):    
        
        absolute_url = self.getAbsoluteUrl(uri,token)
        
        if method.upper() == 'GET':
            url = '%s&%s'%(absolute_url,urllib.urlencode(params))
            req = urllib2.urlopen(url)
            resp = req.read()
        else:
            rst = urllib2.Request(absolute_url)
            req = urllib2.urlopen(rst,type(params)==dict and 
                                  urllib.urlencode(params) or params)
            resp = req.read()
        
        content = json.loads(resp)
        
        if content.has_key('errcode') and content['errcode'] != 0:
            raise WeiXinRequestException(content['errcode'],content['errmsg'])
        
        return content
        
    def getAccessToken(self):
        
        if not self._wx_account.isExpired():
            return self._wx_account.access_token
        
        params = {'grant_type':'client_credential',
                  'appid':self._wx_account.app_id,
                  'secret':self._wx_account.app_secret}
        
        content = self.handleRequest(self._token_uri, params,token=False)
        
        self._wx_account.access_token = content['access_token']
        self._wx_account.expired      = datetime.datetime.now()
        self._wx_account.expires_in   = content['expires_in']
        self._wx_account.save()
        
        return content['access_token']
    
    def getCustomerInfo(self,openid,lang='zh_CN'):
        return self.handleRequest(self._user_info_uri, {'openid':openid,'lang':lang})
    
    
    def createGroups(self,name):
        name = type(name)==unicode and name.encode('utf8') and name
        return self.handleRequest(self._create_groups_uri, {'name':name}, method='POST')
    
    
    def getGroups(self):
        return self.handleRequest(self._get_groups_uri)
    
    def getUserGroupById(self,openid):
        return self.handleRequest(self._get_user_group_uri, {'openid':openid}, method='POST')
        
    def updateGroupName(self,id,name):
        name = type(name)==unicode and name.encode('utf8') and name
        return self.handleRequest(self._update_group_uri, {'id':id,'name':name}, method='POST')    
        
    def updateGroupName(self,openid,to_groupid):
        return self.handleRequest(self._update_group_member_uri, {'openid':openid,
                                                      'to_groupid':to_groupid}, 
                                  method='POST')   
    
    def getUserInfo(self,openid):
        return self.handleRequest(self._get_user_info_uri, {'openid':openid},method='GET') 
        
    def getFollowersID(self,next_openid=''):
        return self.handleRequest(self._get_followers_uri, {'next_openid':next_openid}, 
                                  method='GET') 
        
    def createMenu(self,params):
        assert type(params) == dict
        jmenu = json.dumps(params,ensure_ascii=False)
        return self.handleRequest(self._create_menu_uri, str(jmenu), method='POST')
        
    def getMenu(self):
        return self.handleRequest(self._get_menu_uri, {},method='GET')
    
    def deleteMenu(self):
        return self.handleRequest(self._detele_menu_uri, {},method='GET')
    
    def createQRcode(self,action_name,action_info,scene_id,expire_seconds=0):
        
        action_name = (type(action_name)==unicode and 
                       action_name.encode('utf8') and 
                       action_name)
        
        params = {"action_name":action_name ,
                  "action_info": {"scene": {"scene_id": scene_id}}}
        if action_name=='QR_SCENE':
            params.update(expire_seconds=expire_seconds)
            
        return self.handleRequest(self._create_qrcode_uri, params,method='POST')
        
    def checkSignature(self,signature,timestamp,nonce):
        
        import time
        import hashlib
        
        if time.time() - int(timestamp) > 300:
            return False
        
        sign_array = [self._wx_account.token,timestamp,nonce]
        sign_array.sort()
        
        sha1_value = hashlib.sha1(''.join(sign_array))

        return sha1_value.hexdigest() == signature
    
    
    def getMerchant(self,product_id):
        return self.handleRequest(self._merchant_get_uri, 
                                  {'product_id':product_id},
                                  method='GET')
        
    def getMerchantByStatus(self,status):
        return self.handleRequest(self._merchant_getbystatus_uri, 
                                  {'status':status},
                                  method='POST')
        
    def addMerchantStock(self,product_id,quantity,sku_info=''):
        return self.handleRequest(self._merchant_stock_add_uri, 
                                  {'product_id':product_id,
                                   'quantity':quantity,
                                   'sku_info':sku_info},
                                  method='POST')
        
    def reduceMerchantStock(self,product_id,quantity,sku_info=''):
        return self.handleRequest(self._merchant_stock_reduce_uri, 
                                  {'product_id':product_id,
                                   'quantity':quantity,
                                   'sku_info':sku_info},
                                  method='POST')
        
    def getOrderById(self,order_id):
        
        response = self.handleRequest(self._merchant_order_getbyid_uri, 
                                  {'order_id':order_id},
                                  method='POST')
        return response['order']
        
    def getOrderByFilter(self,status,begintime,endtime):
        
        response = self.handleRequest(self._merchant_order_getbyfilter_uri, 
                                  {'status':status,
                                   'begintime':begintime,
                                   'endtime':endtime},
                                  method='POST')
        return response['order_list']
        
    def deliveryOrder(self,order_id,delivery_company,delivery_track_no):
        return self.handleRequest(self._merchant_order_setdelivery_uri, 
                                  {'order_id':order_id,
                                   'delivery_company':delivery_company,
                                   'delivery_track_no':delivery_track_no},
                                  method='POST')
        
    
    
    
    
    
