# coding=utf-8
from __future__ import unicode_literals, absolute_import
import logging
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from core.options import log_action, CHANGE

logger = logging.getLogger(__name__)
from ..apis.v1.xiaolumama import set_mama_manager_by_mama_id, change_mama_follow_elite_mama, get_mama_by_id
from ..models import XiaoluMama
from .permission import IsAccessChangeUpperMama
from flashsale.pay.models.user import Customer

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


class ChangeUpperMama(APIView):
    """更换/设置/妈妈的上级妈妈，在修改精英妈妈的场景使用本接口
    apis/xiaolumm/v1/mm/change_upper_mama
    """
    queryset = XiaoluMama.objects.all()
    renderer_classes = (JSONRenderer,)
    # permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, permissions.IsAdminUser)
    permission_classes = (IsAccessChangeUpperMama,)

    def get(self, request):
        return Response({'direct_info': [XiaoluMama.ELITE_TYPE_CHOICES]})

    def post(self, request):
        content = request.POST or request.data
        mama_id = content.get('mama_id') or 0
        upper_mama_id = content.get('upper_mama_id') or 0
        direct_info = content.get('direct_info') or ''
        if not (mama_id and upper_mama_id and direct_info):
            return Response({'code': 1, 'info': '参数错误'})

        try:
            mm = get_mama_by_id(mama_id)
            state = change_mama_follow_elite_mama(mama_id=int(mama_id),
                                                  upper_mama_id=int(upper_mama_id),
                                                  direct_info=direct_info)
            if state:
                log_action(request.user, mm, CHANGE, '修改上级妈妈信息 upper=%s direct_info=%s' % (upper_mama_id, direct_info))
        except Exception as e:
            return Response({'code': 2, 'info': e.message})
        return Response({'code': 0, 'info': '设置成功'})

class CreateMama(APIView):
    """create妈妈，
    apis/xiaolumm/v1/mm/create_mama
    """


queryset = XiaoluMama.objects.all()
renderer_classes = (JSONRenderer,)
# permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, permissions.IsAdminUser)
permission_classes = (IsAccessChangeUpperMama,)


def get(self, request):
    return Response({'direct_info': [XiaoluMama.ELITE_TYPE_CHOICES]})


def post(self, request):
    content = request.POST or request.data
    customer_id = content.get('customer_id') or 0
    upper_mama_id = content.get('upper_mama_id') or 0
    direct_info = content.get('direct_info') or ''
    if not (customer_id and upper_mama_id and direct_info):
        return Response({'code': 1, 'info': '参数错误'})

    try:
        cu = Customer.objects.filter(id=customer_id).first()
        if not cu:
            return Response({'code': 3, 'info': '用户不存在'})
        mama = XiaoluMama.objects.filter(openid=cu.unionid).first()
        if not mama:
            mama = XiaoluMama(openid=cu.unionid, mobile=cu.mobile, progress=XiaoluMama.PROFILE,
                              last_renew_type=XiaoluMama.ELITE, status=XiaoluMama.EFFECT,
                              charge_status=XiaoluMama.CHARGED, agencylevel=XiaoluMama.VIP_LEVEL)
            mama.save()
        else:
            return Response({'code': 4, 'info': '小鹿妈妈已经存在，无需再创建'})

        log_action(request.user, mama, CHANGE, 'create妈妈信息 upper=%s direct_info=%s' % (upper_mama_id, direct_info))
        if upper_mama_id == 0:
            return Response({'code': 0, 'info': '设置成功'})
        state = change_mama_follow_elite_mama(mama_id=int(mama.id),
                                              upper_mama_id=int(upper_mama_id),
                                              direct_info=direct_info)

    except Exception as e:
        return Response({'code': 2, 'info': e.message})
    return Response({'code': 0, 'info': '设置成功'})