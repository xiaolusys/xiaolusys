# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db import transaction
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse

from .models import Customer, Register
from core.weixin import options
from .tasks import task_Update_Sale_Customer, task_Refresh_Sale_Customer
from shopapp.weixin.views.views import valid_openid
from shopapp.weixin.models import WeiXinUser, WeixinUnionID, WeiXinAccount

import logging

logger = logging.getLogger('django.request')


class FlashSaleBackend(object):
    """ 微信用户名，密码授权登陆 """
    create_unknown_user = True
    supports_inactive_user = False
    supports_object_permissions = False

    def authenticate(self, request, mobile, password, **kwargs):

        if not request.path.startswith('/rest'):
            return None

        if not mobile or not password:
            return AnonymousUser()

        try:
            customers = Customer.objects.filter(mobile=mobile, status=Customer.NORMAL)
            customer = None
            if customers.count() > 1:
                customer = customers.filter(user__username=mobile).first()

            if not customer:
                customer = customers.first()

            if not customer:
                return AnonymousUser

            user = customer.user
            if not user.check_password(password):
                return AnonymousUser()
        except Customer.DoesNotExist:
            logger.error('the backend login user %s not exist'%mobile)
            return AnonymousUser()

        except User.DoesNotExist:
            return AnonymousUser()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class WeixinPubBackend(object):
    """ 微信公众号授权登陆 """
    create_unknown_user = True
    supports_inactive_user = False
    supports_object_permissions = False

    def get_unoinid(self, openid, appkey):
        try:
            return WeixinUnionID.objects.get(openid=openid, app_key=appkey).unionid
        except WeixinUnionID.DoesNotExist:
            return ''

    def authenticate(self, request, auth_code, wxpub_appid, **kwargs):

        code = auth_code
        wxpub_appsecret = WeiXinAccount.get_wxpub_account_secret(wxpub_appid)
        userinfo = options.get_auth_userinfo(code,
                                             appid=wxpub_appid,
                                             secret=wxpub_appsecret,
                                             request=request)
        openid, unionid = userinfo.get('openid'), userinfo.get('unionid')
        if not openid or not unionid:
            openid, unionid = options.get_cookie_openid(request.COOKIES, wxpub_appid)

        if openid and not unionid:
            logger.warn('weixin unionid not return:openid=%s' % openid)
            unionid = self.get_unoinid(openid, wxpub_appid)

        if not valid_openid(unionid):
            return AnonymousUser()

        try:
            with transaction.atomic():
                profile = Customer.objects.get(unionid=unionid, status=Customer.NORMAL)
                # 如果openid有误，则重新更新openid
                if unionid and openid:
                    WeixinUnionID.objects.get_or_create(openid=openid,
                                                        app_key=wxpub_appid,
                                                        unionid=unionid)
                    task_Refresh_Sale_Customer.delay(userinfo, app_key=wxpub_appid)

                if profile.user:
                    if not profile.user.is_active:
                        profile.user.is_active = True
                        profile.user.save()
                    return profile.user
                else:
                    user, state = User.objects.get_or_create(username=unionid, is_active=True)
                    profile.user = user
                    profile.save()

        except Customer.DoesNotExist:
            if not self.create_unknown_user or not unionid:
                return AnonymousUser()

            nick = userinfo.get('nickname')
            thumbnail = userinfo.get('headimgurl')
            user, state = User.objects.get_or_create(username=unionid, is_active=True)
            if nick and thumbnail:
                profile, state = Customer.objects.get_or_create(unionid=unionid, user=user, nick=nick, thumbnail=thumbnail)
            else:
                profile, state = Customer.objects.get_or_create(unionid=unionid, user=user)
            # if not normal user ,no login allowed
            if profile.status != Customer.NORMAL:
                return AnonymousUser()

            WeixinUnionID.objects.get_or_create(openid=openid,
                                                app_key=wxpub_appid,
                                                unionid=unionid)
            task_Refresh_Sale_Customer.delay(userinfo, app_key=wxpub_appid)

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class WeixinAppBackend(object):
    """ 微信APP授权登陆 """
    create_unknown_user = True
    supports_inactive_user = False
    supports_object_permissions = False

    def authenticate(self, request, **kwargs):

        content = request.POST
        unionid = content.get('unionid') or kwargs.get('unionid')
        openid = content.get('openid') or kwargs.get('unionid')
        request_path = request.path
        if not ((request_path.startswith("/rest/") or
                 request_path.startswith("/games/") or
                 request_path.startswith("/bitmall/"))
                and unionid):
            return None

        if not valid_openid(openid) or not valid_openid(unionid):
            return AnonymousUser()

        params = {
            'openid': content.get('openid'),
            'unionid': content.get('unionid'),
            'nickname': content.get('nickname'),
            'headimgurl': content.get('headimgurl'),
        }
        try:
            profile = Customer.objects.get(unionid=unionid, status=Customer.NORMAL)
            if profile.user:
                user = profile.user
                if not user.is_active:
                    user.is_active = True
                    user.save()
            else:
                user, state = User.objects.get_or_create(username=unionid, is_active=True)
                profile.user = user
                profile.save()
            if profile.thumbnail != params.get('headimgurl'):  # 更新头像
                profile.thumbnail = params.get('headimgurl')
                profile.save()

        except Customer.DoesNotExist:
            if not self.create_unknown_user:
                return AnonymousUser()

            user, state = User.objects.get_or_create(username=unionid, is_active=True)
            profile, state = Customer.objects.get_or_create(unionid=unionid, user=user)
            if profile.nick == '':
                profile.set_nickname(params.get('nickname'))
                profile.thumbnail = params.get('headimgurl')
                profile.save()
            # if not normal user ,no login allowed
            if profile.status != Customer.NORMAL:
                return AnonymousUser()

        task_Refresh_Sale_Customer.delay(params, app_key=settings.WX_APPID)
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class SMSLoginBackend(object):
    """ 短信验证码登陆后台 """
    create_unknown_user = True
    supports_inactive_user = False
    supports_object_permissions = False

    def authenticate(self, request, mobile, sms_code, **kwargs):
        """
        1, get django user first;
        2, if not,then get customer user;
        3, if not else,then create django user
        """
        try:
            register = Register.objects.get(vmobile=mobile)
            if not register.is_submitable():
                return AnonymousUser()

            customers = Customer.objects.filter(mobile=mobile, status=Customer.NORMAL)
            customer  = None
            if customers.count() > 1:
                customer = customers.filter(user__username=mobile).first()

            if not customer:
                customer = customers.first()

            if not customer:
                return AnonymousUser

            user = customer.user
            if not user.is_active:
                user.is_active = True
                user.save()

        except Register.DoesNotExist:
            return AnonymousUser()
        except User.DoesNotExist:
            if not self.create_unknown_user:
                return AnonymousUser()
            user, state = User.objects.get_or_create(username=mobile, is_active=True)
            Customer.objects.create(user=user, mobile=mobile)
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
