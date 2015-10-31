#-*- coding:utf8 -*-
import hashlib
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
from django.forms import model_to_dict
import json


class SaleRefundViewSet(viewsets.ModelViewSet):
    """
    - {prefix}/method: get 获取用户的退款单列表
    - {prefix}/method: post 创建用户的退款单
        -创建退款单
            --id:   sale order id
            --reason:   退货原因
            --num:      退货数量
            --sum_price:    申请金额
            --description:  申请描述
        -修改退款单
            --id:   sale order id
            --modify:   1
            --reason:   退货原因
            --num:  退货数量
            --sum_price:    申请金额
            --description:  申请描述
        -添加退款单物流信息
            --id:   sale order id
            --modify:   2
            --company:  物流公司
            --sid:  物流单号
    -{prefix}/{{ order_id }}/get_by_order_id/method:get  根据订单id 获取指定的退款单
     返回: feedback  驳回原因
            id: id
            buyer_id: 用户id
            reason: 买家申请原因
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
        queryset = queryset.order_by('created')[::-1]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):

        res = refund_Handler(request)
        return Response(res)

    @detail_route(methods=["get"])
    def get_by_order_id(self, request, pk=None):
        order_id = pk  # 获取order_id
        queryset = self.filter_queryset(self.get_owner_queryset(request)).filter(order_id=order_id)
        refund_dic = {}
        if queryset.exists():
            sale_refund = queryset[0]
            refund_dic = model_to_dict(sale_refund, fields=["id", "feedback", "buyer_id", "reason"])
        return Response(refund_dic)


class UserAddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be   viewed or edited.
    - author： kaineng .fang  2015-8--
    - 方法及其目的
    - /{id}/delete（）：删除某个地址 （post  方法)
    - /{id}/change_default：选择收获地址  (post方法）   更改默认地址
    - /create_address：创建新的收获地址（post方法）  
        > data: {    
        >     "receiver_state": receiver_state,
        >     "receiver_city": receiver_city,
        >     "receiver_district": receiver_district,
        >     "receiver_address": receiver_address,
        >     "receiver_name": receiver_name,
        >     "receiver_mobile": receiver_mobile,
        > }
    - /get_one_addres： 得到要修改的那一个地址的信息（get请求） data{"id":}         
    - /{id}/update: 修改地址（post）      
        > data: {
        >     id：地址ＩＤ
        >     "receiver_state": receiver_state,
        >     "receiver_city": receiver_city,
        >     "receiver_district": receiver_district,
        >     "receiver_address": receiver_address,
        >     "receiver_name": receiver_name,
        >     "receiver_mobile": receiver_mobile,
        > }
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
        
    @detail_route(methods=['post'])
    def update(self, request, *args, **kwargs):
        result = {}
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
        try:
            UserAddress.objects.filter(id=id).update(
            cus_uid=customer_id,
            receiver_name=receiver_name,
            receiver_state=receiver_state,
            receiver_city=receiver_city,
            receiver_district=receiver_district,
            receiver_address=receiver_address,
            receiver_mobile=receiver_mobile)
            result['ret'] = True
        except:
            result['ret'] = False
        return Response(result)

    @detail_route(methods=["post"])
    def delete_address(self, request, pk=None):
        try:
            instance = self.get_object()
            instance.status = UserAddress.DELETE
            instance.save()
            return Response({'ret': True})
        except:
            return Response({'ret': False})
    
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

    @list_route(methods=['post'])
    def create_address(self, request):
        result = {}
        customer = get_object_or_404(Customer, user=request.user)
        customer_id = customer.id  # 获取用户id
        content = request.REQUEST
        receiver_state = content.get('receiver_state', None)
        receiver_city = content.get('receiver_city', None)
        receiver_district = content.get('receiver_district', None)
        receiver_address = content.get('receiver_address', None)
        receiver_name = content.get('receiver_name', None)
        receiver_mobile = content.get('receiver_mobile', None)
        try:
            UserAddress.objects.create(cus_uid=customer_id, receiver_name=receiver_name, 
                                       receiver_state=receiver_state,default=True,
                                       receiver_city=receiver_city, receiver_district=receiver_district,
                                       receiver_address=receiver_address, receiver_mobile=receiver_mobile)
            result['ret'] = True
        except:
            result['ret'] = False
        return Response(result)

    @list_route(methods=['get'])
    def get_one_address(self, request):
        id = request.GET.get("id")
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        qs = queryset.filter(id=id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

from rest_framework_extensions.cache.decorators import cache_response

class DistrictViewSet(viewsets.ModelViewSet):
    """
    ###地理区域信息接口及参数：
    
    －　/province_list：省列表
    －　/city_list：根据省获得市
    > 　id:即province ID
     
    －　/country_list:根据市获得区或者县
    > 　id:即country ID
    """
    queryset = District.objects.all()
    serializer_class = serializers.DistrictSerializer# Create your views here.
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def calc_distirct_cache_key(self, view_instance, view_method,
                            request, args, kwargs):
        key_vals = ['id']
        key_maps = kwargs or {}
        for k,v in request.GET.copy().iteritems():
            if k in key_vals and v.strip():
                key_maps[k] = v
                
        return hashlib.sha256(u'.'.join([
                view_instance.__module__,
                view_instance.__class__.__name__,
                view_method.__name__,
                json.dumps(key_maps, sort_keys=True).encode('utf-8')
            ])).hexdigest()
    
    @cache_response(timeout=24*60*60,key_func='calc_distirct_cache_key')
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)   
    
    @cache_response(timeout=24*60*60,key_func='calc_distirct_cache_key')
    @list_route(methods=['get'])
    def province_list(self, request, *args, **kwargs):
        queryset = District.objects.filter(grade=1)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @cache_response(timeout=24*60*60,key_func='calc_distirct_cache_key')
    @list_route(methods=['get'])
    def city_list(self, request, *args, **kwargs):
        content = request.REQUEST
        province_id = content.get('id',None)
        if province_id==u'0':
            return      Response({"result":False})
        else:
            queryset = District.objects.filter(parent_id=province_id)
            serializer = self.get_serializer(queryset, many=True)
            return Response({"result":True,"data":serializer.data})  
    
    @cache_response(timeout=24*60*60,key_func='calc_distirct_cache_key')
    @list_route(methods=['get'])
    def country_list(self, request, *args, **kwargs):
        content = request.REQUEST
        city_id = content.get('id',None)
        #print city_id.encode("utf-8"),type(int(city_id.encode("utf-8")))
        print type(city_id),city_id
        if city_id==u'0':
            print "等于0"
            return      Response({"result":False})
        else:
            queryset = District.objects.filter(parent_id=city_id)
            serializer = self.get_serializer(queryset, many=True)
            return Response({"result":True,"data":serializer.data})   

