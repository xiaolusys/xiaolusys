# coding: utf8
from __future__ import absolute_import, unicode_literals

from rest_framework import viewsets
from rest_framework import authentication, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from outware.models import OutwareAccount

import logging
logger = logging.getLogger(__name__)


class FengchaoCallbackViewSet(viewsets.GenericViewSet):
    """
    ## 蜂巢回调 API：
    ``` 接口响应 code = 0 表示成功, code > 0表示失败, info 为失败错误信息```
    > ### 采购单实收回传接口: [po_confirm]( ./callback/po_confirm.json ) 调用方法:POST;
    > ### 订单状态更新接口: [order_state]( ./callback/order_state.json ) 调用方法:POST;
    > ### 订单确认发货接口: [order_delivery]( ./callback/order_delivery.json ) 调用方法:POST;
    > ### 退货确认收货接口: [return_delivery]( ./callback/return_delivery.json ) 调用方法:POST;
    """
    authentication_classes = []
    permission_classes = []
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer,)
    serializer_class = BaseSerializer

    def list(self, request, *args, **kwargs):
        return Response({'code': 0, 'info': 'success'})

    def verify_request(self, request):
        data = request.POST.dict()
        owapp = OutwareAccount.objects.get(app_id=data.get('app_id'))
        sign = data.pop('sign')
        return owapp.sign_verify(data, sign)

    @list_route(methods=['POST'])
    def po_confirm(self, request, *args, **kwargs):
        if not self.verify_request(request):
            return Response({'code': 1, 'info': '签名无效'})

        return Response({'code': 0, 'info': 'success'})

    @list_route(methods=['POST'])
    def order_state(self, request, *args, **kwargs):
        if not self.verify_request(request):
            return Response({'code': 1, 'info': '签名无效'})

        return Response({'code': 0, 'info': 'success'})

    @list_route(methods=['POST'])
    def order_delivery(self, request, *args, **kwargs):
        if not self.verify_request(request):
            return Response({'code': 1, 'info': '签名无效'})

        return Response({'code': 0, 'info': 'success'})

    @list_route(methods=['POST'])
    def return_delivery(self, request, *args, **kwargs):
        if not self.verify_request(request):
            return Response({'code': 1, 'info': '签名无效'})

        return Response({'code': 0, 'info': 'success'})


