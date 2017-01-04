# encoding=utf8
import os
import requests
import simplejson
import base64

from Crypto.Cipher import AES
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.response import Response
from django.conf import settings

from flashsale.pay.models.user import Customer
from shopapp.weixin.models.base import WeixinUnionID


TOKEN_TIMEOUT = 60 * 60 * 2  # token 2小时过期


class WXBizDataCrypt:
    def __init__(self, appId, sessionKey):
        self.appId = appId
        self.sessionKey = sessionKey

    def decrypt(self, encryptedData, iv):
        # base64 decode
        sessionKey = base64.b64decode(self.sessionKey)
        encryptedData = base64.b64decode(encryptedData)
        iv = base64.b64decode(iv)

        cipher = AES.new(sessionKey, AES.MODE_CBC, iv)

        decrypted = simplejson.loads(self._unpad(cipher.decrypt(encryptedData)))

        if decrypted['watermark']['appid'] != self.appId:
            raise Exception('Invalid Buffer')

        return decrypted

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]


class WeApp(object):
    appid = settings.WEAPP_APPID
    secret = settings.WEAPP_SECRET

    def get_session_key(self, code):
        url = 'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': self.appid,
            'secret': self.secret,
            'js_code': code,
            'grant_type': 'authorization_code',
        }
        resp = requests.get(url, params=params)
        return simplejson.loads(resp.content)


class WeAppViewSet(viewsets.ViewSet):
    """
    """
    authentication_classes = ()

    def login(self, request, *args, **kwargs):
        """
        GET /rest/v2/weapp/login

        params:
        - code

        return:
        {
            'session': 'xxxxx'
        }

        code 换取 session_key
        """
        code = request.GET.get('code')

        weapp = WeApp()
        data = weapp.get_session_key(code)
        session_key = data['session_key']
        openid = data['openid']

        #
        item = WeixinUnionID.objects.filter(app_key=settings.WEAPP_APPID, openid=openid).first()
        unionid = item.unionid if item else ''
        if unionid:
            customer = Customer.objects.get(unionid=unionid)
            data['unionid'] = unionid
            data['customer_id'] = customer.id

        token = 'weapp' + os.urandom(24).encode('hex')
        cache.set(token, data, TOKEN_TIMEOUT)
        resp = {
            'token': token,
            'unionid': unionid,
        }
        return Response(resp)

    def post_user_info(self, request, *args, **kwargs):
        """
        POST /rest/v2/weapp/user_info

        params:
        - encryptedData
        - rawData
        - iv
        - token

        return:
        {
            'code': 0
            'msg': ''
        }
        """
        encrypted_data = request.POST.get('encryptedData')
        iv = request.POST.get('iv')
        token = request.POST.get('x-token')
        user_info = request.POST.get('rawData')

        token_value = cache.get(token)
        if not token_value:
            return Response({'code': 1, 'msg': '没有登录'})

        if user_info:
            try:
                user_info = simplejson.loads(user_info)
            except Exception:
                return Response({'code': 2, 'msg': '参数错误'})

        session_key = token_value['session_key']
        openid = token_value['openid']

        pc = WXBizDataCrypt(WeApp.appid, session_key)
        resp = pc.decrypt(encrypted_data, iv)
        unionid = resp['unionId']

        customer = Customer.objects.filter(unionid=unionid).first()
        if not customer:
            with transaction.atomic():
                user, state = User.objects.get_or_create(username=unionid, is_active=True)

                customer = Customer()
                customer.unionid = unionid
                customer.user = user
                customer.thumbnail = user_info.get('avatarUrl', '')
                customer.nick = user_info.get('nickName', '')
                customer.save()

                WeixinUnionID.objects.get_or_create(
                    app_key=settings.WEAPP_APPID,
                    openid=openid,
                    defaults={'unionid': unionid}
                )

        token_value['customer_id'] = customer.id
        token_value['unionid'] = unionid
        cache.set(token, token_value, TOKEN_TIMEOUT)
        return Response({'code': 0, 'mgs': 'OK'})

