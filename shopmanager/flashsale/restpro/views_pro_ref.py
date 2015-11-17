# coding=utf-8
""" 产品退货记录分析　"""
from rest_framework import viewsets
from . import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from shopback.refunds.models_refund_rate import ProRefunRcord


class ProRefRcdViewSet(viewsets.ModelViewSet):
    queryset = ProRefunRcord.objects.all()
    serializer_class = serializers.ProRefunRcordSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        queryset = self.queryset.filter(contactor=request.user.id)
        return queryset

    def list(self, request, *args, **kwargs):
        if request.user.has_perm('refunds.browser_all_pro_duct_ref_lis'):
            queryset = self.queryset
        else:
            queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.order_by('product')[::-1]  # 产品id排序
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return