# coding=utf-8
from __future__ import unicode_literals, absolute_import
import datetime
import decimal

from rest_framework import viewsets
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from rest_framework import filters
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.decorators import detail_route, list_route
from rest_framework.decorators import parser_classes
from rest_framework.response import Response

from flashsale.pay.apis.v1.customer import get_customer_by_django_user
from flashsale.xiaolumm.models import CashOut
from flashsale.xiaolumm.apis.v1.xiaolumama import get_mama_by_openid
from flashsale.xiaolumm.apis.v1.mmcashout import cash_out_2_budget
from ..serializers import mmcashout
import logging

logger = logging.getLogger(__name__)


class CashOutFilter(filters.FilterSet):
    class Meta:
        model = CashOut
        fields = ['status', 'cash_out_type']


class CashOutViewSet(viewsets.ModelViewSet):
    """ version2: 代理提现接口
    """
    queryset = CashOut.objects.all()
    serializer_class = mmcashout.CashOueSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication, )
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer, )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CashOutFilter

    def create(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def update(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def partial_update(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def destroy(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def retrieve(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    @property
    def customer(self):
        return get_customer_by_django_user(self.request.user)

    @property
    def mama(self):
        return get_mama_by_openid(self.customer.unionid)

    def owner_queryset(self):
        return self.queryset.filter(xlmm=self.mama.id)

    def list(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """妈妈用户提现列表
        """
        queryset = self.owner_queryset()
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['post'])
    def cash_out_2_budget(self, request):
        # type: (HttpRequest, *Any, **Any) -> Response
        """妈妈钱包 提现 到 小鹿钱包
        """
        cash_out_value = request.POST.get('value') or None
        if not cash_out_value:
            return Response({"code": 1, 'info': '参数错误'})
        value = int(decimal.Decimal(cash_out_value) * 100)
        info, code = '提交成功', 0
        try:
            cash_out_2_budget(self.mama, value)
        except Exception as e:
            info = e.message
            code = 2
        return Response({"code": code, 'info': info})
