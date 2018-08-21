# encoding=utf8
from django.db.models import Q
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework.response import Response
from rest_framework import permissions

from common.auth import WeAppAuthentication
from flashsale.coupon.models import CouponTransferRecord
from flashsale.pay.models.user import Customer
from flashsale.restpro.v2.serializers.serializers import BudgetLogSerialize
from flashsale.coupon.models import CouponTemplate


def template_name(template_id):
    ct = CouponTemplate.objects.filter(id=template_id).first()
    if ct:
        return ct.title
    return ''


class EliteScoreViewSet(viewsets.GenericViewSet):
    """
    """
    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BudgetLogSerialize

    def index(self, request, *args, **kwargs):
        """
        GET /rest/v2/elite_score

        精英妈妈积分记录
        """
        customer = Customer.getCustomerByUser(user=request.user)
        mama = customer.getXiaolumm()

        if not mama:
            return Response({'code': 1, 'msg': '没有mama'})

        result = []

        records = CouponTransferRecord.objects.filter(
            Q(coupon_from_mama_id=mama.id) | Q(coupon_to_mama_id=mama.id),
            transfer_status=CouponTransferRecord.DELIVERED).order_by('-created')

        for record in records:
            score = 0
            if record.coupon_from_mama_id == mama.id:
                if record.transfer_type in [CouponTransferRecord.OUT_CASHOUT, CouponTransferRecord.IN_RETURN_COUPON]:
                    score = -record.elite_score
            if record.coupon_to_mama_id == mama.id:
                if record.transfer_type in [
                    CouponTransferRecord.IN_BUY_COUPON,
                    CouponTransferRecord.OUT_TRANSFER,
                    CouponTransferRecord.IN_GIFT_COUPON,
                    CouponTransferRecord.IN_RECHARGE,
                    CouponTransferRecord.IN_BUY_COUPON_WITH_COIN
                ]:
                    score = record.elite_score

            if score != 0:
                result.append({
                    'created': record.created,
                    'type': record.transfer_type_display,
                    'score': score,
                    'template_id': record.template_id,
                })

        queryset = self.paginate_queryset(result)
        resp = self.get_paginated_response(queryset)

        for item in resp.data['results']:
            item['desc'] = template_name(item['template_id'])
        return resp
