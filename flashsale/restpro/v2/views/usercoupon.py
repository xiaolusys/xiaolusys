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
from flashsale.coupon.apis.v1.transfer import return_transfer_coupon_2_up_level_mama
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
        unused_boutique_coupons = UserCoupon.objects.get_unused_boutique_coupons().filter(customer_id=customer.id)
        queryset = unused_boutique_coupons
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.BoutiqueUserCouponSerialize(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializers.BoutiqueUserCouponSerialize(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['post'])
    def return_boutique_coupons(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """退还　精品券　优惠券　给上级妈妈
        """
        customer = get_customer_by_django_user(request.user)
        coupon_ids = request.POST.get('coupon_ids')
        user_coupons = UserCoupon.objects.get_unused_boutique_coupons().filter(customer_id=customer.id,
                                                                               id__in=coupon_ids)
        coupon_ids = [c['id'] for c in user_coupons.values('id')]
        state = return_transfer_coupon_2_up_level_mama(coupon_ids)
        if not state:
            return Response({'code': 1, 'info': '退券失败'})
        return Response({'code': 0, 'info': '退券成功'})
