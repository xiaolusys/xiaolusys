# coding=utf-8
import logging
import datetime
import urlparse
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from flashsale.coupon import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import APIException

from shopback.items.models import Product
from flashsale.coupon.models import UserCoupon, OrderShareCoupon, CouponTemplate
from flashsale.pay.models import Customer, ShoppingCart, SaleTrade
from flashsale.pay.tasks import task_release_coupon_push
from flashsale.promotion.models_freesample import XLSampleOrder

logger = logging.getLogger(__name__)


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
    serializer_class = serializers.UserCouponSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(customer_id=customer.id)

    def list_unpast_coupon(self, queryset, status=UserCoupon.UNUSED):
        """ 过滤券池状态 """
        queryset = queryset.filter(status=status)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = self.list_unpast_coupon(queryset, status=UserCoupon.UNUSED)
        queryset = queryset.order_by('-created')  # 时间排序
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def list_past_coupon(self, request):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = self.list_unpast_coupon(queryset, status=UserCoupon.PAST)
        queryset = queryset.order_by('-created')  # 时间排序
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """　根据参数生成不同类型的优惠券,多张优惠券逗号分隔 """
        content = request.REQUEST
        template_ids = content.get("template_id") or ''
        if not template_ids:  # 参数有误
            return Response({"code": 3, "res": "优惠券不存在", "coupons": ""})
        try:
            template_ids = [int(i) for i in template_ids.split(',')]
            customer = Customer.objects.get(user=request.user)
            if template_ids:  # 根据模板id发放
                code = None
                msg = None
                coupon_ids = []
                for template_id in template_ids:
                    try:
                        coupon, code, msg = UserCoupon.objects.create_normal_coupon(buyer_id=customer.id,
                                                                                    template_id=template_id, ufrom='wx')
                        if coupon:  # 添加返回的coupon
                            coupon_ids.append(coupon.id)
                    except:
                        return Response({"code": 9, "res": "您已领取", "coupons": ""})
                queryset = self.queryset.filter(id__in=coupon_ids)
                serializer = self.get_serializer(queryset, many=True)
                if code == 0:
                    # 推送消息提醒
                    task_release_coupon_push.s(customer.id).delay()
                return Response({"code": code, "res": msg, "coupons": serializer.data})
        except Customer.DoesNotExist:
            return Response({"code": 8, "res": "需登陆后领取", "coupons": ""})
        except TypeError:
            return Response({"code": 7, "res": "优惠券不存在", "coupons": ""})
        else:
            return Response({"code": 7, "res": "优惠券不存在", "coupons": ""})

    def check_by_coupon(self, coupon, product_ids=None, use_fee=None):
        coupon_message = ''
        try:
            coupon.check_user_coupon(product_ids=product_ids, use_fee=use_fee)  # 验证优惠券
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

    @list_route(methods=['get'])
    def get_usercoupons_by_template(self, request):
        """
        :arg template_id
        :return user coupon with the template
        """
        content = request.REQUEST
        template_id = content.get('template_id') or 0
        queryset = self.get_owner_queryset(request)
        queryset = queryset.filter(template_id=template_id)
        queryset = queryset.order_by('created')[::-1]  # 时间排序
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CouponTemplateViewSet(viewsets.ModelViewSet):
    queryset = CouponTemplate.objects.all()
    serializer_class = serializers.CouponTemplateSerialize
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)  # 这里使用只读的权限
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_useful_template_query(self):
        # 点击方式领取的　有效的　在预置天数内的优惠券
        tpls = self.queryset.filter(coupon_type=CouponTemplate.TYPE_NORMAL,
                                    status__gte=CouponTemplate.SENDING,
                                    status__lte=CouponTemplate.FINISHED)
        now = datetime.datetime.now()
        tpls = tpls.filter(release_start_time__lte=now, release_end_time__gte=now)  # 开始发放中的优惠券模板
        return tpls

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_useful_template_query())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()


def get_order_or_active_share_template(coupon_type):
    """
    获取订单分享模板
    获取活动分享模板
    """
    now = datetime.datetime.now()
    tpl = CouponTemplate.objects.filter(
        coupon_type=coupon_type,
        status=CouponTemplate.SENDING,
    ).order_by('-created').first()  # 最新建的一个
    if tpl:
        if not tpl.release_start_time <= now <= tpl.release_end_time:
            raise Exception('优惠券模板设置错误:%s' % tpl.id)
    return tpl


def get_customer(request):
    """ get customer """
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        return None
    return customer


class OrderShareCouponViewSet(viewsets.ModelViewSet):
    queryset = OrderShareCoupon.objects.all()
    serializers = serializers.OrderShareCouponSerialize
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def create(self, request, *args, **kwargs):
        raise APIException('method not allowed')

    def check_order_valid(self, uniq_id, buyer_id):
        """ 判断订单是该用户的 """
        return SaleTrade.objects.filter(tid=uniq_id, buyer_id=buyer_id).first()

    def check_customer_active(self, customer_id):
        """ 检查用户活动的有效性 """
        return XLSampleOrder.objects.filter(customer_id=customer_id).first()

    @list_route(methods=['post'])
    def create_order_share(self, request, *args, **kwargs):
        """
        创建订单分享
        返回分享链接
        """
        customer = get_customer(request)
        if customer is None:
            return Response({"code": 2, "msg": "用户不存在", "share_link": ''})
        content = request.REQUEST
        uniq_id = content.get('uniq_id') or ''  # 订单分享创建
        ufrom = content.get("ufrom") or ''
        if not uniq_id:
            return Response({"code": 1, "msg": "参数有误", "share_link": ''})
        if self.check_order_valid(uniq_id, customer.id) is None:
            return Response({"code": 4, "msg": "订单不存在", "share_link": ''})

        tpl = get_order_or_active_share_template(CouponTemplate.TYPE_ORDER_SHARE)  # 获取有效的分享模板
        if not tpl:
            return Response({"code": 3, "msg": "分享出错", "share_link": ''})
        if not ufrom:
            logger.warn('customer:{0}, param ufrom is None'.format(customer.id))
        state, order_share = OrderShareCoupon.objects.create_coupon_share(tpl, customer, uniq_id, ufrom)
        share_link = '/pages/odsharecoupon.html?uniq_id={0}'.format(order_share.uniq_id)
        share_link = urlparse.urljoin(settings.M_SITE_URL, share_link)
        return Response({"code": 0, "msg": "分享成功", "share_link": share_link})

    @list_route(methods=['post'])
    def create_active_share(self, request, *args, **kwargs):
        """
        创建活动分享
        返回分享链接
        """
        customer = get_customer(request)
        if customer is None:
            return Response({"code": 2, "msg": "用户不存在", "share_link": ''})
        content = request.REQUEST
        uniq_id = content.get('uniq_id') or ''  # 活动分享创建
        ufrom = content.get("ufrom") or ''
        if not uniq_id:
            return Response({"code": 1, "msg": "参数有误", "share_link": ''})
        # if self.check_customer_active(customer.id) is None:  # 检查参与活动的有效性
        # return Response({"code": 3, "msg": "分享出错", "share_link": ''})

        tpl = get_order_or_active_share_template(CouponTemplate.TYPE_ACTIVE_SHARE)  # 获取有效的分享模板
        if not tpl:
            return Response({"code": 3, "msg": "分享出错", "share_link": ''})
        if not ufrom:
            logger.warn('customer:{0}, param ufrom is None'.format(customer.id))
        state, active_share = OrderShareCoupon.objects.create_coupon_share(tpl, customer, uniq_id, ufrom)
        share_link = '/pages/acsharecoupon.html?uniq_id={0}'.format(active_share.uniq_id)
        share_link = urlparse.urljoin(settings.M_SITE_URL, share_link)
        return Response({"code": 0, "msg": "分享成功", "share_link": share_link})

    @list_route(methods=['post'])
    def pick_order_share_coupon(self, request):
        content = request.REQUEST
        uniq_id = content.get("uniq_id") or ''
        ufrom = content.get("ufrom") or ''
        customer = get_customer(request)
        if customer is None:
            return Response({"code": 3, "msg": "用户不存在", "coupon_id": ''})
        if not uniq_id:
            return Response({"code": 1, "msg": "参数错误", "coupon_id": ''})
        coupon_share = self.queryset.filter(uniq_id=uniq_id).first()
        if coupon_share is None:
            return Response({"code": 2, "msg": "领取完了哦", "coupon_id": ''})
        else:
            if not coupon_share.release_count < coupon_share.limit_share_count:  # 领取次数必须小于最大领取限制
                return Response({"code": 2, "msg": "领取完了", "coupon_id": ''})
        if not ufrom:
            logger.warn('customer:{0}, param ufrom is None'.format(customer.id))

        template_id = coupon_share.template_id
        coupon, code, msg = UserCoupon.objects.create_order_share_coupon(customer.id, template_id, uniq_id, ufrom)
        if code != 0:
            return Response({"code": code, "msg": msg, "coupon_id": ''})
        else:
            return Response({"code": code, "msg": msg, "coupon_id": coupon.id})

    @list_route(methods=['post'])
    def pick_active_share_coupon(self, request):
        content = request.REQUEST
        uniq_id = content.get("uniq_id") or ''
        ufrom = content.get("ufrom") or ''
        customer = get_customer(request)
        if customer is None:
            return Response({"code": 3, "msg": "用户不存在", "coupon_id": ''})
        if not uniq_id:
            return Response({"code": 1, "msg": "参数错误", "coupon_id": ''})
        coupon_share = self.queryset.filter(uniq_id=uniq_id).first()
        if coupon_share is None:
            return Response({"code": 2, "msg": "领取完了哦", "coupon_id": ''})
        else:
            print coupon_share.release_count, coupon_share.limit_share_count
            if not coupon_share.release_count < coupon_share.limit_share_count:  # 领取次数必须小于最大领取限制
                return Response({"code": 2, "msg": "领取完了", "coupon_id": ''})
        if not ufrom:
            logger.warn('customer:{0}, param ufrom is None'.format(customer.id))

        template_id = coupon_share.template_id
        coupon, code, msg = UserCoupon.objects.create_active_share_coupon(customer.id, template_id, uniq_id, ufrom)
        if code != 0:
            return Response({"code": code, "msg": msg, "coupon_id": ''})
        else:
            return Response({"code": code, "msg": msg, "coupon_id": coupon.id})
