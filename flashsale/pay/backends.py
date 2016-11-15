# -*- encoding:utf-8 -*-

from django.db import models
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse

from .models import Customer, Register
from core.weixin import options
from .tasks import task_Update_Sale_Customer, task_Refresh_Sale_Customer
from shopapp.weixin.views import valid_openid
from shopapp.weixin.models import WeiXinUser, WeixinUnionID

import logging

logger = logging.getLogger('django.request')


class FlashSaleBackend(object):
    """ 微信用户名，密码授权登陆 """
    create_unknown_user = True
    supports_inactive_user = False
    supports_object_permissions = False

    def authenticate(self, request, **kwargs):

        if not request.path.endswith(reverse('flashsale_login')):
            return None

        username = request.POST.get('username')
        password = request.POST.get('password')
        if not username or not password:
            messages.add_message(request, messages.ERROR, u'请输入用户名及密码')
            return AnonymousUser()

        try:
            user = User.objects.get(username=username)
            customer = Customer.objects.get(user=user)
            if not customer.is_loginable():
                messages.add_message(request, messages.ERROR, u'用户状态异常')
                return AnonymousUser()
            if not user.check_password(password):
                messages.add_message(request, messages.ERROR, u'用户名或密码错误')
                return AnonymousUser()
        except Customer.DoesNotExist:
            messages.add_message(request, messages.ERROR, u'用户信息异常')
            return AnonymousUser()

        except User.DoesNotExist:
            messages.add_message(request, messages.ERROR, u'用户名或密码错误')
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

    def authenticate(self, request, authen_keys=[], **kwargs):
        content = request.GET
        if (not request.path.startswith(("/mm/", "/rest/", "/sale/", "/m/"))
            or kwargs.get('username')
            or kwargs.get('unionid')
            or content.get('unionid')):
            return None

        code = content.get('code')
        userinfo = options.get_auth_userinfo(code,
                                             appid=settings.WXPAY_APPID,
                                             secret=settings.WXPAY_SECRET,
                                             request=request)
        openid, unionid = userinfo.get('openid'), userinfo.get('unionid')
        if not openid or not unionid:
            openid, unionid = options.get_cookie_openid(request.COOKIES, settings.WXPAY_APPID)

        if openid and not unionid:
            logger.warn('weixin unionid not return:openid=%s' % openid)
            unionid = self.get_unoinid(openid, settings.WXPAY_APPID)

        if not valid_openid(unionid):
            return AnonymousUser()

        try:
            profile = Customer.objects.get(unionid=unionid, status=Customer.NORMAL)
            # 如果openid有误，则重新更新openid
            if unionid:
                task_Refresh_Sale_Customer.delay(userinfo, app_key=settings.WXPAY_APPID)

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

            user, state = User.objects.get_or_create(username=unionid, is_active=True)
            profile, state = Customer.objects.get_or_create(unionid=unionid, openid=openid, user=user)
            # if not normal user ,no login allowed
            if profile.status != Customer.NORMAL:
                return AnonymousUser()
            task_Refresh_Sale_Customer.delay(userinfo, app_key=settings.WXPAY_APPID)

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
        if not (request.path.startswith("/rest/") and content.get('unionid')):
            return None

        openid = content.get('openid')
        unionid = content.get('unionid')
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
                profile.nick = params.get('nickname')
                profile.thumbnail = params.get('headimgurl')
                profile.save()
            # if not normal user ,no login allowed
            if profile.status != Customer.NORMAL:
                return AnonymousUser()

        task_Refresh_Sale_Customer.delay(params, app_key=settings.WXAPP_ID)
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

    def authenticate(self, request, **kwargs):
        """
        1, get django user first;
        2, if not,then get customer user;
        3, if not else,then create django user
        """
        content = request.POST
        mobile = kwargs.get('mobile') or content.get('sms_code')
        sms_code = kwargs.get('sms_code') or content.get('sms_code')
        if not (request.path.startswith("/rest/") and mobile and sms_code):
            return None

        try:
            register = Register.objects.get(vmobile=mobile)
            if not register.is_submitable():
                return AnonymousUser()

            try:
                user = User.objects.get(username=mobile)
            except User.DoesNotExist, err:
                customers = Customer.objects.filter(mobile=mobile)
                if not customers.exists():
                    raise err
                user = customers[0].user

            if not user.is_active:
                user.is_active = True
                user.save()
            # if not normal user ,no login allowed
            customer = Customer.objects.get(user=user)
            if customer.status != Customer.NORMAL:
                return AnonymousUser()

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
