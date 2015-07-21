#-*- coding:utf-8 -*-
import datetime
from django.shortcuts import get_object_or_404, HttpResponseRedirect
from django.contrib.auth.models import  User
from django.contrib.auth.forms import UserCreationForm
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status

from flashsale.pay.models import Register,Customer

from . import permissions as perms
from . import serializers 
from shopapp.smsmgr.tasks import task_register_code

class RegisterViewSet(mixins.CreateModelMixin,mixins.ListModelMixin,viewsets.GenericViewSet):
    """
    特卖平台 用户注册API：
    
    """
    queryset = Register.objects.all()
    serializer_class = serializers.RegisterSerializer
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)

    def create(self, request, *args, **kwargs):
        """发送验证码时候新建register对象"""
        mobile = request.data['vmobile']
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=60)
        if mobile == "": #进行正则判断，待写
            return Response("false")
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() > 0:
            temp_reg = reg[0]
            reg_pass = reg.filter(mobile_pass=True)
            if reg_pass.count() > 0:
                return Response("0") #已经注册过
            if temp_reg.modified > last_send_time:
                return Response("1")#60s内已经发送过
            else:
                temp_reg.verify_code = temp_reg.genValidCode()
                temp_reg.verify_count += 1
                temp_reg.save()
                task_register_code.s(request.data['vmobile'])()
                return Response("OK")

        new_reg = Register(vmobile=mobile)
        new_reg.verify_code = new_reg.genValidCode()
        new_reg.verify_count = 1
        new_reg.save()
        task_register_code.s(request.data['vmobile'])()
        return Response("OK")
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['post'])
    def check_code_user(self, request):
        """验证码判断、验证码过时功能（未写）、新建用户"""
        post = request.POST
        mobile = post['username']

        reg = Register.objects.filter(vmobile=mobile)
        reg_pass = reg.filter(mobile_pass=True)
        if reg.count() == 0:
            return Response("无验证码")
        elif reg_pass.count() > 0:
            return Response("0")#已经注册过
        reg_temp = reg[0]
        verify_code = reg_temp.verify_code
        if verify_code != post.get('valid_code', 0):
            return Response("验证码不对")
        form = UserCreationForm(post)
        if form.is_valid():
            new_user = form.save()
            a = Customer()
            a.user = new_user
            a.mobile = mobile
            a.save()
            reg_temp.mobile_pass = True
            reg_temp.save()
            return HttpResponseRedirect("/mm/plist")
        else:
            return Response("error")

class CustomerViewSet(viewsets.ModelViewSet):
    """
    特卖平台 用户操作API：
    
    """
    queryset = Customer.objects.all()
    serializer_class = serializers.CustomerSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
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
    
    def perform_destroy(self,instance):
        instance.status = Customer.DELETE
        instance.save()
    
    
    
    

