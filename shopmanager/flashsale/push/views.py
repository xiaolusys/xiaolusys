# coding: utf-8
from rest_framework import authentication, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework import permissions

from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.pay.models.user import Customer

from . import models, serializers


class PushViewSet(viewsets.ViewSet):
    """
    """
    queryset = models.PushTopic.objects.all()
    serializer_class = serializers.PushTopicSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    @list_route(methods=['post'])
    def set_device(self, request, *args, **kwargs):
        """
        接口已废弃
        """
        customer = Customer.objects.normal_customer.filter(user=request.user).first()
        if not customer:
            return Response({'user_account': ''})

        return Response({'user_account': 'customer-%d' % customer.id})

    @list_route(methods=['get'])
    def topic(self, request, *args, **kwargs):
        """
        CUSTOMER_PAY 购买过的买家
        XLMM 小鹿妈妈
        XLMM_A类 一元小鹿妈妈

        """
        customer = Customer.objects.filter(user=request.user).first()
        topics = []

        if not customer:
            return Response({
                'topics': [],
                'customer_id': '',
            })

        agencylevels = {
            XiaoluMama.INNER_LEVEL: u"普通",
            XiaoluMama.VIP_LEVEL: "VIP1",
            XiaoluMama.A_LEVEL: u"A类",
            XiaoluMama.VIP2_LEVEL: "VIP2",
            XiaoluMama.VIP4_LEVEL: "VIP4",
            XiaoluMama.VIP6_LEVEL: "VIP6",
            XiaoluMama.VIP8_LEVEL: "VIP8",
        }

        # 付费买家
        if customer.first_paytime:
            topics.append(u'CUSTOMER_PAY')

        # 小鹿妈妈
        xlmm = customer.get_xiaolumm()
        if xlmm:
            topics.append(u'XLMM')
            level = agencylevels.get(xlmm.agencylevel, '')
            topics.append(u'XLMM_' + level)

        return Response({
            'topics': topics,
            'customer_id': customer.id
        })
