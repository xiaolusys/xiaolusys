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
    detail  （）：获得用户所有收获地址  (使用 get 方法）    /address.json
    delete（）：删除某个地址 （post  方法)      /address/" + id + "/delete_address
    change_default：选择收获地址  (post方法）    /address/" + id + "/change_default",更改默认地址
    create_address：创建新的收获地址（post方法）  /address/create_address?format=json'   data: {
          
            "receiver_state": receiver_state,
            "receiver_city": receiver_city,
            "receiver_district": receiver_district,
            "receiver_address": receiver_address,
            "receiver_name": receiver_name,
            "receiver_mobile": receiver_mobile,
        }
        
        get_one_addres： 得到要修改的那一个地址的信息（get请求）        /address/  get_one_address       data{"id":}         
         update:        "/address/" + id + "/update";  :修改地址    （post）      data: {
             “id”：
            "receiver_state": receiver_state,
            "receiver_city": receiver_city,
            "receiver_district": receiver_district,
            "receiver_address": receiver_address,
            "receiver_name": receiver_name,
            "receiver_mobile": receiver_mobile,
        }
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

    @list_route(methods=['post'])
    def create_address(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        customer_id = customer.id  # 获取用户id
        content = request.REQUEST
        receiver_state = content.get('receiver_state', None)
        receiver_city = content.get('receiver_city', None)
        receiver_district = content.get('receiver_district', None)
        receiver_address = content.get('receiver_address', None)
        receiver_name = content.get('receiver_name', None)
        receiver_mobile = content.get('receiver_mobile', None)
        UserAddress.objects.create(cus_uid=customer_id, receiver_name=receiver_name, receiver_state=receiver_state,
                                   receiver_city=receiver_city, receiver_district=receiver_district,
                                   receiver_address=receiver_address, receiver_mobile=receiver_mobile)
        return Response({"22": 55})

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
from shopback.base import log_action, ADDITION, CHANGE

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
            id = query.id
            coupon_no = query.coupon_no
            coupol = CouponPool.objects.get(coupon_no=coupon_no)
            coupon_user = query.coupon_user
            coupon_type = coupol.coupon_type
            coupon_value = coupol.coupon_value
            coupon_status = coupol.coupon_status
            created = coupol.created.strftime("%Y-%m-%d")
            deadline = coupol.deadline.strftime("%Y-%m-%d %H:%M")
            data_entry = {"id": id, "coupon_user": coupon_user, "coupon_no": coupon_no, "coupon_type": coupon_type,
                          "coupon_value": coupon_value, "coupon_status": coupon_status,
                          "deadline": deadline,"created":created
                          }
            data.append(data_entry)

        return Response(data)

    @list_route(methods=['post'])
    def user_create_coupon(self, request, *args, **kwargs):
        """用户购买页面　在自己没有优惠券的情况下　生成优惠券 """
        data = ['ok']
        customer = Customer.objects.get(user=request.user.id)
        coupon_type = request.data.get("coupon_type", 0)
        if coupon_type:
            value_type = int(coupon_type)
            COUPON_VALUE = (0, 3, 30)   # 优惠券价格
            mobile = customer.mobile
            coupon_user = customer.id
            unionid = customer.unionid
            coupon_value = COUPON_VALUE[value_type]
            deadline = datetime.datetime.today() + datetime.timedelta(days=2)
            karg_dic = {"coupon_user": coupon_user, "unionid": unionid, "mobile": mobile, "deadline": deadline,
                        "coupon_type": coupon_type, "coupon_value": coupon_value}
            cou_xlmm = Coupon()
            # 只是为小鹿代理生成优惠券
            cou_xlmm.xlmm_Coupon_Create(**karg_dic)
            log_action(request.user.id, customer, CHANGE, u'通过接口程序－生成优惠券')
            # 每个客户都生成优惠券
            # cou = CouponPool.objects.create(coupon_value=coupon_value, deadline=deadline,
            #                                coupon_type=value_type, coupon_status=3)  # 生成优惠券 # 可以使用的 # 有效两天
            # Coupon.objects.create(coupon_user=customer.id, coupon_no=cou.coupon_no, mobile=mobile)  # 发放优惠券到用户

        return Response(data)

    @detail_route(methods=['post'])
    def pass_user_coupon(self, request, pk=None, *args, **kwargs):
        # 修改该优惠券为　使用过的状态　CouponPool.USED
        instance = self.get_object()
        coupon_no = instance.coupon_no
        # 优惠券发放列表中找到对应的优惠券
        coupon_pool = CouponPool.objects.get(coupon_no=coupon_no)
        # 修改该优惠券状态到　已经使用的
        res = coupon_pool.use_coupon()
        return Response(data=[res])