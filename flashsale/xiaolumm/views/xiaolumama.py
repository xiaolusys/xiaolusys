# coding=utf-8
from __future__ import unicode_literals, absolute_import
import logging
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

logger = logging.getLogger(__name__)
from ..apis.v1.xiaolumama import set_mama_manager_by_mama_id
from ..models import XiaoluMama


class SetMamaManager(APIView):
    """设置小鹿妈妈的管理员
    """
    queryset = XiaoluMama.objects.all()
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, permissions.IsAdminUser)

    def get(self, request):
        return Response({})

    def post(self, request):
        mama_id = request.POST.get('mama_id') or 0
        manager_id = request.POST.get('manager_id') or 0
        if not (mama_id and manager_id):
            return Response({'code': 1, 'info': '参数错误'})
        set_mama_manager_by_mama_id(mama_id=int(mama_id), manager_id=int(manager_id))
        return Response({'code': 0, 'info': '设置成功'})