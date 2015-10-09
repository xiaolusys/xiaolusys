#encoding:utf-8
import time
import urllib2
from django.http import HttpResponse
from httpproxy.views import HttpProxy

import logging
from . import service
logger = logging.getLogger('weixin.proxy')

class WXMessageHttpProxy(HttpProxy):
    
    def get_wx_api(self,pub_id):
        wx_api =service.WeiXinAPI()
        wx_api.setAccountId(wxpubId=pub_id)
        return wx_api
    
    def get_full_url(self, url):
        """
        Constructs the full URL to be requested.
        """
        param_str = self.request.GET.urlencode()
        request_url = self.base_url
        url     = url.lstrip('/')
        if url:
            request_url = request_url.rstrip('/')
            request_url = u'%s/%s' % (self.base_url, url)
        request_url += '?%s' % param_str if param_str else ''
        return request_url
    
    def get(self, request, pub_id):
        content  = request.REQUEST
        wx_api   = self.get_wx_api(pub_id)
        if wx_api.checkSignature(content.get('signature',''),
                                 content.get('timestamp',0),
                                 content.get('nonce','')):
            wx_api._wx_account.activeAccount()
            return HttpResponse(content['echostr'])
        logger.debug('sign fail:{0}'.format(content))
        return HttpResponse(u'微信接口验证失败')

    def post(self, request, pub_id, *args, **kwargs):
        content    = request.REQUEST
        wx_api   = self.get_wx_api(pub_id)
        if not wx_api.checkSignature(content.get('signature',''),
                                     content.get('timestamp',0),
                                     content.get('nonce','')):
            logger.debug('sign fail:{0}'.format(content))
            return HttpResponse(u'非法请求')
        
#         content  = request.body
#         params   = parseXML2Param(content)
#         ret_params = wx_service.handleRequest(params)
#         response = formatParam2XML(ret_params)
        
        request_url = self.get_full_url(self.url)
        request = self.create_request(request_url,body=request.body)
        response = urllib2.urlopen(request)
        start = time.time()
        try:
            response_body = response.read()
            status = response.getcode()
            logger.debug(self._msg % ('%s\n%s'%(request_url,response_body)))
        except urllib2.HTTPError, e:
            response_body = e.read()
            logger.error(self._msg % ('%s\n%s'%(request_url,response_body)))
            status = e.code
        end = time.time()
        logger.debug('\nconsume seconds：%.2f'%(end - start))
        return HttpResponse(response_body, status=status,
                content_type=response.headers['content-type'])
        
    
class WXCustomAndMediaProxy(HttpProxy):
    
    def get_wx_api(self):
        return service.WeiXinAPI()
    
    def get_extra_request_params(self):
        wx_serv = self.get_wx_api()
        return {'access_token':wx_serv.getAccessToken()}
        
    def get_full_url(self, url):
        """
        Constructs the full URL to be requested.
        """
        param_str = self.request.GET.urlencode()
        request_url = self.base_url
        url     = url.lstrip('/')
        if url:
            request_url = request_url.rstrip('/')
            request_url = u'%s/%s' % (self.base_url, url)
        request_url += '?%s' % param_str if param_str else ''
        return request_url

    def post(self, request, *args, **kwargs):
        """
        Proxy for the Request
        """
        request_url = self.get_full_url(self.url)
        request = self.create_request(request_url,body=request.body)
        response = urllib2.urlopen(request)
        start = time.time()
        try:
            response_body = response.read()
            status = response.getcode()
            logger.debug(self._msg % ('%s\n%s'%(request_url,response_body)))
        except urllib2.HTTPError, e:
            response_body = e.read()
            logger.error(self._msg % ('%s\n%s'%(request_url,response_body)))
            status = e.code
        end = time.time()
        logger.debug('\nconsume seconds：%.2f'%(end - start))
        return HttpResponse(response_body, status=status,
                content_type=response.headers['content-type'])
        
    get = post

import json
import datetime
from django.views.generic import View

class WXTokenProxy(View):
    
    def get_wx_api(self,app_key):
        wx_api = service.WeiXinAPI()
        wx_api.setAccountId(appKey=app_key)
        return wx_api
    
    def get(self, request):
        
        content = request.GET
        appid   = content.get('appid')
        secret  = content.get('secret')
        error_resp = HttpResponse(json.dumps({"errcode":40013,"errmsg":"invalid appid"}), 
                                  content_type='application/json')
        if not appid or not secret:
            return error_resp
        wx_api = self.get_wx_api(appid)
        if wx_api._wx_account.app_secret != secret:
            return error_resp
        access_token = wx_api.getAccessToken(force_update=True)
        resp = {"access_token":access_token,"expires_in":55*60}
        logger.debug('refresh token:[%s]%s'%(datetime.datetime.now(),resp))
        return HttpResponse(json.dumps(resp), content_type='application/json')
        
        