# coding=utf-8
from __future__ import unicode_literals, absolute_import
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework import authentication
from rest_framework import permissions

from flashsale.pay.apis.v1.customer import get_customer_by_django_user

from flashsale.coupon import serializers
from flashsale.coupon.models import UserCoupon
from flashsale.coupon.apis.v1.transfer import apply_pending_return_transfer_coupon
from flashsale.coupon.apis.v1.usercoupon import return_transfer_coupon
import logging

logger = logging.getLogger(__name__)


class UserCouponsViewSet(viewsets.ModelViewSet):
    queryset = UserCoupon.objects.all()
    serializer_class = serializers.UserCouponSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        return Response({'code': 1, 'info': 'method not allow'})

    def update(self, request, *args, **kwargs):
        return Response({'code': 1, 'info': 'method not allow'})

    def destroy(self, request, *args, **kwargs):
        return Response({'code': 1, 'info': 'method not allow'})

    @list_route(methods=['get'])
    def get_unused_boutique_coupons(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """获取　未使用状态的　精品类型　优惠券
        """
        customer = get_customer_by_django_user(user=request.user)
        data = []
        ubcs = UserCoupon.objects.get_unused_boutique_coupons().filter(customer_id=customer.id)
        # queryset = unused_boutique_coupons
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        # serializer = serializers.BoutiqueUserCouponSerialize(page, many=True)
        # return self.get_paginated_response(serializer.data)
        # serializer = serializers.BoutiqueUserCouponSerialize(queryset, many=True)
        # return Response(serializer.data)
        item = {}
        for coupon in ubcs:
            template_id = coupon.template_id
            if template_id not in item:
                product_img = coupon.self_template().extras.get('product_img')
                item[template_id] = {
                    'product_img': product_img,
                    'coupon_num': 1,
                    'coupon_ids': [],
                    'gift_transfer_coupon_ids': [],
                    'from_sys_coupon_ids': [],
                    'from_mama_coupon_ids': [],
                }
            else:
                item[template_id]['coupon_num'] += 1
            item[template_id]['coupon_ids'].append(coupon.id)
            transfer_coupon_pk = coupon.extras.get('transfer_coupon_pk')
            if transfer_coupon_pk:
                item[template_id]['from_mama_coupon_ids'].append(coupon.id)
            elif coupon.is_gift_transfer_coupon:  # 如果是系统赠送的流通优惠券
                item[template_id]['gift_transfer_coupon_ids'].append(coupon.id)
            else:
                item[template_id]['from_sys_coupon_ids'].append(coupon.id)
        for k, v in item.iteritems():
            data.append({
                'template_id': k,
                'product_img': v['product_img'],
                'coupon_ids': v['coupon_ids'],
                'coupon_num': v['coupon_num'],
                'from_mama_coupon_ids': v['from_mama_coupon_ids'],
                'gift_transfer_coupon_ids': v['gift_transfer_coupon_ids'],
                'from_sys_coupon_ids': v['from_sys_coupon_ids']
            })
        return Response(data)

    @list_route(methods=['POST'])
    def apply_return_boutique_coupons(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """提交退还　精品券　优惠券　给上级妈妈　的申请
        """
        customer = get_customer_by_django_user(request.user)
        coupon_ids = request.POST.get('coupon_ids')
        if not isinstance(coupon_ids, list):
            coupon_ids = coupon_ids.split(',')
            coupon_ids = [str(i).strip() for i in coupon_ids if i.strip().isdigit()]
        if not coupon_ids:
            return Response({'code': 1, 'info': '参数错误'})
        user_coupons = UserCoupon.objects.get_unused_boutique_coupons().filter(customer_id=customer.id,
                                                                               id__in=coupon_ids)
        coupon_ids = [c['id'] for c in user_coupons.values('id')]
        if not coupon_ids:
            return Response({'code': 3, 'info': '没有找到优惠券'})
        state = apply_pending_return_transfer_coupon(coupon_ids)
        if not state:
            return Response({'code': 2, 'info': '申请失败'})
        return Response({'code': 0, 'info': '申请成功'})

    @list_route(methods=['post'])
    def return_freeze_boutique_coupons_2_upper(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """将自己　被冻结的　且标记了　将要退回　流通记录的　优惠券退回给上级
        """
        customer = get_customer_by_django_user(request.user)
        coupon_ids = request.POST.get('coupon_ids')
        if not isinstance(coupon_ids, list):
            coupon_ids = coupon_ids.split(',')
            coupon_ids = [str(i).strip() for i in coupon_ids if i.strip().isdigit()]
        if not coupon_ids:
            return Response({'code': 1, 'info': '参数错误'})
        user_coupons = UserCoupon.objects.get_freeze_boutique_coupons().filter(customer_id=customer.id,
                                                                               id__in=coupon_ids)
        if not user_coupons:
            return Response({'code': 3, 'info': '没有找到优惠券'})
        state = return_transfer_coupon(user_coupons)
        if not state:
            return Response({'code': 2, 'info': '操作失败'})
        return Response({'code': 0, 'info': '操作成功'})

