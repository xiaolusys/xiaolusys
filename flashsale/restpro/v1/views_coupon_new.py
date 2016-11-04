# coding=utf-8
import logging
import datetime
import collections
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
from flashsale.coupon.models import UserCoupon, OrderShareCoupon, CouponTemplate, TmpShareCoupon
from flashsale.pay.models import Customer, ShoppingCart, SaleTrade
from flashsale.pay.tasks import task_release_coupon_push
from flashsale.promotion.models import XLSampleOrder
from flashsale.coupon import constants
from flashsale.pay.models import SaleTrade

logger = logging.getLogger(__name__)


def is_old_customer(customer_id):
    """判断是否是新客户"""
    return SaleTrade.objects.filter(buyer_id=customer_id,
                                    status__gte=SaleTrade.WAIT_SELLER_SEND_GOODS,
                                    status__lte=SaleTrade.TRADE_FINISHED).first()  # 有成功支付订单的


def release_tmp_share_coupon(customer):
    """
    查看临时优惠券中的优惠券是否存在未发的发放
    """
    if not customer:
        return True
    tmp_coupons = TmpShareCoupon.objects.filter(mobile=customer.mobile, status=False)
    st = is_old_customer(customer.id)
    for tmp_coupon in tmp_coupons:
        share = OrderShareCoupon.objects.filter(uniq_id=tmp_coupon.share_coupon_id).first()
        if not share:
            continue
        tpl = share.template
        if not tpl:
            continue
        try:
            if tpl.coupon_type == CouponTemplate.TYPE_ORDER_SHARE:
                # 存在订单分享优惠券
                has_order_share_coupon = UserCoupon.objects.filter(customer_id=customer.id,
                                                                   coupon_type=UserCoupon.TYPE_ORDER_SHARE).exists()
                template_id = constants.LIMIT_ORDER_SHARE_COUPON_TEMPLATE if st or has_order_share_coupon else tpl.id
                x = UserCoupon.objects.create_order_share_coupon(customer.id, template_id, share.uniq_id, ufrom=u'tmp',
                                                                 coupon_value=tmp_coupon.value)
            elif tpl.coupon_type == CouponTemplate.TYPE_ACTIVE_SHARE:
                UserCoupon.objects.create_active_share_coupon(customer.id, tpl.id, share.uniq_id, ufrom=u'tmp')
            tmp_coupon.status = True
            tmp_coupon.save(update_fields=['status'])  # 更新状态到已经领取
        except Exception as exc:
            logger.error(u'release_tmp_share_coupon for customer %s -%s' % (customer.id, exc))
            continue
    return True


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

    ## /rest/v1/usercoupons/get_user_coupons  获取用户优惠券

    params:

    - status　选填(默认为使用),
             可选值
             0:未使用,
             1:已使用,
             2:冻结中,
             3:已经过期,
             4:已经取消
    - coupon_type 选填(默认为全部),
                  可选值
                  1:普通类型,
                  2:下单红包,
                  3:订单分享,
                  4:推荐专享,
                  5:售后补偿,
                  6:活动分享,
                  7:提现兑换,
                  8:精品专用券
    """

    queryset = UserCoupon.objects.all()
    serializer_class = serializers.UserCouponSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(customer_id=customer.id)

    def list_unpast_coupon(self, queryset, status=UserCoupon.UNUSED, coupon_type=None):
        """
        过滤券池状态
        """
        filter_params = {'status': status}
        if coupon_type:
            filter_params['coupon_type'] = coupon_type

        if status in [str(UserCoupon.PAST), str(UserCoupon.USED)]:
            queryset = queryset.filter(**filter_params)
            if queryset.count() > 10:
                queryset = queryset.order_by("-created")[:10]
        else:
            filter_params['expires_time__gte'] = datetime.datetime.now()
            queryset = queryset.filter(**filter_params).order_by('-created')
        return queryset

    @list_route(methods=['get'])
    def get_user_coupons(self, request):
        content = request.REQUEST
        status = content.get("status") or None
        coupon_type = content.get('coupon_type') or None
        customer = get_customer(request)
        release_tmp_share_coupon(customer)  # 查看临时优惠券 有则发放
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = self.list_unpast_coupon(queryset, status=status, coupon_type=coupon_type)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """
        获取优惠券:
        step 1 : 查看临时优惠券中的优惠券是否存在未发的发放 release_tmp_share_coupon
        step 2 : 给当前的优惠券数据
        """

        customer = get_customer(request)
        release_tmp_share_coupon(customer)  # 查看临时优惠券 有则发放

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
            return Response({"code": 7, "res": "优惠券不存在", "coupons": ""})
        try:
            template_ids = [int(i) for i in template_ids.split(',')]
            customer = Customer.objects.get(user=request.user)
            if template_ids:  # 根据模板id发放
                code = 7
                msg = u'没有发放'
                coupon_ids = []
                for template_id in template_ids:
                    try:
                        coupon, code, msg = UserCoupon.objects.create_normal_coupon(buyer_id=customer.id,
                                                                                    template_id=template_id, ufrom='wx')
                        if coupon:  # 添加返回的coupon
                            coupon_ids.append(coupon.id)
                    except:
                        continue
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
    def coupon_able(self, request):
        default_return = collections.defaultdict(usable_coupon=[], disable_coupon=[], info='', code=0)
        content = request.REQUEST
        cart_ids = content.get("cart_ids", None)

        if not cart_ids:
            default_return.update({'info': '购物车为空!', 'code': 1})
            return Response(default_return)

        cart_ids = cart_ids.split(',')  # 购物车id
        carts = ShoppingCart.objects.filter(id__in=cart_ids)
        product_ids = []  # 购物车中的产品id
        total_fee = 0  # 购物车总费用
        for cart in carts:
            total_fee += cart.price * cart.num
            product_ids.append(cart.item_id)

        queryset = self.get_owner_queryset(request)  # customer coupons
        queryset = self.list_unpast_coupon(queryset)  # customer not past coupon
        usable_set = []
        disable_set = []
        for coupon in queryset:
            try:
                coupon.check_user_coupon(product_ids=product_ids, use_fee=total_fee)  # 验证优惠券
                usable_set.append(coupon)
            except AssertionError:
                disable_set.append(coupon)

        from flashsale.pay.models import ModelProduct
        # 检查款式　是否限制使用优惠券　如果是则设置usable_set 为空
        mds = ModelProduct.objects.filter(id__in=[i['model_id'] for i in
                                                  Product.objects.filter(id__in=product_ids).values('model_id')])
        for md in mds:
            if md.is_coupon_deny:
                usable_set = []
                break

        usable_serialier = self.get_serializer(usable_set, many=True)
        disable_serialier = self.get_serializer(disable_set, many=True)
        default_return.update({'usable_coupon': usable_serialier.data, 'disable_coupon': disable_serialier.data})

        return Response(default_return)

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
        queryset = queryset.order_by('-created')  # 时间排序
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def get_share_coupon(self, request):
        """
        获取某个分享 中领取的 优惠券
        """
        content = request.REQUEST
        uniq_id = content.get('uniq_id') or ''
        coupon_share = OrderShareCoupon.objects.filter(uniq_id=uniq_id).first()
        if coupon_share:
            queryset = self.queryset.filter(order_coupon_id=coupon_share.id)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response([])

    @list_route(methods=['get'])
    def get_register_gift_coupon(self, request):
        default_return = collections.defaultdict(code=0, info='', pop_flag=0, coupons=[])
        tplids = [56, 57, 58, 59, 60, 128, 129]
        customer = Customer.objects.get(user=request.user)
        if not customer:
            default_return.update({"code": 1, "info": "用户不存在"})
            return Response(default_return)
        gift_coupons = self.queryset.filter(template_id__in=tplids, customer_id=customer.id)
        if gift_coupons.exists():
            serializer = self.get_serializer(gift_coupons, many=True)
            default_return.update({"info": "新手礼包已领取", "coupons": serializer.data})
            return Response(default_return)
        success_id = []
        codes = []
        except_msgs = set()
        for tplid in tplids:
            try:
                coupon, c_code, msg = UserCoupon.objects.create_normal_coupon(buyer_id=customer.id,
                                                                              template_id=tplid)
                if c_code in [0, 9]:  # 0　是创建　9　是已经存在的
                    codes.append(c_code)
                    success_id.append(coupon.id)
            except AssertionError as e:
                except_msgs.add(e.message)
                continue
        if len(success_id) > 0:
            queryset = self.queryset.filter(id__in=success_id)
            serializer = self.get_serializer(queryset, many=True)
            if codes.count(0) == 7:  # 完整领取　则设置　领取弹窗　位　为　0
                default_return.update({"pop_flag": 1})
            default_return.update({'info': '新手礼包已领取', "coupons": serializer.data})
            return Response(default_return)
        default_return.update({"code": 2, "info": "领取出错啦:%s" % ','.join(except_msgs)})
        return Response(default_return)

    @list_route(methods=['get'])
    def is_picked_register_gift_coupon(self, request):
        default_return = collections.defaultdict(code=0, info='', is_picked=0)
        tplids = range(54, 61)
        customer = Customer.objects.get(user=request.user)
        if not customer:
            default_return.update({"code": 1, "info": "用户不存在"})
            return Response(default_return)
        if self.queryset.filter(template_id__in=tplids, customer_id=customer.id).exists():
            default_return.update({'is_picked': 1, "info": "已经领取过"})
            return Response(default_return)
        default_return.update({"info": "没有领取"})
        return Response(default_return)


class CouponTemplateViewSet(viewsets.ModelViewSet):
    queryset = CouponTemplate.objects.all()
    serializer_class = serializers.CouponTemplateSerialize
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)  # 这里使用只读的权限

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

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
        return Response({})


def get_order_or_active_share_template(coupon_type, template_id=None):
    """
    获取订单分享模板
    获取活动分享模板
    """
    now = datetime.datetime.now()
    if not template_id:
        tpl = CouponTemplate.objects.filter(
            coupon_type=coupon_type,
            status=CouponTemplate.SENDING,
        ).order_by('-created').first()  # 最新建的一个
    else:
        tpl = CouponTemplate.objects.filter(id=template_id).first()  # 指定的那个
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
    serializer_class = serializers.OrderShareCouponSerialize
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def list(self, request, *args, **kwargs):
        raise APIException("METHOD NOT ALLOWED!!!")

    def create(self, request, *args, **kwargs):
        raise APIException('method not allowed')

    def check_order_valid(self, uniq_id, buyer_id):
        """ 判断订单是该用户的 """
        return SaleTrade.objects.filter(tid=uniq_id, buyer_id=buyer_id).first()

    def check_customer_active(self, customer_id):
        """ 检查用户活动的有效性 """
        return XLSampleOrder.objects.filter(customer_id=customer_id).first()

    @list_route(methods=['get'])
    def get_share_coupon(self, request):
        """
        获取某个分享 中领取的 优惠券
        1. 提取正式优惠券
        2. 展示没有领取的临时优惠券
        """
        default_return = collections.defaultdict(tmp_coupon=[], coupon=[])
        content = request.REQUEST
        uniq_id = content.get('uniq_id') or ''
        coupon_share = OrderShareCoupon.objects.filter(uniq_id=uniq_id).first()
        tmpcoupons = TmpShareCoupon.objects.filter(share_coupon_id=uniq_id, status=False)
        tmpserializer = serializers.TmpShareCouponMapSerialize(tmpcoupons, many=True)
        default_return.update({"tmp_coupon": tmpserializer.data})
        if coupon_share:
            queryset = UserCoupon.objects.filter(order_coupon_id=coupon_share.id)
            serializer = serializers.ShareUserCouponSerialize(queryset, many=True)
            default_return.update({"coupon": serializer.data})
            return Response(default_return)
        return Response(default_return)

    @list_route(methods=['post'])
    def create_order_share(self, request, *args, **kwargs):
        """
        创建订单分享
        返回分享链接
        """
        default_return = collections.defaultdict(code=0, msg='', share_link='', title='', description='',
                                                 post_img='', share_times_limit=0)
        customer = get_customer(request)
        if customer is None:
            default_return.update({"code": 2, "msg": "用户不存在"})
            return Response(default_return)
        content = request.REQUEST
        uniq_id = content.get('uniq_id') or ''  # 订单分享创建
        ufrom = content.get("ufrom") or ''
        if not uniq_id:
            default_return.update({"code": 1, "msg": "参数有误"})
            return Response(default_return)
        if self.check_order_valid(uniq_id, customer.id) is None:
            default_return.update({"code": 4, "msg": "订单不存在"})
            return Response(default_return)

        tpl = get_order_or_active_share_template(CouponTemplate.TYPE_ORDER_SHARE,
                                                 template_id=constants.ORDER_SHARE_COUPON_TEMPLATE)  # 获取有效的分享模板
        if not tpl:
            default_return.update({"code": 3, "msg": "分享出错"})
            return Response(default_return)
        if not ufrom:
            logger.warn('customer:{0}, param ufrom is None'.format(customer.id))
        state, order_share = OrderShareCoupon.objects.create_coupon_share(tpl, customer, uniq_id, ufrom)

        share_link = 'rest/v1/users/weixin_login/?next=/mall/order/redpacket?uniq_id={0}&ufrom={1}'.format(
            order_share.uniq_id, ufrom)
        share_link = urlparse.urljoin(settings.M_SITE_URL, share_link)
        default_return.update({"code": 0, "msg": "分享成功", "share_link": share_link,
                               'title': order_share.title, "description": order_share.description,
                               "post_img": order_share.post_img, "share_times_limit": tpl.share_times_limit})
        return Response(default_return)

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
        share_link = '/pages/acsharecoupon.html?uniq_id={0}&ufrom={1}'.format(active_share.uniq_id, ufrom)
        share_link = urlparse.urljoin(settings.M_SITE_URL, share_link)
        return Response({"code": 0, "msg": "分享成功", "share_link": share_link})

    @list_route(methods=['post', 'get'])
    def pick_order_share_coupon(self, request):
        content = request.REQUEST
        uniq_id = content.get("uniq_id") or ''
        ufrom = content.get("ufrom") or ''
        customer = get_customer(request)
        default_return = collections.defaultdict(code=0, msg='', coupon={})
        if customer is None:
            default_return.update({"code": 9, "msg": "用户不存在"})
            return Response(default_return)
        if not uniq_id:
            default_return.update({"code": 10, "msg": "参数错误"})
            return Response(default_return)
        coupon_share = self.queryset.filter(uniq_id=uniq_id).first()
        if coupon_share is None:
            default_return.update({"code": 8, "msg": "领取完了哦"})
            return Response(default_return)
        else:

            urelase_tmp_count = TmpShareCoupon.objects.filter(share_coupon_id=uniq_id, status=False).count()  # 临时未　领取　
            if not (coupon_share.release_count + urelase_tmp_count) < coupon_share.limit_share_count:  # 领取次数必须小于最大领取限制
                default_return.update({"code": 8, "msg": "领取完了"})
                return Response(default_return)
        if not ufrom:
            logger.warn('customer:{0}, param ufrom is None'.format(customer.id))

        # 判断当前用户是否有　历史订单
        st = is_old_customer(customer.id)
        # 如果有订单的用户　再次领取的分享优惠券为指定的其他优惠券
        template_id = constants.LIMIT_ORDER_SHARE_COUPON_TEMPLATE if st else coupon_share.template_id

        coupon, code, msg = UserCoupon.objects.create_order_share_coupon(customer.id, template_id, uniq_id, ufrom)
        if code != 0:
            default_return.update({"code": code, "msg": msg})
            return Response(default_return)
        else:
            default_return.update({"code": code, "msg": msg})
            serializer = serializers.UserCouponSerialize(coupon)
            return Response({"code": code, "msg": msg, "coupon": serializer.data})

    @list_route(methods=['post'])
    def pick_active_share_coupon(self, request):
        content = request.REQUEST
        uniq_id = content.get("uniq_id") or ''
        ufrom = content.get("ufrom") or ''
        customer = get_customer(request)
        if customer is None:
            return Response({"code": 9, "msg": "用户不存在", "coupon_id": ''})
        if not uniq_id:
            return Response({"code": 10, "msg": "参数错误", "coupon_id": ''})
        coupon_share = self.queryset.filter(uniq_id=uniq_id).first()
        if coupon_share is None:
            return Response({"code": 8, "msg": "领取完了哦", "coupon_id": ''})
        else:
            if not coupon_share.release_count < coupon_share.limit_share_count:  # 领取次数必须小于最大领取限制
                return Response({"code": 8, "msg": "领取完了", "coupon_id": ''})
        if not ufrom:
            logger.warn('customer:{0}, param ufrom is None'.format(customer.id))

        template_id = coupon_share.template_id
        coupon, code, msg = UserCoupon.objects.create_active_share_coupon(customer.id, template_id, uniq_id, ufrom)
        if code != 0:
            return Response({"code": code, "msg": msg, "coupon_id": ''})
        else:
            return Response({"code": code, "msg": msg, "coupon_id": coupon.id})


def check_uniq_id(uniq_id):
    """ 检查分享的uniq_id 有效 """
    now = datetime.datetime.now()
    orders_share = OrderShareCoupon.objects.filter(
        uniq_id=uniq_id,
        share_start_time__lte=now,  # 开始分享时间 小于 现在时间
        share_end_time__gte=now,  # 结束分享时间 大于 现在时间
    ).first()
    if orders_share:
        return True
    return False


class TmpShareCouponViewset(viewsets.ModelViewSet):
    queryset = TmpShareCoupon.objects.all()
    serializer_class = serializers.TmpShareCouponSerialize

    def list(self, request, *args, **kwargs):
        raise APIException("METHOD NOT ALLOWED !")

    def update(self, request, *args, **kwargs):
        raise APIException("METHOD NOT ALLOWED !")

    def perform_update(self, serializer):
        raise APIException("METHOD NOT ALLOWED !")

    def partial_update(self, request, *args, **kwargs):
        raise APIException("METHOD NOT ALLOWED !")

    def create(self, request, *args, **kwargs):
        """
        提交临时优惠券
        """
        content = request.REQUEST
        mobile = content.get('mobile') or ''
        uniq_id = content.get("uniq_id") or ''
        coupon = {
            "title": '',
            "coupon_value": 0,
            "deadline": '',
            "mobile": ''}

        default_return = collections.defaultdict(code=0, msg='', coupon=coupon)
        if not (mobile and uniq_id):
            default_return.update({"code": 1, "msg": "参数出错"})
            return Response(default_return)
        if not check_uniq_id(uniq_id):
            default_return.update({"code": 2, "msg": "领取出错"})
            return Response(default_return)

        coupon_share = OrderShareCoupon.objects.filter(uniq_id=uniq_id).first()
        if not coupon_share:
            default_return.update({"code": 4, "msg": "没有找到该分享"})
            return Response(default_return)

        # 当前分享的　临时优惠券张数
        unrelease_tmp_count = self.queryset.filter(share_coupon_id=uniq_id, status=False).count()  # 未领取的临时记录张数
        if unrelease_tmp_count + coupon_share.release_count >= coupon_share.limit_share_count:
            default_return.update({"code": 5, "msg": "领完了"})
            return Response(default_return)
        try:
            tpl = coupon_share.template
            tmp_shre, state = TmpShareCoupon.objects.get_or_create(mobile=mobile, share_coupon_id=uniq_id)
            value, start_use_time, expires_time = tpl.calculate_value_and_time()
            if state and tmp_shre.value != value:
                tmp_shre.value = value
                tmp_shre.save(update_fields=['value'])
            coupon.update(
                {"coupon_value": tmp_shre.value,
                 "title": tpl.title,
                 "deadline": expires_time,
                 "mobile": mobile})
        except Exception as exc:
            logger.warn("when release tmp share coupon the mobile is %s, uniq_id is %s exc:%s" % (mobile, uniq_id, exc))
            default_return.update({"code": 3, "msg": "领取出错了"})
            return Response(default_return)
        default_return.update({"code": 0, "msg": "领取成功"})
        return Response(default_return)
