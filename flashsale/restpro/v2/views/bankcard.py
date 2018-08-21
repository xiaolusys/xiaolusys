# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import logging
import os
import time
import urlparse

from django.db import IntegrityError
from rest_framework import status
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response

from flashsale.restpro import permissions as perms
from flashsale.pay.models import Customer, BankAccount
from .. import serializers
from flashsale.pay import constants
from core.ocr import bankcard


class BankAccountViewset(viewsets.ModelViewSet):
    """
    ## 用户银行卡API:
    > ## 获取支持银行卡类型参数列表 GET: [/rest/v2/bankcards/preferances](/rest/v2/bankcards/preferances):
    > ## 银行卡列表 GET: [/rest/v2/bankcards](/rest/v2/bankcards):
    > ## 创建银行卡 POST: /rest/v2/bankcards:
    > ## 设置默认银行卡 POST: /rest/v2/bankcards/[cardid]/set_default:
    > ## 获取默认银行卡 GET: /rest/v2/bankcards/get_default:
    > ## 删除银行卡 POST: /rest/v2/bankcards/[cardid]/delete:
    """
    queryset = BankAccount.objects.filter(status=BankAccount.NORMAL)
    serializer_class = serializers.BankAccountSerializer
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)

    def get_userbanks(self, request):
        return self.queryset.filter(user=request.user)

    @list_route(methods=['get'])
    def preferances(self, request, *args, **kwargs):
        bank_list = constants.BANK_LIST
        return Response({'banks': bank_list})

    def list(self, request, *args, **kwargs):
        queryset = self.get_userbanks(request)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data.update(
            user=request.user.id
        )
        account_no = data['account_no']
        account_name = data['account_name']
        if not bankcard.verify(account_no, account_name):
            return Response({'code': 1 ,'info': '银行卡号不合法' })

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        if data.get('default'):
            instance = self.queryset.get(id=serializer.data.get('id'))
            instance.set_default()

        headers = self.get_success_headers(serializer.data)
        return Response({'code': 0, 'card': serializer.data}, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        raise NotImplemented('not available.')

    @detail_route(methods=['post'])
    def set_default(self, request, *args, **kwargs):
        """ you can't change the card account name and no if saved """
        instance = self.get_object()
        instance.set_default()

        serializer = self.get_serializer(instance)
        return Response({'code': 0, 'card': serializer.data})

    @list_route(methods=['get'])
    def get_default(self, request, *args, **kwargs):
        default_account = self.get_userbanks(request).filter(default=True).first()
        if not default_account:
            return Response({})
        # print 'default_account', default_account
        serializer = self.get_serializer(instance=default_account)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.set_invalid()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'])
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.set_invalid()
        return Response({'code': 0, 'info': '删除成功'})