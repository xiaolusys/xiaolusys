# -*- coding:utf-8 -*-
import os
import re
import urllib
import time
import datetime
from urlparse import urlparse

from django.conf import settings
from django.http.request import validate_host
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from flashsale.pay.models import Register, Customer, Integral
from shopapp.smsmgr.tasks import task_register_code
from django.contrib.auth.models import User as DjangoUser
import logging

logger = logging.getLogger('django.request')

PHONE_NUM_RE = re.compile(r'^0\d{2,3}\d{7,8}$|^1[34578]\d{9}$|^147\d{8}', re.IGNORECASE)
TIME_LIMIT = 360
RESEND_TIME_LIMIT = 180
SYSTEMOA_ID = 641
MAX_DAY_LIMIT = 5


def check_day_limit(reg):
    """
    whether or not the day_limit is reached.
    """
    if reg.code_time:
        date1 = datetime.datetime.now().date()
        date2 = reg.code_time.date()
        if date1 == date2:
            if reg.verify_count > MAX_DAY_LIMIT:
                return True
        else:
            reg.verify_count = 0
            reg.save()
    return False


def get_register(mobile):
    """
    get register record by mobile, create one if not exists.
    """
    regs = Register.objects.filter(vmobile=mobile)
    if regs.count() > 0:
        return regs[0]
    return Register(vmobile=mobile)


def validate_code(mobile, verify_code):
    """
    Only indicate whether or not verify_code is valid.
    """
    current_time = datetime.datetime.now()
    earliest_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
    regs = Register.objects.filter(vmobile=mobile)

    if regs.count() <= 0:
        return False

    reg = regs[0]
    if not reg.code_time:
        return False
    if not reg.verify_code:
        return False

    reg.submit_count += 1  # 提交次数加一
    reg.save()

    if reg.code > earliest_send_time and reg.verify_code == verify_code:
        return True

    return False


def get_customer(request, mobile):
    """
    1) get customer by authenticated user (if logged in);
    2) get customer by mobile if otherwise.
    """
    user = request.user
    if user and user.is_authenticated():
        customers = Customer.objects.filter(user=user).exclude(status=Customer.DELETE)
    else:
        customers = Customer.objects.filter(mobile=mobile).exclude(status=Customer.DELETE)
    if customers.count() > 0:
        return customers[0]
    return None


def validate_mobile(mobile):
    """
    check mobile format
    """
    if re.match(PHONE_NUM_RE, mobile):  # 进行正则判断
        return True
    return False


def customer_exists(mobile):
    """
    check customer existance by mobile.
    """
    customers = Customer.objects.filter(mobile=mobile).exclude(status=Customer.DELETE)
    if customers.count() > 0:
        return True
    return False


def should_resend_code(reg):
    """
    whether or not the system should resend code
    """
    if reg.verify_count <= 0:
        return True

    current_time = datetime.datetime.now()
    earliest_send_time = current_time - datetime.timedelta(seconds=RESEND_TIME_LIMIT)
    if reg.code_time and reg.code_time > earliest_send_time:
        return True
    return False


class VerifyCodeViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    处理所有和验证码相关的请求，暂有5类：
    register，sms_login, find_pwd, change_pwd, bind.
    """

    def valid_send_request(self, request):
        if not settings.DEPLOY_ENV:
            return True
        user_agent = (request.META.get('HTTP_USER_AGENT') or '').lower()
        http_referer = (request.META.get('HTTP_REFERER') or '').lower()
        if not user_agent or user_agent.lower().find('windows') > 0:
            return False
        if (user_agent.find('xlmm') < 0 and user_agent.find('micromessenger') < 0 ):
            return False
        domain = http_referer and urlparse(http_referer).hostname
        if domain and not validate_host(domain, settings.ALLOWED_HOSTS):
            return False
        return True

    @list_route(methods=['post'])
    def send_code(self, request):
        """
        send code under 5 action cases:
        register, find_pwd, change_pwd, bind, sms_login
        """
        content = request.data
        mobile = content["mobile"]
        action = content["action"]

        if not validate_mobile(mobile):
            return Response({"rcode": 1, "msg": u"亲，手机号码错啦！"})

        valid_request = self.valid_send_request(request)
        if not valid_request:
            import random
            rnum = random.randint(1, 10)
            if rnum % 2 == 1:
                return Response({"rcode": 0, "msg": u"手机已注册"})
            else:
                return Response({"rcode": 0, "msg": u"验证码已发送"})

        customer = get_customer(request, mobile)
        if customer:
            if action == 'register':
                return Response({"rcode": 2, "msg": u"该用户已经存在啦！"})
        else:
            if action == 'find_pwd' or action == 'change_pwd' or action == 'bind':
                return Response({"rcode": 3, "msg": u"该用户还不存在呢！"})

        reg = get_register(mobile)
        if check_day_limit(reg):
            return Response({"rcode": 4, "msg": u"当日验证次数超过限制!"})

        if should_resend_code(reg):
            return Response({"rcode": 5, "msg": u"验证码刚发过咯，请等待下哦！"})

        reg.verify_code = reg.genValidCode()
        reg.code_time = datetime.datetime.now()
        reg.save()
        task_register_code.delay(mobile, "3")
        return Response({"rcode": 0, "msg": u"验证码已发送！"})

    @list_route(methods=['post'])
    def verify_code(self, request):
        """
        verify code under 5 action cases:
        register, find_pwd, change_pwd, bind, sms_login
        """

        content = {}
        for k,v in request.POST.iteritems():
            content[k] = v

        mobile = content["mobile"]
        action = content["action"]
        verify_code = content["verify_code"]

        if not validate_mobile(mobile):
            return Response({"rcode": 1, "msg": u"亲，手机号码错啦！"})

        customer = get_customer(request, mobile)
        if customer:
            if action == 'register':
                return Response({"rcode": 2, "msg": u"该用户已经存在啦！"})  # 已经有用户了
        else:
            if action == 'find_pwd' or action == 'change_pwd' or action == 'bind':
                return Response({"rcode": 3, "msg": u"该用户还不存在呢！"})

        if not validate_code(mobile, verify_code):
            return Response({"rcode": 4, "msg": u"验证码不对或过期啦！"})  # 验证码过期或者不对

        if not customer:
            django_user, state = DjangoUser.objects.get_or_create(username=mobile, is_active=True)
            customer, state = Customer.objects.get_or_create(user=django_user)

        customer.mobile = mobile
        customer.save()

        if action == 'register' or action == 'msm_login':
            req_params = content

            # force to use SMSLoginBackend for authentication
            req_params['sms_code'] = verify_code

            user = authenticate(request=request, **req_params)
            login(request, user)

        ### we need to wrap up user information and send back to app client
        ### xiuqing todo!
        return Response({"rcode": 0, "msg": u"验证码校验通过！"})  # 验证码过期或者不对

    @list_route(methods=['post'])
    def reset_password(self, request):
        """
        reset password after verifying code
        """
        content = request.data
        mobile = content["mobile"]
        pwd1 = content["password1"]
        pwd2 = content["password2"]
        verify_code = content["verify_code"]

        if not validate_mobile(mobile):
            return Response({"rcode": 1, "msg": u"亲，手机号码错啦！"})

        if not mobile or not pwd1 or not pwd2 or not verify_code or pwd1 != pwd2:
            return Response({"rcode": 2, "msg": u"提交的参数有误呀！"})

        customer = get_customer(request, mobile)
        if not customer:
            return Response({"rcode": 3, "msg": u"该用户还不存在呢！"})

        if not validate_code(mobile, verify_code):
            return Response({"rcode": 4, "msg": u"验证码不对或过期啦！"})  # 验证码过期或者不对

        django_user = customer.user
        django_user.set_password(pwd1)
        django_user.save()

        return Response({"rcode": 0, "msg": u"密码设置成功啦！"})
