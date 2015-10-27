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
        queryset = queryset.order_by('created')[::-1]
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
    queryset = Coupon.objects.filter()
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
            created = coupol.created.strftime("%Y-%m-%d")
            deadline = coupol.deadline.strftime("%Y-%m-%d")
            data_entry = {"id": id, "coupon_user": coupon_user, "coupon_no": coupon_no, "coupon_type": coupon_type,
                          "coupon_value": coupon_value, "coupon_status": query.status,
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
            log_action(request.user.id, customer, CHANGE, u'通过接口程序－生成小鹿代理优惠券')
        return Response(data)

    @list_route(methods=['post'])
    def user_create_coupon_every(self, request, *args, **kwargs):
        """　　默认创建￥３　有效两天　类型为１　的优惠券　每个coustomer　都可以创建"""
        customer = Customer.objects.get(user=request.user.id)
        coupon_type = request.data.get("coupon_type", CouponPool.LIM30)
        coupon_value = request.data.get("coupon_value", 3)
        deadline = request.data.get("deadline", datetime.datetime.today()+datetime.timedelta(days=2))
        mobile = customer.mobile or ''
        data = ['ok']
        if coupon_type:
            # 每个客户都生成优惠券
            cou = CouponPool.objects.create(coupon_value=coupon_value, deadline=deadline,
                                            coupon_type=coupon_type, coupon_status=3)  # 生成优惠券 # 可以使用的 # 有效两天
            Coupon.objects.create(coupon_user=customer.id, coupon_no=cou.coupon_no, mobile=mobile)  # 发放优惠券到用户
        return Response(data)

    @detail_route(methods=['post'])
    def pass_user_coupon(self, request, pk=None, *args, **kwargs):
        # 修改该优惠券为　使用过的状态　CouponPool.USED
        instance = self.get_object()
        # 修改该优惠券状态到　已经使用的
        res = instance.use_coupon()
        return Response(data=[res])

    @detail_route(methods=['get'])
    def get_user_coupon(self, request, pk=None, *args, **kwargs):
        # 修改该优惠券为　使用过的状态　CouponPool.USED
        instance = self.get_object()
        coupon_no = instance.coupon_no
        # 优惠券发放列表中找到对应的优惠券
        coupon_pool = CouponPool.objects.get(coupon_no=coupon_no)
        # 修改该优惠券状态到　已经使用的
        data_entry = {"id": instance.id, "coupon_user": instance.coupon_user,
                      "coupon_no": coupon_no, "coupon_type": coupon_pool.coupon_type,
                      "coupon_value": coupon_pool.coupon_value,
                      "coupon_status": coupon_pool.coupon_status,
                      "deadline": coupon_pool.deadline, "created": coupon_pool.created
                      }
        return Response(data=[data_entry])
    
from flashsale.pay.models_coupon_new import UserCoupon


class UserCouponsViewSet(viewsets.ModelViewSet):
    """
    - {prefix}/method: get 获取用户优惠券
    ->return:
        -->id:          优惠券id
        -->coupon_no:   优惠券券池号码
        -->status:      优惠券状态　0：未使用，１:已经使用
        -->poll_status: 券池发放状态：１:已经发放，0：未发放，2:已经过期
        -->coupon_type: 优惠券类型：RMB118:"二期代理优惠券" ,POST_FEE:"退货补邮费", C150_10:"满150减10", C259_20:"满259减20"
        -->sale_trade:  绑定交易id：购买交易的id
        -->customer:    对应的客户id
        -->coupon_value: 优惠券对应的面值
        -->valid:       优惠券的有效性（ttur or false）
        -->title:       优惠券标题
        -->created:     创建时间
        -->deadline:    截止时间
    
    - {prefix}/method: post 创建用户优惠券
    ->arg: coupon_type  优惠券类型
    -->C150_10:满150减10
    -->C259_20:满259减20
    :return
    {'res':'limit'}         ->: 创建受限
    {'res':'success'}       ->: 创建成功
    {'res':'not_release'}   ->: 暂未发放
    """

    queryset = UserCoupon.objects.all()
    serializer_class = serializers.UsersCouponSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(customer=customer.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        data = []
        for query in queryset:
            id = query.id
            coupon_no = query.cp_id.coupon_no
            customer = query.customer
            coupon_type = query.cp_id.template.type
            coupon_value = query.cp_id.template.value
            valid = query.cp_id.template.valid
            title = query.cp_id.template.title
            poll_status = query.cp_id.status
            status = query.status
            sale_trade = query.sale_trade
            created = query.created.strftime("%Y-%m-%d")
            deadline = query.cp_id.template.deadline.strftime("%Y-%m-%d")
            data_entry = {"id": id, "coupon_no": coupon_no, "status": status, "poll_status": poll_status,
                          "coupon_type": coupon_type, "sale_trade": sale_trade,
                          "customer": customer, "coupon_value": coupon_value,
                          "valid": valid, "title": title, "created": created,
                          "deadline": deadline}
            data.append(data_entry)
        return Response(data)

    def create(self, request, *args, **kwargs):
        """　根据参数生成不同类型的优惠券　"""
        content = request.REQUEST
        if content:
            return Response({"res": "not_release"})
        try:
            template_id = int(content.get("template_id", None))
        except TypeError:
            return Response({"res": "not_release"})
        try:
            customer = Customer.objects.get(user=request.user)
            if template_id:     # 根据模板id发放
                uc = UserCoupon()
                cus = {"buyer_id": customer.id, "template_id": template_id}
                release_res = uc.release_by_template(**cus)
                return Response({"res": release_res})
        except Customer.DoesNotExist:
            return Response({"res": "cu_not_fund"})
        else:
            return Response({"res": "not_release"})

