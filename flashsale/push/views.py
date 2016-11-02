# coding: utf-8
from rest_framework import authentication, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework import permissions

from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.pay.models.user import Customer
from flashsale.protocol.models import APPFullPushMessge

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
        返回用户所在 TOPIC　用于 APP　推送

        CUSTOMER_PAY 购买过的买家
        XLMM 小鹿妈妈
        XLMM_A类 一元小鹿妈妈

        """
        customer = Customer.objects.filter(user=request.user).first()
        topics = []

        if not customer:
            return Response({
                'topics': [],
            })

        # 内部测试专用分组
        if customer.id in [1, 913405]:
            topics.append(APPFullPushMessge.TOPIC_CESHI)

        agencylevels = {
            XiaoluMama.VIP_LEVEL: APPFullPushMessge.TOPIC_XLMM_VIP_LEVEL,
            XiaoluMama.A_LEVEL: APPFullPushMessge.TOPIC_XLMM_A_LEVEL,
            XiaoluMama.VIP2_LEVEL: APPFullPushMessge.TOPIC_XLMM_VIP2_LEVEL,
            XiaoluMama.VIP4_LEVEL: APPFullPushMessge.TOPIC_XLMM_VIP4_LEVEL,
            XiaoluMama.VIP6_LEVEL: APPFullPushMessge.TOPIC_XLMM_VIP6_LEVEL,
            XiaoluMama.VIP8_LEVEL: APPFullPushMessge.TOPIC_XLMM_VIP8_LEVEL,
        }

        # 付费买家
        if customer.first_paytime:
            topics.append(APPFullPushMessge.TOPIC_CUSTOMER_PAY)

        # 小鹿妈妈
        xlmm = customer.get_xiaolumm()
        if xlmm:
            topics.append(APPFullPushMessge.TOPIC_XLMM)
            level = agencylevels.get(xlmm.agencylevel, None)
            if level:
                topics.append(level)

        return Response({
            'topics': topics,
        })
