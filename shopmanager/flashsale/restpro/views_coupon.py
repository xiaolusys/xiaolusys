# coding=utf-8
from flashsale.pay.models_coupon_new import UserCoupon, CouponsPool
from rest_framework import viewsets
from . import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import APIException


class UserCouponsViewSet(viewsets.ModelViewSet):
    """
    - {prefix}/method: get 获取用户惠券(默认为有效且没有过期的优惠券)
    - {prefix}/list_past_coupon method:get 获取用户已经过期的优惠券
    ->return:
        -->id:          优惠券id
        -->coupon_no:   优惠券券池号码
        -->status:      优惠券状态　0：未使用，１:已经使用
        -->poll_status: 券池发放状态：１:已经发放，0：未发放，2:已经过期
        -->coupon_type: 优惠券类型：RMB118:"二期代理优惠券" ,POST_FEE:"退货补邮费", C150_10:"满150减10", C259_20:"满259减20"
        -->sale_trade:  绑定交易id：购买交易的id
        -->customer:    对应的客户id
        -->coupon_value: 优惠券对应的面值
        -->valid:       优惠券的有效性（true or false）
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

    def list_valid_coupon(self, queryset, valid=True):
        """ 过滤模板是否有效状态 """
        queryset = queryset.filter(cp_id__template__valid=valid)
        return queryset

    def list_unpast_coupon(self, queryset, status=CouponsPool.RELEASE):
        """ 过滤券池状态 """
        queryset = queryset.filter(cp_id__status=status)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = self.list_valid_coupon(queryset, valid=True)
        queryset = self.list_unpast_coupon(queryset, status=CouponsPool.RELEASE)
        queryset = queryset.order_by('created')[::-1]  # 时间排序
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def list_past_coupon(self, request):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = self.list_unpast_coupon(queryset, status=CouponsPool.PAST)
        queryset = queryset.order_by('created')[::-1]  # 时间排序
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
            if template_id:  # 根据模板id发放
                uc = UserCoupon()
                cus = {"buyer_id": customer.id, "template_id": template_id}
                release_res = uc.release_by_template(**cus)
                return Response({"res": release_res})
        except Customer.DoesNotExist:
            return Response({"res": "cu_not_fund"})
        else:
            return Response({"res": "not_release"})

    @detail_route(methods=["post"])
    def choose_coupon(self, request, pk=None):
        print "request data :", request.data
        content = request.REQUEST
        price = int(content.get("price", 0))
        coupon_id = pk  # 获取order_id
        queryset = self.filter_queryset(self.get_owner_queryset(request)).filter(id=coupon_id)
        coupon = queryset.get(id=pk)
        try:
            coupon.check_usercoupon()  # 验证优惠券
            coupon.cp_id.template.usefee_check(price)
        except Exception, exc:
            raise APIException(u"错误:%s" % exc.message)
        return Response({"res": "ok"})