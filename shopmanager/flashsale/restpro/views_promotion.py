# -*- coding:utf8 -*-
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import exceptions
from . import permissions as perms
from flashsale.promotion.models import XLSampleSku, XLSampleApply, XLFreeSample, XLSampleOrder, XLInviteCode
from flashsale.promotion.managers import VipCodeManager
import serializers
from django.forms import model_to_dict
import datetime
from django.db.models import Sum, Count
from flashsale.pay.models import Customer
from django.shortcuts import get_object_or_404


class XLFreeSampleViewSet(viewsets.ModelViewSet):
    """ 获取免费申请试用　产品信息接口　"""
    queryset = XLFreeSample.objects.all()
    serializer_class = serializers.XLFreeSampleSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    free_samples = (1, )

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(id__in=self.free_samples)  # 要加入活动的产品
        data = []
        for sample in queryset:
            dic = model_to_dict(sample, exclude=['id'])
            data.append({"sample": dic,
                         "skus": [model_to_dict(sku, fields=['sku_name', 'sku_code']) for sku in sample.skus.all()]})
        return Response(data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class XLSampleOrderViewSet(viewsets.ModelViewSet):
    """　### 申请免费活动商品正式订单提交接口　

    """
    queryset = XLSampleOrder.objects.all()
    serializer_class = serializers.XLSampleOrderSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    share_link = '/sale/promotion/xlsampleapply/'

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def get_promotion_result(self, vipcode):
        """ 返回自己的邀请链接　和邀请结果　推荐数量　和下载数量 """
        promote_count = XLSampleApply.objects.filter(vipcode=vipcode).count()  # 邀请的数量
        app_down_count = XLSampleOrder.objects.filter(vipcode=vipcode).count()  # 下载appd 的数量
        return promote_count, app_down_count, self.share_link

    def create(self, request, *args, **kwargs):
        content = request.REQUEST
        customer = get_object_or_404(Customer, user=request.user)
        vipcode = content.get('vipcode', None)
        outer_id = content.get('outer_id', None)
        sku_code = content.get('sku_code', None)
        mobile = content.get('mobile', None)
        if mobile is None:
            return Response({"code": 1})  # 缺少参数
        xlin_codes = XLInviteCode.objects.filter(mobile=customer.mobile)
        try:
            XLSampleOrder.objects.get(customer_id=customer.id, vipcode=vipcode)
            # 返回自己的邀请链接　和邀请结果
            if xlin_codes.exists():
                cus_vicode = xlin_codes[0].vipcode
                promote_count, app_down_count, share_link = self.get_promotion_result(cus_vicode)
                return Response(
                    {'promote_count': promote_count, 'app_down_count': app_down_count, 'share_link': share_link})
            else:
                return Response({'share_link': self.share_link})
        except XLSampleOrder.DoesNotExist:
            if not (sku_code and customer.id and vipcode and outer_id):
                return Response({"code": 1})  # 缺少参数
            # 参数不缺创建正式申请记录
            XLSampleOrder.objects.create(customer_id=customer.id, vipcode=vipcode, outer_id=outer_id, sku_code=sku_code)
            # 创建自己的邀请链接
            expiried = datetime.datetime(2016, 2, 29)
            cus_vicode = XLInviteCode.objects.genVIpCode(mobile, expiried)
            # 返回自己的邀请链接　和邀请结果　推荐数量　和下载数量
            promote_count, app_down_count, share_link = self.get_promotion_result(cus_vicode)
            return Response(
                {'promote_count': promote_count, 'app_down_count': app_down_count, 'share_link': share_link})
        except XLSampleOrder.MultipleObjectsReturned:
            # 返回自己的邀请链接　和邀请结果
            if xlin_codes.exists():
                cus_vicode = xlin_codes[0].vipcode
                promote_count, app_down_count, share_link = self.get_promotion_result(cus_vicode)
                return Response(
                    {'promote_count': promote_count, 'app_down_count': app_down_count, 'share_link': share_link})
            else:
                return Response({'share_link': self.share_link})

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def win_prize(self, request):
        """ 中奖接口:满足条件 """
        xlsapplys = XLSampleApply.objects.all()  # 手机验证
        xlsorders = XLSampleOrder.objects.all()  # 下载
        grou_xlsapplys = xlsapplys.values("vipcode").annotate(vipcode_count=Count('mobile'))
        group_xlsorders = xlsapplys.values("vipcode").annotate(vipcode_count=Count('id'))
        return Response({"code": 1})