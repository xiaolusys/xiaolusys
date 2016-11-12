# coding=utf-8
from django.conf import settings
from django.contrib.auth.models import User,AnonymousUser

from core.weixin import options
from core.weixin import constants

import logging
logger = logging.getLogger('xiaolumm.core.weixin')

class WeixinPubBackend(object):
    """ 微信公众号授权登陆 """
    create_unknown_user = True
    supports_inactive_user = False
    supports_object_permissions = False

    def get_unoinid(self, openid, appkey):
        from shopapp.weixin.models import WeixinUnionID
        try:
            return WeixinUnionID.objects.get(openid=openid,app_key=appkey).unionid
        except WeixinUnionID.DoesNotExist:
            return ''

    def authenticate(self, request, auth_classes=[], **kwargs):
        logger.debug('WeixinPubBackend:%s,%s'%(auth_classes, kwargs))
        content = request.POST
        if constants.WEIXIN_AUTHENTICATE_KEY not in auth_classes:
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
            logger.warn('weixin unionid not return:openid=%s'%openid)
            unionid = self.get_unoinid(openid,settings.WXPAY_APPID)

        if not options.valid_openid(unionid):
            return AnonymousUser()

        from flashsale.pay.models import Customer
        from flashsale.pay.tasks import task_Refresh_Sale_Customer
        try:
            profile = Customer.objects.get(unionid=unionid,status=Customer.NORMAL)
            #如果openid有误，则重新更新openid
            if unionid :
                task_Refresh_Sale_Customer.delay(userinfo, app_key=settings.WXPAY_APPID)

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
            if not self.create_unknown_user or not unionid:
                return AnonymousUser()

            user,state = User.objects.get_or_create(username=unionid,is_active=True)
            Customer.objects.get_or_create(unionid=unionid,openid=openid,user=user)
            task_Refresh_Sale_Customer.delay(userinfo, app_key=settings.WXPAY_APPID)

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None