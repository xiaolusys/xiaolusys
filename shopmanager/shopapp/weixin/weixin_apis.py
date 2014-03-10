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
from shopapp.weixin.models import WeiXinAccount

class WeiXinRequestException(Exception):
    
    def __init__(self,code=None,msg=None):
        self.code = code
        self.msg  = msg
  
    def __str__(self):
        return u'微信API调用错误:(%s,%s)'%(str(self.code),self.msg)



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
    
    
    def __init__(self):
        self._wx_account = WeiXinAccount.getAccountInstance()
        
    def getAbsoluteUrl(self,url):
        return settings.WEIXIN_API_HOST+url
        
    def handleRequest(self,url,params={},method="GET",token=True):    
        
        absolute_url = self.getAbsoluteUrl(url)
        if token :
            params.update(access_token=self.getAccessToken())
        
        if method.upper() == 'GET':
            uri = '%s?%s'%(absolute_url,urllib.urlencode(params))
            req = urllib2.urlopen(uri)
            resp = req.read()
        else:
            rst =  urllib2.Request(absolute_url)
            req = urllib2.urlopen(rst,urllib.urlencode(params))
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
        return self.handleRequest(self._create_groups_uri, {'name':name}, method='POST')
    
    
    def getGroups(self):
        return self.handleRequest(self._get_groups_uri)
    
    def getUserGroupById(self,openid):
        return self.handleRequest(self._get_user_group_uri, {'openid':openid}, method='POST')
        
    def updateGroupName(self,id,name):
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
        return self.handleRequest(self._create_menu_uri, params, method='POST')
        
    def getMenu(self):
        return self.handleRequest(self._get_menu_uri, {},method='GET')
    
    def deleteMenu(self):
        return self.handleRequest(self._detele_menu_uri, {},method='GET')
    
    def createQrcode(self,action_name,action_info,scene_id,expire_seconds=0):
        
        params = {"action_name":action_name ,"action_info": {"scene": {"scene_id": 123}}}
        if action_name=='QR_SCENE':
            params.update(expire_seconds=expire_seconds)
            
        return self.handleRequest(self._create_qrcode_uri, params,method='POST')
    
    
    