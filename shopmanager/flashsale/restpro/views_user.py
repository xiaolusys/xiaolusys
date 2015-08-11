# -*- coding:utf-8 -*-
import datetime
from django.shortcuts import get_object_or_404, HttpResponseRedirect
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.forms import UserCreationForm
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

from . import permissions as perms
from . import serializers
from shopapp.smsmgr.tasks import task_register_code


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
        last_send_time = current_time - datetime.timedelta(seconds=60)
        if mobile == "":  # 进行正则判断，待写
            return Response({"result": "false"})
        reg = Register.objects.filter(vmobile=mobile)
        already_exist = Customer.objects.filter(mobile=mobile)
        if already_exist.count() > 0:
            return Response({"result": "0"})  # 已经有用户了
        if reg.count() > 0:
            temp_reg = reg[0]
            reg_pass = reg.filter(mobile_pass=True)
            if reg_pass.count() > 0:
                return Response({"result": "0"})  # 已经注册过
            if temp_reg.modified > last_send_time:
                return Response({"result": "1"})  # 60s内已经发送过
            else:
                temp_reg.verify_code = temp_reg.genValidCode()
                temp_reg.verify_count += 1
                temp_reg.save()
                task_register_code.s(mobile)()
                return Response({"result": "OK"})

        new_reg = Register(vmobile=mobile)
        new_reg.verify_code = new_reg.genValidCode()
        new_reg.verify_count = 1
        new_reg.save()
        task_register_code.s(mobile)()
        return Response({"result": "OK"})

    def list(self, request, *args, **kwargs):

        return Response("not open")

    @list_route(methods=['post'])
    def check_code_user(self, request):
        """验证码判断、验证码过时功能（未写）、新建用户"""
        post = request.POST
        mobile = post['username']
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
        verify_code = reg_temp.verify_code
        if verify_code != post.get('valid_code', 0):
            return Response({"result": "1"})  # 验证码不对
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

    # from django.contrib.auth.views import password_change
    @list_route(methods=['post'])
    def change_pwd_code(self, request):
        """修改密码时获取验证码"""
        mobile = request.data['vmobile']
        already_exist = Customer.objects.filter(mobile=mobile)
        if already_exist.count() == 0:
            return Response("1")  # 尚无用户或者手机未绑定
        if mobile == "":  # 进行正则判断，待写
            return Response("false")
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            new_reg = Register(vmobile=mobile)
            new_reg.verify_code = new_reg.genValidCode()
            new_reg.verify_count = 1
            new_reg.mobile_pass = True
            new_reg.save()
            task_register_code.s(mobile)()
            return Response('0')
        else:
            reg_temp = reg[0]
            reg_temp.verify_code = reg_temp.genValidCode()
            reg_temp.save()
            task_register_code.s(mobile)()
        return Response("0")

    @list_route(methods=['post'])
    def change_user_pwd(self, request):
        """提交修改密码"""
        mobile = request.data['username']
        passwd1 = request.data['password1']
        passwd2 = request.data['password2']
        verify_code = request.data['valid_code']

        if not mobile and not passwd1 and not passwd2 and not verify_code and len(mobile) == 0 and len(
                passwd1) == 0 and len(
                passwd2) and len(verify_code) == 0 and passwd2 != passwd1:
            return Response('2')
        already_exist = Customer.objects.filter(mobile=mobile)
        if already_exist.count() == 0:
            return Response("1")  # 尚无用户或者手机未绑定
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            return Response("3")  # 验证码不对
        reg_temp = reg[0]
        verify_code_server = reg_temp.verify_code
        if verify_code_server != verify_code:
            return Response("3")  # 验证码不对
        try:
            system_user = already_exist[0].user
            system_user.set_password(passwd1)
            system_user.save()
        except:
            return Response("5")
        return Response("0")

    @list_route(methods=['post'])
    def customer_login(self, request):
        """验证用户登录"""
        # 获取用户名和密码
        # 判断网址的结尾是不是登录请求网址(ajax url请求)
        if not request.path.endswith("customer_login"):
            return None
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            return Response({"result": "null"})
        try:
            customer = Customer.objects.get(models.Q(email=username) | models.Q(mobile=username))
            user = customer.user
            user1 = authenticate(username=user.username, password=password)
            if user1 is not None:
                login(request, user1)
                return Response({"result": "login"})   # 登录成功
            if not user.check_password(password):
                return Response({"result": "p_error"})  # 密码错误
        except Customer.DoesNotExist:
            return Response({"result": "u_error"})  # # 用户错误
        except Customer.MultipleObjectsReturned:
            return Response({"result": "s_error"})  # 账户异常
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
        return Response({'result':'login'})

