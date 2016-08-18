# coding: utf-8
from rest_framework import authentication, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from flashsale.pay.models import Customer

from . import models, serializers


class PushViewSet(viewsets.ModelViewSet):
    """
    接口已废弃
    """
    queryset = models.PushTopic.objects.all()
    serializer_class = serializers.PushTopicSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = ()

    @list_route(methods=['post'])
    def set_device(self, request, *args, **kwargs):
        customer = Customer.objects.normal_customer.filter(user=request.user).first()
        if not customer:
            return Response({'user_account': ''})

        return Response({'user_account': 'customer-%d' % customer.id})
