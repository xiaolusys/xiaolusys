#-*- coding:utf8 -*-
import datetime
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from .views_refund import refund_Handler

from flashsale.pay.models import SaleTrade,Customer

from . import permissions as perms
from . import serializers 

from flashsale.pay.models import SaleRefund,District,UserAddress

class SaleRefundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = SaleRefund.objects.all()
    serializer_class = serializers.SaleRefundSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def get_owner_queryset(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        return self.queryset.filter(buyer_id=customer.id)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
            创建退款单 根据退款状态的不同 创建不同的状态的退款/退款单
        """
        res = refund_Handler(request)
        return Response(data=res)


class UserAddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be   viewed or edited.
    author： kaineng .fang  2015-8--
    方法及其目的
    detail  （）：获得用户所有收获地址
    delete（）：删除某个地址
    change_default：选择收获地址
    create_address：创建新的收获地址
    """
    queryset = UserAddress.normal_objects.order_by('-default')
    serializer_class = serializers.UserAddressSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def get_owner_queryset(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        return self.queryset.filter(cus_uid=customer.id, status='normal')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)    
    
#fang kaineng  2015-7-31    
    def detail(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        #print customer.id
        queryset=UserAddress.objects.filter(cus_uid=customer.id)
        serializer = self.get_serializer(queryset, many=True)

        return    Response(serializer.data)
        
    @detail_route(methods=['post'])
    def update(self, request, *args, **kwargs):
        customer = get_object_or_404(Customer,user=request.user)
        customer_id=customer.id     #  获取用户id
        content = request.REQUEST
        id = content.get('id',None)
        receiver_state = content.get('receiver_state',None)
        receiver_city = content.get('receiver_city',None)
        receiver_district = content.get('receiver_district',None)
        receiver_address= content.get('receiver_address',None)
        receiver_name=content.get('receiver_name',None)
        receiver_mobile=content.get('receiver_mobile',None)
        UserAddress.objects.filter(id=id).update(
            cus_uid=customer_id,
            receiver_name=receiver_name,
            receiver_state=receiver_state,
            receiver_city=receiver_city,
            receiver_district=receiver_district,
            receiver_address=receiver_address,
            receiver_mobile=receiver_mobile)
        return Response("0")

    @detail_route(methods=["post"])
    def delete_address(self, request, pk=None):
        instance = self.get_object()
        instance.status = UserAddress.DELETE
        instance.save()
        return Response({'ret': True})
    
    @detail_route(methods=['post'])
    def change_default(self, request, pk=None):
        id_default = pk
        result = {}
        try:
            customer = get_object_or_404(Customer,user=request.user)
            other_addr = UserAddress.objects.filter(cus_uid=customer.id)
            for one in other_addr:
                one.default = False
                one.save()
            default_addr = UserAddress.objects.get(id=id_default)
            default_addr.default = True
            default_addr.save()
            result['ret'] = True
        except:
            result['ret'] = False
        return Response(result)
    
    @detail_route(methods=['post'])
    def create_address(self, request, pk=None):
        customer = get_object_or_404(Customer,user=request.user)
        customer_id=customer.id     #  获取用户id
        content = request.REQUEST
        receiver_state = content.get('receiver_state',None)
        receiver_city = content.get('receiver_city',None)
        receiver_district = content.get('receiver_district',None)
        receiver_address= content.get('receiver_address',None)
        receiver_name=content.get('receiver_name',None)
        receiver_mobile=content.get('receiver_mobile',None)
        UserAddress.objects.create(  cus_uid= customer_id, receiver_name =  receiver_name,  receiver_state    = receiver_state , receiver_city    =  receiver_city,receiver_district  =   receiver_district,receiver_address   =  receiver_address, receiver_mobile    =  receiver_mobile   )
        return Response({"22":55})

    @list_route(methods=['get'])
    def get_one_address(self, request):
        id = request.GET.get("id")
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        qs = queryset.filter(id=id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class DistrictViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    author:kaineng.fang
    方法名及其目的：
    province_list（）：省列表
    city_list：根据省获得市
    country_list:根据市获得区或者县
    """
    queryset = District.objects.all()
    serializer_class = serializers.DistrictSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)   
     
    @list_route(methods=['get'])
    def province_list(self, request, *args, **kwargs):
        queryset = District.objects.filter(grade=1)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @list_route(methods=['get'])
    def city_list(self, request, *args, **kwargs):
        content = request.REQUEST
        province_id = content.get('id',None)
        queryset = District.objects.filter(parent_id=province_id)
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data) 
    
    @list_route(methods=['get'])
    def country_list(self, request, *args, **kwargs):
        content = request.REQUEST
        city_id = content.get('id',None)
        print  city_id
        queryset = District.objects.filter(parent_id=city_id)
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)    

from flashsale.pay.models_coupon import IntegralLog, Integral, CouponPool, Coupon

class UserIntegralViewSet(viewsets.ModelViewSet):
    queryset = Integral.objects.all()
    serializer_class = serializers.UserIntegralSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(integral_user=customer.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserIntegralLogViewSet(viewsets.ModelViewSet):
    queryset = IntegralLog.objects.all()
    serializer_class = serializers.UserIntegralLogSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(integral_user=customer.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserCouponPoolViewSet(viewsets.ModelViewSet):
    queryset = CouponPool.objects.all()
    serializer_class = serializers.UserCouponPoolSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

import json
from django.http import HttpResponse


class UserCouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = serializers.UserCouponSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(coupon_user=customer.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        data = []
        for query in queryset:
            coupon_no = query.coupon_no
            coupol = CouponPool.objects.get(coupon_no=coupon_no)
            coupon_user = query.coupon_user
            coupon_type = coupol.coupon_type
            coupon_value = coupol.coupon_value
            coupon_status = coupol.coupon_status
            created = coupol.created.strftime("%Y-%m-%d")
            deadline = coupol.deadline.strftime("%Y-%m-%d %H:%M")
            data_entry = {"coupon_user": coupon_user, "coupon_no": coupon_no, "coupon_type": coupon_type,
                          "coupon_value": coupon_value, "coupon_status": coupon_status,
                          "deadline": deadline,"created":created
                          }
            data.append(data_entry)

        return HttpResponse(json.dumps(data), content_type='application/json')
    
