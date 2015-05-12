#-*- encoding:utf8 -*-

from django.db import models
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User,AnonymousUser
from django.contrib.auth.backends import RemoteUserBackend
from django.core.urlresolvers import reverse

from .models import Customer
from .options import get_user_unionid
from shopapp.weixin.views import valid_openid
from shopapp.weixin.models import WeiXinUser

import logging
logger = logging.getLogger('django.request')


class FlashSaleBackend(RemoteUserBackend):
    
    create_unknown_user = False
    upports_inactive_user = False
    supports_object_permissions = False

    def authenticate(self, request, **kwargs):
        
        if not request.path.endswith(reverse('flashsale_login')):
            return None
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            customer = Customer.objects.get(models.Q(email=username)|models.Q(mobile=username))
            user = customer.user 
            
            if not user.check_password(password):
                messages.add_message(request, messages.ERROR, u'用户名或密码错误')
                return AnonymousUser()
        except Customer.DoesNotExist:
            messages.add_message(request, messages.ERROR, u'用户名或密码错误')
            return AnonymousUser()
            
        try:
            wxuser = WeiXinUser.objects.get(mobile=username)
            customer.nick   = wxuser.nickname
            customer.save()
        except:
            pass 

        return user
    

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None
        

class WeixinPubBackend(RemoteUserBackend):
    
    create_unknown_user = True
    upports_inactive_user = False
    supports_object_permissions = False

    def authenticate(self, request, **kwargs):
        
        if not request.path.startswith("/mm/"):
            return None
        
        code = request.GET.get('code')
        openid,unionid = get_user_unionid(code,appid=settings.WXPAY_APPID,secret=settings.WXPAY_SECRET)
        
        if not valid_openid(openid) or not valid_openid(unionid):
            return AnonymousUser()
        
        try:
            logger.error(' auth openid: %s,unionid: %s'%(openid,unionid))
            profile = Customer.objects.get(openid=openid,unionid=unionid)
            if profile.user:
                if not profile.user.is_active:
                    profile.user.is_active = True
                    profile.user.save()
                return profile.user
            else:
                user,state = User.objects.get_or_create(username=unionid,is_active=True)
                profile.user = user
                profile.save()
            
        except Customer.DoesNotExist:
            if not self.create_unknown_user:
                return AnonymousUser()
            logger.error('anoymous openid: %s,unionid: %s'%(openid,unionid))
            user,state = User.objects.get_or_create(username=unionid,is_active=True)
            profile,state = Customer.objects.get_or_create(openid=openid,unionid=unionid,user=user)
            
        try:
            wxuser = WeiXinUser.objects.get(models.Q(openid=openid)|models.Q(unionid=unionid))
            profile.nick   = wxuser.nickname
            profile.mobile = wxuser.mobile
            profile.save()
        except:
            pass 
        
        return user
    

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None
  
