# encoding:utf-8
import time
import urllib2
from django.http import HttpResponse
from httpproxy.views import HttpProxy

from shopapp.weixin.models import  WeiXinAutoResponse
from . import tasks

import logging
from . import service

logger = logging.getLogger('weixin.proxy')


class WXMessageHttpProxy(HttpProxy):
    def get_wx_api(self, pub_id):
        wx_api = service.WeiXinAPI()
        wx_api.setAccountId(wxpubId=pub_id)
        return wx_api

    def get_full_url(self, url):
        """
        Constructs the full URL to be requested.
        """
        param_str = self.request.GET.urlencode()
        request_url = self.base_url
        url = url.lstrip('/')
        if url:
            request_url = request_url.rstrip('/')
            request_url = u'%s/%s' % (self.base_url, url)
        request_url += '?%s' % param_str if param_str else ''
        return request_url

    def get(self, request, pub_id):
        content = request.REQUEST
        wx_api = self.get_wx_api(pub_id)
        if wx_api.checkSignature(content.get('signature', ''),
                                 content.get('timestamp', 0),
                                 content.get('nonce', '')):
            wx_api._wx_account.activeAccount()
            return HttpResponse(content['echostr'])
        logger.error('sign fail:{0}'.format(content))
        return HttpResponse(u'微信接口验证失败')

    def post(self, request, pub_id, *args, **kwargs):
        content = request.REQUEST
        wx_api = self.get_wx_api(pub_id)
        if not wx_api.checkSignature(content.get('signature', ''),
                                     content.get('timestamp', 0),
                                     content.get('nonce', '')):
            logger.error('sign fail:{0}'.format(content))
            return HttpResponse(u'非法请求')

        request_body = request.body
        params = service.parseXML2Param(request_body)

        openid = params.get('FromUserName')
        wx_pubid = params.get('ToUserName')
        event    = params.get('Event') or ''
        msgtype  = params.get('MsgType') or ''
        eventKey = params.get('EventKey') or ''

        # 获取信息和创建帐户
        tasks.task_get_unserinfo_and_create_accounts.delay(openid, wx_pubid)
        
        # 处理关注／取关事件
        if event in ('subscribe', 'unsubscribe'):
            tasks.task_subscribe_or_unsubscribe_update_userinfo.delay(openid, wx_pubid, event, eventKey)

        if event == WeiXinAutoResponse.WX_EVENT_SUBSCRIBE or\
           event == WeiXinAutoResponse.WX_EVENT_SCAN or \
           event == WeiXinAutoResponse.WX_EVENT_CLICK: 
            ret_params = service.handleWeiXinMenuRequest(openid, wx_pubid, event, eventKey)
            response = service.formatParam2XML(ret_params)
            return HttpResponse(response, content_type="text/xml")
        
        ret_params = {'ToUserName': params['FromUserName'],
                      'FromUserName': params['ToUserName'],
                      'CreateTime': int(time.time())}
        ret_params.update(WeiXinAutoResponse.respEmptyString())
        response = service.formatParam2XML(ret_params)
        return HttpResponse(response, content_type="text/xml")
        #　如果公众号由多客服处理，直接转发
        # if wx_api._account.isResponseToDRF():
        #     ret_params = {'ToUserName': params['FromUserName'],
        #                   'FromUserName': params['ToUserName'],
        #                   'CreateTime': int(time.time())}
        #     ret_params.update(WeiXinAutoResponse.respDKF())
        #     resp_drfxml = service.formatParam2XML(ret_params)
        #     return  HttpResponse(resp_drfxml, content_type="text/xml")

        # request_url = self.get_full_url(self.url)
        # request_header = {'Content-type': request.META.get('CONTENT_TYPE'),
        #                   'Content-length': request.META.get('CONTENT_LENGTH')}
        # request = self.create_request(request_url, body=request.body, headers=request_header)
        # response = urllib2.urlopen(request)
        # start = time.time()
        # try:
        #     response_body = response.read()
        #     status = response.getcode()
        #     logger.debug(self._msg % ('%s\nQ%s\nP%s' % (request_url, request_body, response_body)))
        # except urllib2.HTTPError, e:
        #     response_body = e.read()
        #     logger.error(self._msg % ('%s\nQ%s\nP%s' % (request_url, request_body, response_body)))
        #     status = e.code
        # end = time.time()
        # logger.debug('\nconsume seconds：%.2f' % (end - start))
        # return HttpResponse(response_body, status=status,
        #                     content_type=response.headers['content-type'])


class WXCustomAndMediaProxy(HttpProxy):
    def get_wx_api(self):
        return service.WeiXinAPI()

    def get_extra_request_params(self):
        wx_serv = self.get_wx_api()
        return {'access_token': wx_serv.getAccessToken()}

    def get_full_url(self, url):
        """
        Constructs the full URL to be requested.
        """
        param_str = self.request.GET.urlencode()
        request_url = self.base_url
        url = url.lstrip('/')
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
        request_body = request.body
        request_header = {'Content-type': request.META.get('CONTENT_TYPE'),
                          'Content-length': request.META.get('CONTENT_LENGTH')}
        request = self.create_request(request_url, body=request.body, headers=request_header)
        response = urllib2.urlopen(request)
        start = time.time()
        try:
            response_body = response.read()
            status = response.getcode()
            logger.debug(self._msg % ('%s\nQ%s\nP%s' % (request_url, request_body, response_body)))
        except urllib2.HTTPError, e:
            response_body = e.read()
            logger.error(self._msg % ('%s\nQ%s\nP%s' % (request_url, request_body, response_body)))
            status = e.code
        end = time.time()
        logger.debug('\nconsume seconds：%.2f' % (end - start))
        return HttpResponse(response_body, status=status,
                            content_type=response.headers['content-type'])

    get = post


import json
import datetime
from django.views.generic import View


class WXTokenProxy(View):
    def get_wx_api(self, app_key):
        wx_api = service.WeiXinAPI()
        wx_api.setAccountId(appKey=app_key)
        return wx_api

    def get(self, request):
        content = request.GET
        appid = content.get('appid')
        secret = content.get('secret')
        error_resp = HttpResponse(json.dumps({"errcode": 40013, "errmsg": "invalid appid"}),
                                  content_type='application/json')
        if not appid or not secret:
            return error_resp
        wx_api = self.get_wx_api(appid)
        if wx_api._wx_account.app_secret != secret:
            return error_resp
        access_token = wx_api.getAccessToken()
        resp = {"access_token": access_token, "expires_in": 5 * 60}
        logger.debug('refresh token:[%s]%s' % (datetime.datetime.now(), resp))
        return HttpResponse(json.dumps(resp), content_type='application/json')


import urlparse
from django.conf import settings
from django.shortcuts import get_object_or_404
from shopback.items.models import Product


class SaleProductSearch(View):
    """
        特卖商品查询接口，提供
    """

    def get(self, request):
        content = request.GET
        itemid = content.get('itemid')
        user_id = content.get('user_id', '')

        product = get_object_or_404(Product, id=itemid)
        product_detail = product.detail
        resp_params = {
            "items": {
                "id": product.id,
                "name": product.name,
                "imageurl": product.pic_path,
                "url": urlparse.urljoin(settings.M_SITE_URL, '/pages/shangpinxq.html?id=%s' % product.id),
                "currency": "￥",
                "siteprice": '%.2f' % product.agent_price,
                "marketprice": '%.2f' % product.std_sale_price,
                "category": str(product.category),
                "brand": "小鹿美美",
                "custom1": ["可选颜色", product_detail and product_detail.color or ''],
                "custom2": ["可选尺码", ','.join([s.name for s in product.normal_skus])],
                "custom3": ["材质", product_detail and product_detail.material or ''],
                "custom4": ["洗涤说明", product_detail and product_detail.wash_instructions or ''],
                "custom5": ["备注", product_detail and product_detail.note or '']
            }
        }

        return HttpResponse(json.dumps(resp_params), content_type='application/json')
