# coding=utf-8
import time, re
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import HttpResponseRedirect
from core.weixin.options import gen_weixin_redirect_url
from django.contrib.auth import authenticate, login, logout

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework import renderers
from rest_framework import exceptions

from flashsale.restpro import options
from core.weixin.options import gen_wxlogin_sha1_sign

import logging
import serializers

logger = logging.getLogger('django.request')

from flashsale.pay.models import Customer, Integral, Register

PHONE_NUM_RE = re.compile(r'^0\d{2,3}\d{7,8}$|^1[34578]\d{9}$|^147\d{8}', re.IGNORECASE)


def in_weixin(request):
    user_agent = request.META.get('HTTP_USER_AGENT')
    if user_agent:
        user_agent = user_agent.lower()
        if user_agent.find('micromessenger') >= 0:
            return True
    return False


def check_sign(request):
    """
    功能：微信app 登录接口数据校验算法:
    参数：params = {'a':1,'c':2,'b':3}
    时间戳：timestamp = 1442995986
    随机字符串：noncestr = 8位随机字符串，如abcdef45
        　 　secret : 3c7b4e3eb5ae4c (测试值)

       签名步骤:
       1，获得所有签名参数：　sign_params = {timestamp:时间戳,noncestr:随机值,secret:密钥值}
        如　{'timestamp':'1442995986','noncestr':'1442995986abcdef','secret':'3c7b4e3eb5ae4c'}
       2,根据参数的字符串key，进行升序排列,并组装成新的字符串，如：
        sign_string = '&'.join(sort([k=v for k,v in sign_params],asc=true))
       如　'noncestr=1442995986abcdef&secret=3c7b4e3eb5ae4c&timestamp=1442995986'
       3,签名算法
        sign = hash.sha1(sign_string).hexdigest()
        如　签名值＝'39ae931c59394c9b4b0973b3902956f63a35c21e'
       4,最后传递给服务器的参数：
       URL:~?noncestr=1442995986abcdef&timestamp=1442995986&sign=366a83819b064149a7f4e9f6c06f1e60eaeb02f7
       POST: 'a=1&b=3&c=2'
    """
    CONTENT = request.GET
    params = {}
    for k, v in CONTENT.iteritems():
        params[k] = v
    timestamp = params.get('timestamp')
    if not timestamp or time.time() - int(timestamp) > 6 * 60 * 60:
        return False
    origin_sign = params.pop('sign')
    new_sign = gen_wxlogin_sha1_sign(params, settings.WXAPP_SECRET)
    if origin_sign and origin_sign == new_sign:
        return True
    params.update({'sign': origin_sign})
    logger.error('%s' % params)
    return False


class LoginViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Register.objects.all()
    serializer_class = serializers.RegisterSerializer
    authentication_classes = ()
    permission_classes = ()

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def weixin_auth_and_redirect(self, request):
        next_url = request.GET.get('next')
        code = request.GET.get('code')

        if not in_weixin(request):
            return HttpResponseRedirect(next_url)

        user = request.user
        if not user or user.is_anonymous():
            return HttpResponseRedirect(next_url)

        if not code:
            params = {'appid': settings.WXPAY_APPID,
                      'redirect_uri': request.build_absolute_uri().split('#')[0],
                      'response_type': 'code',
                      'scope': 'snsapi_base',
                      'state': '135'}
            redirect_url = gen_weixin_redirect_url(params)

        return HttpResponseRedirect(redirect_url)

    @list_route(methods=['post'])
    def customer_login(self, request):
        """验证用户登录"""
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '/index.html')
        if not username or not password:
            return Response({"code": 1, "message": u"用户名和密码不全呢！", 'next': ''})

        customers = Customer.objects.filter(mobile=username).exclude(status=Customer.DELETE)
        if customers.count() == 1:
            # 若是微信授权创建的账户，django user的username不是手机号。
            username = customers[0].user.username

        user = authenticate(username=username, password=password)
        if not user or user.is_anonymous():
            return Response({"code": 2, "message": u"用户名或密码错误呢！", 'next': ''})
        login(request, user)

        if in_weixin(request) and customers.count() == 1 and not customers[0].is_wxauth():
            params = {
                'appid': settings.WXPAY_APPID,
                'response_type': 'code',
                'scope': 'snsapi_base',
                'state': '135',
                'redirect_uri': ('{0}{1}?next={2}').format(settings.M_SITE_URL,
                                                           reverse('rest_v2:xlmm-wxauth'),
                                                           next_url)
            }
            next_url = gen_weixin_redirect_url(params)
        return Response({"code": 0, "message": u"登陆成功", "next": next_url})

    @list_route(methods=['post'])
    def wxapp_login(self, request):
        """
        app客户端微信授权登陆
        """
        if not check_sign(request):
            return Response({"code": 1, "message": u'登陆失败'})

        params = request.POST
        user = authenticate(request=request, **params)
        if not user or user.is_anonymous():
            return Response({"code": 2, "message": u'登陆异常'})

        login(request, user)
        return Response({"code": 0, "message": u'登陆成功'})

    @list_route(methods=['post'])
    def sms_login(self, request, *args, **kwargs):
        """ 短信验证码登陆 """
        req_params = request.POST
        mobile = req_params.get('mobile', '')

        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):
            return Response({"code": 2, "message": u"手机号码有误"})
        sms_code = req_params.get('sms_code', '')
        if not sms_code or not sms_code.isdigit():
            return Response({"code": 3, "message": u"验证码有误"})

        user1 = authenticate(request=request, **req_params)
        if not user1 or user1.is_anonymous():
            return Response({"code": 1, "message": u"登录验证失败"})
        login(request, user1)

        return Response({"code": 0, "message": u'登陆成功'})
