# encoding=utf8
import hashlib

from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from rest_framework import authentication
from rest_framework import exceptions
from django.core.cache import cache

from flashsale.pay.models.user import Customer


class WeAppAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.GET.get('x-token') or request.POST.get('x-token')
        if not token:
            return None

        try:
            session = cache.get(token)
            openid = session['openid']
            unionid = session['unionid']

            customer = Customer.objects.get(unionid=unionid)
            user = customer.user
        except Exception:
            raise exceptions.AuthenticationFailed('No such user')

        return (user, None)


def generate_app_key():
    """
    生成 APP_ID 和 APP_SECRET

    return:
    (app_id, app_secret)
    """
    import os
    app_id = os.urandom(9).encode('hex')
    app_secret = os.urandom(16).encode('hex')
    return (app_id, app_secret)


def md5_sign(data, secret):
    """
    签名

    params:
    - data (string)
    - secret (string) 密钥 APP_SECRET
    """
    return hashlib.md5(data.encode('utf8')+secret).hexdigest().upper()


def check_md5_sign(data, sign, secret):
    """
    检测签名是否正确

    params:
    - data (string) 数据
    - sign (string) 需要检测的签名
    - secret (string) APP_SECRET

    return:
    - True 正确
    - False 错误
    """
    return md5_sign(data, secret) == sign


def group_required(groups):
    def decorator(func):
        def wrapper(req, *args, **kwargs):
            user = req.user
            in_group = user.groups.filter(id__in=groups).first()
            if in_group or user.is_superuser:
                return func(req, *args, **kwargs)
            return HttpResponseForbidden()
        return wrapper
    return decorator


def perm_required(perm):
    """
    *类方法装饰器*
    """
    def decorator(func):
        def wrapper(obj, req, *args, **kwargs):
            user = req.user
            if user.has_perm(perm):
                return func(obj, req, *args, **kwargs)
            else:
                return HttpResponseForbidden()
        return wrapper
    return decorator


