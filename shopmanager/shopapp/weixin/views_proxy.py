#encoding:utf-8
import urllib
import urllib2
from django.http import HttpResponse
from httpproxy.views import HttpProxy

import logging
from . import service
logger = logging.getLogger('django.request')

class WXMessageHttpProxy(HttpProxy):
    
    def get_wx_service(self):
        return service.WeixinUserService()
    
    def get_full_url(self, url):
        """
        Constructs the full URL to be requested.
        """
        param_str = self.request.GET.urlencode()
        request_url = self.base_url
        if url:
            request_url = u'%s/%s' % (self.base_url, url)
        request_url += '?%s' % param_str if param_str else ''
        return request_url
    
    def get(self, request):
        content    = request.REQUEST
        wx_service = self.get_wx_service()
        if wx_service.checkSignature(content.get('signature',''),
                                     content.get('timestamp',0),
                                     content.get('nonce','')):
            wx_service.activeAccount()
            return HttpResponse(content['echostr'])
        return HttpResponse(u'微信接口验证失败')

    def post(self, request, *args, **kwargs):
        content    = request.REQUEST
        wx_service = self.get_wx_service()
        if not wx_service.checkSignature(content.get('signature',''),
                                         content.get('timestamp',0),
                                         content.get('nonce','')):
            return HttpResponse(u'非法请求')
        
#         content  = request.body
#         params   = parseXML2Param(content)
#         ret_params = wx_service.handleRequest(params)
#         response = formatParam2XML(ret_params)
        
        request_url = self.get_full_url(self.url)
        request = self.create_request(request_url)
        response = urllib2.urlopen(request)
        try:
            response_body = response.read()
            status = response.getcode()
            logger.debug(self._msg % response_body)
        except urllib2.HTTPError, e:
            response_body = e.read()
            logger.error(self._msg % response_body)
            status = e.code
        
        return HttpResponse(response_body, status=status,
                content_type=response.headers['content-type'])
        
    
class WXCustomAndMediaProxy(HttpProxy):
    
    def get_wx_service(self):
        return service.WeixinUserService()
    
    def get_extra_request_params(self):
        wx_serv = self.get_wx_service()
        return {'access_token':wx_serv.getAccessToken()}
        
    def get_full_url(self, url):
        """
        Constructs the full URL to be requested.
        """
        param_str = urllib.urlencode(self.get_extra_request_params())
        param_str = '%s&%s'%(self.request.GET.urlencode(),param_str)
        request_url = self.base_url
        if url:
            request_url = u'%s/%s' % (self.base_url, url)
        request_url += '?%s' % param_str if param_str else ''
        return request_url

    def post(self, request, *args, **kwargs):
        
        request_url = self.get_full_url(self.url)
        request = self.create_request(request_url)
        response = urllib2.urlopen(request)
        try:
            response_body = response.read()
            status = response.getcode()
            logger.debug(self._msg % response_body)
        except urllib2.HTTPError, e:
            response_body = e.read()
            logger.error(self._msg % response_body)
            status = e.code
        
        return HttpResponse(response_body, status=status,
                content_type=response.headers['content-type'])
        
    get = post
    

                
        