# coding=utf-8
import datetime
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from . import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import APIException

from shopback.items.models import Product
from flashsale.pay.models_coupon_new import UserCoupon, CouponsPool, CouponTemplate
from flashsale.pay.models import Customer, ShoppingCart


class UserCouponsViewSet(viewsets.ModelViewSet):
    """
    - {prefix}/method: get 获取用户惠券(默认为有效且没有过期的优惠券)
    - {prefix}/list_past_coupon method:get 获取用户已经过期的优惠券
        -  return:
            `id`:优惠券id <br>`coupon_no:`优惠券券池号码<br>
            `title`: 优惠券模板定义的标题
            `status:` 优惠券状态　0：未使用，１:已经使用， 2:冻结中<br>
            `poll_status:` 券池发放状态：１:已经发放，0：未发放，2:已经过期<br>
            `coupon_type:` 优惠券类型：RMB118:"二期代理优惠券" ,POST_FEE:"退货补邮费", C150_10:"满150减10", C259_20:"满259减20"<br>
            `sale_trade:`  绑定交易id：购买交易的id<br>
            `customer:`　对应的客户id<br>
            `coupon_value:` 优惠券对应的面值<br>
            `valid:`　优惠券的有效性（true or false）<br> `title:`　优惠券标题<br>
            `created:`　创建时间<br> `deadline:`　截止时间<br>
            `use_fee:` 满单额（即满多少可以使用）

    - {prefix}/method: post 创建用户优惠券

        `arg`: coupon_type  优惠券类型
        `C150_10:` 满150减10
        `C259_20:` 满259减20

        -  return:
        `创建受限` {'res':'limit'}
        `创建成功` {'res':'success'}
        `暂未发放`{'res':'not_release'}
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
        """　根据参数生成不同类型的优惠券,多张优惠券逗号分隔 """
        content = request.REQUEST
        template_ids = content.get("template_id", '')
        try:
            template_ids = [int(i) for i in template_ids.split(',')]
            customer = Customer.objects.get(user=request.user)
            if template_ids:  # 根据模板id发放
                for template_id in template_ids:
                    uc = UserCoupon()
                    cus = {"buyer_id": customer.id, "template_id": template_id}
                    release_res = uc.release_by_template(**cus)
                return Response({"res": release_res})
        except Customer.DoesNotExist:
            return Response({"res": "cu_not_fund"})
        except TypeError:
            return Response({"res": "not_release"})
        else:
            return Response({"res": "not_release"})

    def check_by_coupon(self, coupon, product_ids=None, use_fee=None):
        coupon_message = ''
        try:
            coupon.check_usercoupon(product_ids=product_ids, use_fee=use_fee)  # 验证优惠券
        except Exception, exc:
            coupon_message = exc.message
        return coupon_message

    @detail_route(methods=["post"])
    def choose_coupon(self, request, pk=None):

        coupon_id = pk  # 获取order_id
        queryset = self.filter_queryset(self.get_owner_queryset(request)).filter(id=coupon_id)
        coupon = queryset.get(id=pk)

        content = request.REQUEST
        cart_ids = content.get("cart_ids", None)
        pro_num = content.get("pro_num", None)
        item = content.get("item_id", None)

        coupon_message = ''
        res = 0
        if item and pro_num:  # 立即购买页面判断
            try:
                pro = Product.objects.get(id=item)

                total_fee = pro.agent_price * int(pro_num)  # 满单金额
                coupon_message = self.check_by_coupon(coupon, product_ids=[item, ], use_fee=total_fee)
                if coupon_message != '':  # 有提示信息
                    res = 1
            except Exception, exc:
                res = 1
                coupon_message = exc.message

        elif cart_ids:  # 购物车页面判断
            cart_ids = cart_ids.split(',')  # 购物车id
            carts = ShoppingCart.objects.filter(id__in=cart_ids)
            product_ids = []
            total_fee = 0
            for cart in carts:
                total_fee += cart.price * cart.num
                product_ids.append(cart.item_id)
            coupon_message = self.check_by_coupon(coupon, product_ids=product_ids, use_fee=total_fee)
            if coupon_message != '':
                res = 1
        return Response({"res": res, "coupon_message": coupon_message})


class CouponTemplateViewSet(viewsets.ModelViewSet):
    queryset = CouponTemplate.objects.all()
    serializer_class = serializers.CouponTemplateSerializer
    authentication_classes = (authentication.SessionAuthentication, )
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)  # 这里使用只读的权限
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_useful_template_query(self):
        # 点击方式领取的　有效的　在预置天数内的优惠券
        tpls = self.queryset.exclude(type__in=(CouponTemplate.RMB118,
                                               CouponTemplate.POST_FEE_5,
                                               CouponTemplate.POST_FEE_10,
                                               CouponTemplate.POST_FEE_15,
                                               CouponTemplate.POST_FEE_20))
        tpls = tpls.filter(way_type=CouponTemplate.CLICK_WAY,
                           valid=True)
        now = datetime.datetime.now()
        tpls = tpls.filter(release_start_time__lte=now, release_end_time__gte=now)  # 开始发放中的优惠券模板
        return tpls

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_useful_template_query())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()


