# coding:utf-8
import hashlib
import time
import datetime
import json
import urllib
import urllib2

from django.conf import settings

from shopapp.weixin.models import WeiXinAccount
from common.utils import (
    randomString,
    update_model_fields,
    randomString,
    getSignatureWeixin,
    cache_lock
)

REFRESH_WX_TOKEN_CACHE_KEY = 'REFRESH_WX_TOKEN_KEY'


class WeiXinRequestException(Exception):
    def __init__(self, code=None, msg=None):
        self.code = code
        self.message = msg

    def __str__(self):
        return u'微信API错误:(%s,%s)' % (str(self.code), self.message)


class WeiXinAPI(object):
    _token_uri = "/cgi-bin/token"
    _user_info_uri = "/cgi-bin/user/info"
    _create_groups_uri = "/cgi-bin/groups/create"
    _get_grounps_uri = "/cgi-bin/groups/get"
    _get_user_group_uri = "cgi-bin/groups/getid"
    _update_group_uri = "/cgi-bin/groups/update"
    _update_group_member_uri = "/cgi-bin/groups/members/update"
    _get_user_info_uri = "/cgi-bin/user/info"
    _get_followers_uri = "/cgi-bin/user/get"
    _create_menu_uri = "/cgi-bin/menu/create"
    _get_menu_uri = "/cgi-bin/menu/get"
    _detele_menu_uri = "/cgi-bin/menu/delete"
    _create_qrcode_uri = "/cgi-bin/qrcode/create"
    _media_get_uri = "/cgi-bin/media/get"
    _js_ticket_uri = "/cgi-bin/ticket/getticket"
    _template_send_uri = '/cgi-bin/message/template/send'
    _get_qrcode_template_url = '{0}/cgi-bin/showqrcode?ticket=%s'.format(settings.WEIXIN_QRCODE_HOST)

    # 微信小店接口
    _merchant_get_uri = "/merchant/get"
    _merchant_getbystatus_uri = "/merchant/getbystatus"
    _merchant_stock_add_uri = "/merchant/stock/add"
    _merchant_stock_reduce_uri = "/merchant/stock/reduce"
    _merchant_order_getbyid_uri = "/merchant/order/getbyid"
    _merchant_order_getbyfilter_uri = "/merchant/order/getbyfilter"
    _merchant_order_setdelivery_uri = "/merchant/order/setdelivery"
    _merchant_modproductstatus_uri = "/merchant/modproductstatus"
    _merchant_category_getsku_uri = "/merchant/category/getsku"

    # 上传文件
    _upload_media_uri = "/cgi-bin/media/upload"

    # 微信原生支付URL
    _native_url = "weixin://wxpay/bizpayurl"
    _deliver_notify_url = "/pay/delivernotify"
    _wxpub_id = None
    _account_data = {}

    # 客服消息接口
    _send_custom_message_uri = '/cgi-bin/message/custom/send'

    def __init__(self):
        pass

    def setAccountId(self, wxpubId=None, appKey=None):
        assert wxpubId or appKey, 'wxpub_id or appKey need one'
        account_valueslist = WeiXinAccount.getWeixinAccountValueList()
        if wxpubId:
            accountid_maps = dict([(wc['account_id'], wc) for wc in account_valueslist])
            self._account_data = accountid_maps.get(wxpubId)
        else:
            wxappkey_maps = dict([(wc['app_id'], wc) for wc in account_valueslist])
            account_data = wxappkey_maps.get(appKey)
            self._account_data = account_data

        if not self._account_data:
            raise Exception('not found wxpubId(%s) or appkey(%s) account' %(wxpubId, appKey))

        self._wxpub_id = self._account_data.get('account_id')

    def getAccountId(self):
        if self._wx_account.isNone():
            return None
        return self._wx_account.account_id

    def getAccount(self):
        if not self._wxpub_id:
            self.setAccountId(appKey=settings.WEIXIN_APPID)
        if not hasattr(self, '_account') or self._account.account_id != self._wxpub_id:
            self._account = WeiXinAccount.objects.get(account_id=self._wxpub_id)
        return self._account

    _wx_account = property(getAccount)

    def getAbsoluteUrl(self, uri, token):
        url = settings.WEIXIN_API_HOST + uri
        return token and '%s?access_token=%s' % (url, self.getAccessToken()) or url + '?'

    def checkSignature(self, signature, timestamp, nonce):

        if time.time() - int(timestamp) > 3600:
            return False
        sign_array = ['%s' % i for i in [self._account_data.get('token'), timestamp, nonce]]
        sign_array.sort()
        sha1_value = hashlib.sha1(''.join(sign_array)).hexdigest()
        return sha1_value == signature

    def handleRequest(self, uri, params={}, method="GET", token=True):

        absolute_url = self.getAbsoluteUrl(uri, token)

        if method.upper() == 'GET':
            url = '%s&%s' % (absolute_url, urllib.urlencode(params))
            req = urllib2.urlopen(url)
            resp = req.read()

        else:
            rst = urllib2.Request(absolute_url)
            req = urllib2.urlopen(rst, type(params) == dict and
                                  urllib.urlencode(params) or params)
            resp = req.read()

        content = json.loads(resp, strict=False)

        if content.get('errcode', 0):
            raise WeiXinRequestException(content['errcode'], content['errmsg'])

        return content

    def refresh_token(self):
        """
        禁止刷新token，由定时任务负责刷新token
        """
        params = {'grant_type': 'client_credential',
                  'appid': self._wx_account.app_id,
                  'secret': self._wx_account.app_secret}

        content = self.handleRequest(self._token_uri, params, token=False)

        self._wx_account.access_token = content['access_token']
        self._wx_account.expired = datetime.datetime.now()
        self._wx_account.expires_in = content['expires_in']
        self._wx_account.save(update_fields=['access_token', 'expired', 'expires_in'])

        self._account_data.update({'access_token':content['access_token']})
        return content['access_token']

    def getAccessToken(self, force_update=False):
        """
        禁止刷新token, force_update参数无效
        """
        return self._account_data.get('access_token', '')

    def getCustomerInfo(self, openid, lang='zh_CN'):
        return self.handleRequest(self._user_info_uri, {'openid': openid, 'lang': lang})

    def createGroups(self, name):
        name = type(name) == unicode and name.encode('utf8') and name
        return self.handleRequest(self._create_groups_uri, {'name': name}, method='POST')

    def getGroups(self):
        return self.handleRequest(self._get_groups_uri)

    def getUserGroupById(self, openid):
        return self.handleRequest(self._get_user_group_uri, {'openid': openid}, method='POST')

    def updateGroupName(self, id, name):
        name = type(name) == unicode and name.encode('utf8') and name
        return self.handleRequest(self._update_group_uri, {'id': id, 'name': name}, method='POST')

    def updateGroupMember(self, openid, to_groupid):
        return self.handleRequest(self._update_group_member_uri, {'openid': openid,
                                                                  'to_groupid': to_groupid},
                                  method='POST')

    def getUserInfo(self, openid):
        return self.handleRequest(self._get_user_info_uri, {'openid': openid}, method='GET')

    def getFollowersID(self, next_openid=''):
        return self.handleRequest(self._get_followers_uri, {'next_openid': next_openid},
                                  method='GET')

    def sendTemplate(self, openid, template_id, to_url, data):
        params = {
            'touser': openid,
            'template_id': template_id,
            'url': to_url,
            'data': data,
        }
        params = json.dumps(params)
        return self.handleRequest(self._template_send_uri, params, method='POST')

    def createMenu(self, params):
        assert type(params) == dict
        jmenu = json.dumps(params, ensure_ascii=False)
        return self.handleRequest(self._create_menu_uri, str(jmenu), method='POST')

    def getMenu(self):
        return self.handleRequest(self._get_menu_uri, {}, method='GET')

    def deleteMenu(self):
        return self.handleRequest(self._detele_menu_uri, {}, method='GET')

    def createQRcode(self, action_name, scene_id, expire_seconds=30 * 24 * 3600):
        """
        action_name: QR_SCENE为临时,QR_LIMIT_SCENE为永久,QR_LIMIT_STR_SCENE为永久的字符串参数值；
        """
        params = {"action_name": str(action_name).upper(),
                  "action_info": {"scene": {"scene_id": scene_id}}}

        if action_name.upper() == 'QR_SCENE':
            params.update(expire_seconds=expire_seconds)

        return self.handleRequest(self._create_qrcode_uri,
                                  params=json.dumps(params),
                                  method='POST')

    def genQRcodeAccesssUrl(self, ticket):
        return self._get_qrcode_template_url % ticket

    def getMerchant(self, product_id):

        params = json.dumps({'product_id': product_id})

        response = self.handleRequest(self._merchant_get_uri,
                                      str(params),
                                      method='POST')
        return response['product_info']

    def getMerchantByStatus(self, status):

        params = json.dumps({'status': status},
                            ensure_ascii=False)
        response = self.handleRequest(self._merchant_getbystatus_uri,
                                      str(params),
                                      method='POST')
        return response['products_info']

    def modMerchantProductStatus(self, product_id, status):

        params = json.dumps({'product_id': product_id, 'status': status},
                            ensure_ascii=False)
        response = self.handleRequest(self._merchant_modproductstatus_uri,
                                      str(params),
                                      method='POST')
        return response

    def addMerchantStock(self, product_id, quantity, sku_info=''):

        params = json.dumps({'product_id': product_id,
                             'quantity': quantity,
                             'sku_info': sku_info},
                            ensure_ascii=False)
        return self.handleRequest(self._merchant_stock_add_uri,
                                  str(params),
                                  method='POST')

    def reduceMerchantStock(self, product_id, quantity, sku_info=''):

        params = json.dumps({'product_id': product_id,
                             'quantity': quantity,
                             'sku_info': sku_info},
                            ensure_ascii=False)
        return self.handleRequest(self._merchant_stock_reduce_uri,
                                  str(params),
                                  method='POST')

    def getOrderById(self, order_id):

        params = json.dumps({'order_id': str(order_id)}, ensure_ascii=False)
        response = self.handleRequest(self._merchant_order_getbyid_uri,
                                      str(params),
                                      method='POST')
        return response['order']

    def getOrderByFilter(self, status=None, begintime=None, endtime=None):

        params = {}

        if status:
            params.update(status=status)

            if begintime:
                params.update(begintime=begintime)

            if endtime:
                params.update(endtime=endtime)

        params_str = json.dumps(params,
                                ensure_ascii=False)

        response = self.handleRequest(self._merchant_order_getbyfilter_uri,
                                      str(params_str),
                                      method='POST')
        return response['order_list']

    def getSkuByCategory(self, cate_id=None):

        params = {'cate_id': cate_id}

        params_str = json.dumps(params,
                                ensure_ascii=False)

        response = self.handleRequest(self._merchant_category_getsku_uri,
                                      str(params_str),
                                      method='POST')

        return response['sku_table']

    def deliveryOrder(self, order_id, delivery_company, delivery_track_no, need_delivery=1, is_others=0):

        params = json.dumps({'order_id': order_id,
                             'delivery_company': delivery_company,
                             'delivery_track_no': delivery_track_no,
                             'is_others': is_others,
                             'need_delivery': need_delivery},
                            ensure_ascii=False)

        return self.handleRequest(self._merchant_order_setdelivery_uri,
                                  str(params),
                                  method='POST')

    def deliverNotify(self, open_id, trans_id, out_trade_no,
                      deliver_status=1, deliver_msg="ok"):

        params = {
            "appid": self._wx_account.app_id,
            "appkey": self._wx_account.pay_sign_key,
            "openid": open_id,
            "transid": trans_id,
            "out_trade_no": out_trade_no,
            "deliver_timestamp": "%.0f" % time.time(),
            "deliver_status": deliver_status,
            "deliver_msg": deliver_msg
        }

        params['app_signature'] = getSignatureWeixin(params)
        params['sign_method'] = 'sha1'

        params.pop('appkey')

        return self.handleRequest(self._deliver_notify_url,
                                  str(json.dumps(params)),
                                  method='POST')

    def getJSTicket(self):
        return self._account_data.get('js_ticket', '')


    def refreshJSTicket(self):
        """ js ticket只能定时刷新，请勿在用户请求中刷新，会产生竞争 """
        access_token = self.getAccessToken()
        js_url = self.getAbsoluteUrl(self._js_ticket_uri, access_token) + '&type=jsapi'
        req = urllib2.urlopen(js_url)
        content = json.loads(req.read())

        self._wx_account.js_ticket = content['ticket']
        self._wx_account.js_expired = datetime.datetime.now()
        self._wx_account.save(update_fields=['js_ticket', 'js_expired'])

        self._account_data.update({'js_ticket': content['ticket']})
        return content['ticket']

    def getShareSignParams(self, referal_url):
        """ referal_url:用户当前停留页面（即发起分享页）的链接地址 """
        sign_params = {"noncestr": randomString(),
                       "jsapi_ticket": self.getJSTicket(),
                       "timestamp": int(time.time()),
                       "url": referal_url}
        key_pairs = ["%s=%s" % (k, v) for k, v in sign_params.iteritems()]
        key_pairs.sort()

        sign_params['signature'] = hashlib.sha1('&'.join(key_pairs)).hexdigest()
        sign_params['app_id'] = self._wx_account.app_id

        return sign_params

    def genNativeSignParams(self, product_id):

        signString = {'appid': self._wx_account.app_id,
                      'timestamp': str(int(time.time())),
                      'noncestr': randomString(),
                      'productid': str(product_id),
                      'appkey': self._wx_account.app_secret
                      }
        signString.update(signString, getSignatureWeixin(signString))
        signString.pop('appkey')

        return signString

    def genPaySignParams(self, package):
        signString = {'appid': self._wx_account.app_id,
                      'timestamp': str(int(time.time())),
                      'noncestr': randomString(),
                      'package': package,
                      'appkey': self._wx_account.pay_sign_key
                      }
        signString.update(signString, getSignatureWeixin(signString))
        signString.pop('appkey')

        return signString

    def upload_media(self, media_stream):
        absolute_url = '%s%s?access_token=%s&type=image'%(settings.WEIXIN_API_HOST,
                                                    self._upload_media_uri,self.getAccessToken())

        from poster.encode import multipart_encode, MultipartParam
        from poster.streaminghttp import register_openers
        register_openers()

        params = MultipartParam(
            name='media',
            filename='image.jpg',
            filetype='image/jpeg',
            fileobj=media_stream
        )
        datagen, headers = multipart_encode([params])
        request = urllib2.Request(absolute_url, datagen, headers)
        resp = urllib2.urlopen(request).read()

        content = json.loads(resp, strict=False)
        if content.get('errcode', 0):
            raise WeiXinRequestException(content['errcode'], content['errmsg'])

        return content

    def send_custom_message(self, params):
        response = self.handleRequest(self._send_custom_message_uri,
                                      json.dumps(params),
                                      method='POST')
        return response

    def genPackageSignParams(self, package):
        return

    def getMediaDownloadUrl(self, media_id):
        return '%s%s?access_token=%s&media_id=%s' % (settings.WEIXIN_MEDIA_HOST,
                                                     self._media_get_uri,
                                                     self.getAccessToken(),
                                                     media_id)
