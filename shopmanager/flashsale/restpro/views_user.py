# -*- coding:utf-8 -*-
import os
import re
import urllib
import datetime

from django.shortcuts import get_object_or_404, HttpResponseRedirect
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from django.core.urlresolvers import reverse
from shopapp.weixin.models import WeiXinUser
from django.db import models
from django.contrib.auth import authenticate, login, logout
from flashsale.pay.models import Register, Customer,Integral
from rest_framework import exceptions
from shopback.base import log_action, ADDITION, CHANGE
from . import permissions as perms
from . import serializers
from shopapp.smsmgr.tasks import task_register_code
from django.contrib.auth.models import User as DjangoUser

PHONE_NUM_RE = re.compile(r'^0\d{2,3}\d{7,8}$|^1[34578]\d{9}$|^147\d{8}', re.IGNORECASE)
TIME_LIMIT = 360
DJUSER, DU_STATE = DjangoUser.objects.get_or_create(username='systemoa', is_active=True)


def check_day_limit(reg_bean):
    if reg_bean.code_time and datetime.datetime.now().strftime('%Y-%m-%d') == reg_bean.code_time.strftime('%Y-%m-%d'):
        if reg_bean.verify_count >= 5:
            return True
        else:
            return False
    else:
        if reg_bean.verify_count >= 1:
            reg_bean.verify_count = 0
            reg_bean.save()
        return False


class RegisterViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    特卖平台 用户注册,修改密码API：
    - {prefix}/[.format]: params={vmobile} 注册新用户时，获取验证码;
    - {prefix}/check_code_user: params={username,valid_code,password1,password2} 注册新用户;
    - {prefix}/change_pwd_code: params={vmobile} 修改密码时，获取验证码api;
    - {prefix}/change_user_pwd: params={username,valid_code,password1,password2} 提交修改密码api;
    """
    queryset = Register.objects.all()
    serializer_class = serializers.RegisterSerializer
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def create(self, request, *args, **kwargs):
        """发送验证码时候新建register对象"""
        mobile = request.data['vmobile']
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):  # 进行正则判断
            raise exceptions.APIException(u'手机号码有误')
        reg = Register.objects.filter(vmobile=mobile)
        already_exist = Customer.objects.filter(mobile=mobile)
        if already_exist.count() > 0:
            return Response({"result": "0"})  # 已经有用户了
        if reg.count() > 0:
            temp_reg = reg[0]
            reg_pass = reg.filter(mobile_pass=True)
            if reg_pass.count() > 0:
                return Response({"result": "0"})  # 已经注册过
            if check_day_limit(temp_reg):
                return Response({"result": "2"})  #当日验证次数超过5
            if temp_reg.code_time and temp_reg.code_time > last_send_time:
                return Response({"result": "1"})  # 180s内已经发送过
            else:
                temp_reg.verify_code = temp_reg.genValidCode()
                temp_reg.code_time = current_time
                temp_reg.save()
                log_action(DJUSER.id, temp_reg, CHANGE, u'修改，注册手机验证码')
                task_register_code.s(mobile, "1")()
                return Response({"result": "OK"})

        new_reg = Register(vmobile=mobile)
        new_reg.verify_code = new_reg.genValidCode()
        new_reg.verify_count = 0
        new_reg.code_time = current_time
        new_reg.save()
        log_action(DJUSER.id, new_reg, ADDITION, u'新建，注册手机验证码')
        task_register_code.s(mobile, "1")()
        return Response({"result": "OK"})

    def list(self, request, *args, **kwargs):
        return Response("not open")

    @list_route(methods=['post'])
    def check_code_user(self, request):
        """验证码判断、验证码过时功能、新建用户"""
        post = request.POST
        mobile = post['username']
        client_valid_code = post.get('valid_code', 0)
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        reg = Register.objects.filter(vmobile=mobile)
        reg_pass = reg.filter(mobile_pass=True)
        already_exist = Customer.objects.filter(mobile=mobile)
        if already_exist.count() > 0:
            return Response({"result": "0"})  # 已经有用户了
        if reg.count() == 0:
            return Response({"result": "3"})  # 未获取验证码
        elif reg_pass.count() > 0:
            return Response({"result": "0"})  # 已经注册过
        reg_temp = reg[0]
        server_verify_code = reg_temp.verify_code
        reg_temp.submit_count += 1     #提交次数加一
        reg_temp.save()
        if (reg_temp.code_time and reg_temp.code_time < last_send_time) or server_verify_code != client_valid_code:
            return Response({"result": "1"})  # 验证码过期或者不对
        form = UserCreationForm(post)
        if form.is_valid():
            new_user = form.save()
            a = Customer()
            a.user = new_user
            a.mobile = mobile
            a.save()
            reg_temp.mobile_pass = True
            reg_temp.cus_uid = a.id

            reg_temp.save()
            return Response({"result": "7"})  # 注册成功
        else:
            return Response({"result": "2"})  # 表单填写有误


    @list_route(methods=['post'])
    def change_pwd_code(self, request):
        """忘记密码时获取验证码"""
        mobile = request.data['vmobile']
        already_exist = Customer.objects.filter(mobile=mobile)
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        if already_exist.count() == 0:
            return Response({"result": "1"})  # 尚无用户或者手机未绑定
        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):  # 进行正则判断
            return Response({"result": "false"})
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            new_reg = Register(vmobile=mobile)
            new_reg.verify_code = new_reg.genValidCode()
            new_reg.verify_count = 0
            new_reg.mobile_pass = True
            new_reg.code_time = current_time
            new_reg.save()
            log_action(DJUSER.id, new_reg, ADDITION, u'新建，忘记密码验证码')
            task_register_code.s(mobile, "2")()
            return Response({"result": "0"})
        else:
            reg_temp = reg[0]
            if check_day_limit(reg_temp):
                return Response({"result": "2"})  #当日验证次数超过5
            if reg_temp.code_time and reg_temp.code_time > last_send_time:
                return Response({"result": "3"})  # 180s内已经发送过
            reg_temp.verify_code = reg_temp.genValidCode()
            reg_temp.code_time = current_time
            reg_temp.save()
            log_action(DJUSER.id, reg_temp, CHANGE, u'修改，忘记密码验证码')
            task_register_code.s(mobile, "2")()
        return Response({"result": "0"})

    @list_route(methods=['post'])
    def change_user_pwd(self, request):
        """提交修改密码"""
        mobile = request.data['username']
        passwd1 = request.data['password1']
        passwd2 = request.data['password2']
        verify_code = request.data['valid_code']
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)

        if not mobile or not passwd1 or not passwd2 or not verify_code or len(mobile) == 0 \
                or len(passwd1) == 0 or len(verify_code) == 0 or passwd2 != passwd1:
            return Response({"result": "2"})
        already_exist = Customer.objects.filter(mobile=mobile)
        if already_exist.count() == 0:
            return Response({"result": "1"})  # 尚无用户或者手机未绑定
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            return Response({"result": "3"})  # 未获取验证码
        reg_temp = reg[0]
        verify_code_server = reg_temp.verify_code
        reg_temp.submit_count += 1     #提交次数加一
        reg_temp.save()
        if reg_temp.code_time and reg_temp.code_time < last_send_time:
            return Response({"result": "4"})
        if verify_code_server != verify_code:
            return Response({"result": "3"})  # 验证码不对
        try:
            system_user = already_exist[0].user
            system_user.set_password(passwd1)
            system_user.save()
            reg_temp.cus_uid = already_exist[0].id
            reg_temp.save()
            log_action(DJUSER.id, already_exist[0], CHANGE, u'忘记密码，修改成功')
            log_action(DJUSER.id, reg_temp, CHANGE, u'忘记密码，修改成功')
        except:
            return Response({"result": "5"})
        return Response({"result": "0"})

    @list_route(methods=['post'])
    def customer_login(self, request):
        """验证用户登录"""
        # 获取用户名和密码
        # 判断网址的结尾是不是登录请求网址(ajax url请求)
        if not request.path.endswith("customer_login"):
            return Response({"result": "fail"})
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next','/index.html')
        if not username or not password:
            return Response({"result": "null"})
        try:
            customers = Customer.objects.filter(models.Q(email=username) | models.Q(mobile=username),status=Customer.NORMAL)
            if customers.count() > 0:
                username = customers[0].user.username
            user1 = authenticate(username=username, password=password)
            if not user1 or user1.is_anonymous():
                return Response({"result": "u_error"})  # 密码错误
            login(request, user1)
            
            user_agent = request.META.get('HTTP_USER_AGENT')
            if not user_agent or user_agent.find('MicroMessenger') < 0:
                return Response({"result": "login", "next": next_url})   #登录不是来自微信，直接返回登录成功
             
            customers = Customer.objects.filter(user=user1)
            if customers.count() == 0 or customers[0].is_wxauth():
                return Response({"result": "login", "next": next_url})  #如果是系统帐号登录，或已经微信授权过，则直接返回登录成功
            
            params = {'appid':settings.WXPAY_APPID,
              'redirect_uri':('{0}{1}?next={2}').format(settings.M_SITE_URL,reverse('v1:xlmm-wxauth'),next_url),
              'response_type':'code',
              'scope':'snsapi_base',
              'state':'135'}
            redirect_url = ('{0}?{1}').format(settings.WEIXIN_AUTHORIZE_URL,urllib.urlencode(params))
            return Response({"result": "login", "next": redirect_url})  #如果用户没有微信授权则直接微信授权后跳转
            
        except Customer.DoesNotExist:
            return Response({"result": "u_error"})  # # 用户错误
        except Customer.MultipleObjectsReturned:
            return Response({"result": "s_error"})  # 账户异常
        except ValueError, exc:
            return Response({"result": "no_pwd"})
        return Response({"result": "fail"})


class CustomerViewSet(viewsets.ModelViewSet):
    """
    特卖平台 用户操作API：
    - {prefix}/customer_logout:用户注销api;
    """
    queryset = Customer.objects.all()
    serializer_class = serializers.CustomerSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        if request.user.is_anonymous():
            return self.queryset.none()
        return self.queryset.filter(user=request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @list_route(methods=['get'])
    def profile(self,request, *args, **kwargs):
        customer = get_object_or_404(Customer,user=request.user)
        serializer = self.get_serializer(customer)
        user_info  = serializer.data
        user_scores = Integral.objects.filter(integral_user=customer.id)
        user_score = 0
        if user_scores.count() > 0:
            user_score = user_scores[0].integral_value
        user_info['score'] = user_score
        return Response(user_info)

    def perform_destroy(self, instance):
        instance.status = Customer.DELETE
        instance.save()
    
    @list_route(methods=['post'])
    def customer_logout(self, request, *args, **kwargs):
        logout(request)
        return Response({"result": 'logout'})
    
    @list_route(methods=['get'])
    def islogin(self,request, *args, **kwargs):
        return Response({'result': 'login'})

    @list_route(methods=['get'])
    def need_set_info(self, request):
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        has_set_passwd = True
        try:
            user = customer.user
            authenticate(username=user.username, password=u"testxiaolummpasswd")
            # authenticate(username="testxiaolu", password=u"testxiaolummpasswd")
        except ValueError, exc:
            has_set_passwd = False

        if customer.mobile and len(customer.mobile) == 11:
            if has_set_passwd:
                return Response({'result': 'no', 'mobile': customer.mobile})
            else:
                return Response({'result': '1', 'mobile': customer.mobile})
        else:
            return Response({'result': 'yes'})


    @list_route(methods=['post'])
    def bang_mobile_code(self, request):
        """绑定手机时获取验证码"""
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        if len(customer.mobile) != 0:
            raise exceptions.APIException(u'账户异常，请联系客服～')
        mobile = request.data['vmobile']
        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):  # 进行正则判断
            return Response({"result": "false"})
        already_exist = Customer.objects.filter(mobile=mobile)
        if already_exist.count() > 0:
            return Response({"result": "1"})  # 手机已经绑定

        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            new_reg = Register(vmobile=mobile)
            new_reg.verify_code = new_reg.genValidCode()
            new_reg.verify_count = 0
            new_reg.code_time = current_time
            new_reg.save()
            log_action(request.user.id, new_reg, ADDITION, u'新建，绑定手机验证码')
            task_register_code.s(mobile, "3")()
            return Response({"result": "0"})
        else:
            reg_temp = reg[0]
            if check_day_limit(reg_temp):
                return Response({"result": "2"})  #当日验证次数超过5
            if reg_temp.code_time and reg_temp.code_time > last_send_time:
                return Response({"result": "3"})  # 180s内已经发送过
            reg_temp.verify_code = reg_temp.genValidCode()
            reg_temp.code_time = current_time
            reg_temp.save()
            log_action(request.user.id, reg_temp, CHANGE, u'绑定手机获取验证码')
            task_register_code.s(mobile, "3")()
        return Response({"result": "0"})

    @list_route(methods=['post'])
    def bang_mobile(self, request):
        """绑定手机,并初始化密码"""
        mobile = request.data['username']
        passwd1 = request.data['password1']
        passwd2 = request.data['password2']
        verify_code = request.data['valid_code']
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        if not mobile or not passwd1 or not passwd2 or not verify_code or len(mobile) == 0 \
                or len(passwd1) == 0 or len(verify_code) == 0 or passwd2 != passwd1:
            return Response({"result": "2"})
        print not re.match(PHONE_NUM_RE, mobile),re.match(PHONE_NUM_RE, mobile)
        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):  # 进行正则判断，待写
            return Response({"result": "2"})
        already_exist = Customer.objects.filter(mobile=mobile)
        if already_exist.count() > 0:
            return Response({"result": "1"})  # 手机已经绑定
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        if len(customer.mobile) != 0:
            raise exceptions.APIException(u'账户异常，请联系客服～')
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            return Response({"result": "3"})  # 验证码不对
        reg_temp = reg[0]
        reg_temp.submit_count += 1     #提交次数加一
        reg_temp.save()
        if reg_temp.code_time and reg_temp.code_time < last_send_time:
            log_action(request.user.id, reg_temp, CHANGE, u'验证码过期')
            return Response({"result": "4"}) #验证码过期
        verify_code_server = reg_temp.verify_code
        if verify_code_server != verify_code:
            log_action(request.user.id, reg_temp, CHANGE, u'验证码不对')
            return Response({"result": "3"})  # 验证码不对
        try:
            customer.mobile = mobile
            customer.save()
            log_action(request.user.id, customer, CHANGE, u'手机绑定成功')
            reg_temp.cus_uid = customer.id
            reg_temp.mobile_pass = True
            reg_temp.save()
            log_action(request.user.id, reg_temp, CHANGE, u'手机绑定成功')
            system_user = customer.user
            system_user.set_password(passwd1)
            system_user.save()
        except:
            return Response({"result": "5"})
        return Response({"result": "0"})

    @list_route(methods=['post'])
    def passwd_set(self, request):
        """绑定手机,并初始化密码"""
        passwd1 = request.data['password1']
        passwd2 = request.data['password2']
        if not passwd1 and not passwd2 and len(passwd1) < 6 and len(passwd2) < 6 and passwd2 != passwd1:
            return Response({"result": "1"})
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        log_action(request.user.id, customer, CHANGE, u'第一次设置密码成功')
        django_user.set_password(passwd1)
        django_user.save()
        return Response({"result": "0"})

    @list_route(methods=['post'])
    def change_pwd_code(self, request):
        """修改密码时获取验证码"""
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        if customer.mobile == "" or not re.match(PHONE_NUM_RE, customer.mobile):  # 进行正则判断，待写
            return Response({"result": "false"})
        reg = Register.objects.filter(vmobile=customer.mobile)
        if reg.count() == 0:
            new_reg = Register(vmobile=customer.mobile)
            new_reg.verify_code = new_reg.genValidCode()
            new_reg.verify_count = 0
            new_reg.mobile_pass = True
            new_reg.code_time = current_time
            new_reg.save()
            log_action(request.user.id, new_reg, ADDITION, u'登录后，新建，修改密码')
            task_register_code.s(customer.mobile, "2")()
            return Response({"result": "0"})
        else:
            reg_temp = reg[0]
            if check_day_limit(reg_temp):
                return Response({"result": "2"})  #当日验证次数超过5
            if reg_temp.code_time and reg_temp.code_time > last_send_time:
                return Response({"result": "3"})  # 180s内已经发送过
            reg_temp.verify_code = reg_temp.genValidCode()
            reg_temp.code_time = current_time
            reg_temp.save()
            log_action(request.user.id, reg_temp, ADDITION, u'登录后，修改密码')
            task_register_code.s(customer.mobile, "2")()
        return Response({"result": "0"})

    @list_route(methods=['post'])
    def change_user_pwd(self, request):
        """提交修改密码"""
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        mobile = request.data['username']
        passwd1 = request.data['password1']
        passwd2 = request.data['password2']
        verify_code = request.data['valid_code']

        if not mobile or not passwd1 or not passwd2 or not verify_code or len(mobile) == 0 \
                or len(passwd1) == 0 or len(verify_code) == 0 or passwd2 != passwd1:
            return Response({"result": "2"})
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        if customer.mobile != mobile:
            raise exceptions.APIException(u'手机参数出错')
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            return Response({"result": "3"})  # 验证码不对
        reg_temp = reg[0]
        reg_temp.submit_count += 1     #提交次数加一
        reg_temp.cus_uid = customer.id
        reg_temp.save()
        log_action(request.user.id, reg_temp, CHANGE, u'修改密码')
        if reg_temp.code_time and reg_temp.code_time < last_send_time:
            return Response({"result": "4"}) #验证码过期

        verify_code_server = reg_temp.verify_code
        if verify_code_server != verify_code:
            return Response({"result": "3"})  # 验证码不对
        try:
            system_user = customer.user
            system_user.set_password(passwd1)
            system_user.save()
            log_action(request.user.id, customer, CHANGE, u'修改密码')
        except:
            return Response({"result": "5"})
        return Response({"result": "0"})
