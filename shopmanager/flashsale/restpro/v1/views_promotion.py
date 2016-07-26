# coding=utf-8
import os, urlparse
import datetime

from django.conf import settings
from django.forms import model_to_dict
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

from rest_framework.decorators import detail_route, list_route
from rest_framework import exceptions
from rest_framework import mixins
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import viewsets

from flashsale.restpro import permissions as perms
from flashsale.promotion.models import XLSampleSku, XLSampleApply, XLFreeSample, XLSampleOrder, XLInviteCode
from . import serializers
from flashsale.pay.models import Customer
from flashsale.promotion.models import XLReferalRelationship
from flashsale.promotion import constants
import logging
import random

logger = logging.getLogger('django.request')

PYQ_TITLES = [
    '告诉你，今年元宵其实要这样过。。。#脸红心跳',
    '哈哈，老公好不好，抢了睡袋就知道！',
    '哈哈，只有1%的人知道，原来这两个我都想要～'
]


def get_random_title():
    n = int(random.random() * 3) % 3
    return PYQ_TITLES[n], n


class XLFreeSampleViewSet(viewsets.ModelViewSet):
    """ 获取免费申请试用　产品信息接口　"""
    queryset = XLFreeSample.objects.all()
    serializer_class = serializers.XLFreeSampleSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    free_samples = (1,)

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
- {prefix} [method:post]  
    -  参数:  
  >> `vipcode`: 邀请码（必须）  
  >> `outer_id`: 免费商品的外部编码（必须）  
  >> `sku_code`: 选择商品尺码id（必须）  
  >> `mobile`: 用户手机号吗（必须）  
    -  返回:  
  >> `promote_count`: 当前用户的推荐数量  
  >> `app_down_count`: 当前用户的下载数量  
  >> `share_link`: 当前用户的分享页（基础链接），分享时候需要修改添加参数   
  `ufrom:`分享到的平台  
  {  
  `wxapp`: 微信  
  `pyq  `: 朋友圈  
  `qq   `: qq  
  `txwb `: 腾讯微博   
  `web  `: 网页  
  }  
  `from_customer:` 分享用户customer id  
- {prefix}/get_share_content [method:post]
`link_qrcode`: 二维码图片地址
`title`: 活动主题
`active_dec`: 活动描述
    """
    queryset = XLSampleOrder.objects.all()
    serializer_class = serializers.XLSampleOrderSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    share_link = constants.SHARE_LINK
    PROMOTION_LINKID_PATH = constants.PROMOTION_LINKID_PATH

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def get_promotion_result(self, customer_id, outer_id):
        """ 返回自己的用户id　　返回邀请结果　推荐数量　和下载数量 """
        applys = XLSampleApply.objects.filter(from_customer=customer_id, outer_id=outer_id)
        promote_count = applys.count()  # 邀请的数量　
        app_down_count = XLSampleOrder.objects.filter(xlsp_apply__in=applys.values('id')).count()  # 下载appd 的数量
        share_link = self.share_link.format(**{'customer_id': customer_id})
        link_qrcode = self.gen_customer_share_qrcode_pic(customer_id, 'web')
        res = {'promote_count': promote_count,
               'app_down_count': app_down_count,
               'share_link': share_link,
               'link_qrcode': link_qrcode}
        return res

    def get_share_link(self, params):
        link = urlparse.urljoin(settings.M_SITE_URL, self.share_link)
        return link.format(**params)

    def get_qrcode_page_link(self):
        return urlparse.urljoin(settings.M_SITE_URL, reverse('qrcode_view'))

    def gen_customer_share_qrcode_pic(self, customer_id, ufrom):

        params = {'customer_id': customer_id, "ufrom": ufrom}
        file_name = os.path.join(self.self.PROMOTION_LINKID_PATH,
                                 'custom-{customer_id}-{ufrom}.jpg'.format(**params))
        share_link = self.get_share_link(params)

        from core.upload.xqrcode import push_qrcode_to_remote
        qrcode_url = push_qrcode_to_remote(file_name, share_link)

        return qrcode_url

    @list_route(methods=['get', 'post'])
    def get_share_content(self, request):
        """ 返回要分享的内容 share_type: picture and link"""
        content = request.REQUEST
        ufrom = content.get('ufrom', None)
        customer = get_object_or_404(Customer, user=request.user)
        customer_id = customer.id
        nick = customer.nick
        # link_qrcode = self.gen_custmer_share_qrcode_pic(customer_id, ufrom)
        title, n = get_random_title()

        # add nick to title shared to PengYouQuan
        if n == 0:
            title = nick + title

        active_dec = '天猫热销10万件的全棉睡袋，现在免费送啦！还全国包邮！宝宝用很好，送人也特别有面子！还有百万现金红包。。。不多说啦，抢抢抢去了！'

        params = {'customer_id': customer_id, "ufrom": ufrom}
        share_link = self.get_share_link(params)
        agent = request.META.get('HTTP_USER_AGENT', None)
        link_qrcode = constants.SAHRE_ICON
        if 'iPhone' in agent:
            # 之前版本的ipthon app 版本是拼接站点地址获取图片的
            link_qrcode = '/static/img/share-222-pyq2.png'

        return Response({"link_qrcode": link_qrcode,
                         "title": title,
                         "share_link": share_link,
                         "share_img": constants.SAHRE_ICON,
                         "qrcode_link": self.get_qrcode_page_link(),
                         "share_type": "link",
                         "active_dec": active_dec})

    def create(self, request, *args, **kwargs):
        content = request.REQUEST
        customer = get_object_or_404(Customer, user=request.user)
        outer_id = content.get('outer_id', None)
        sku_code = content.get('sku_code', None)
        mobile = content.get('mobile', None)

        if mobile is None or not (sku_code and outer_id):
            return Response({"code": 1})  # 缺少参数
        xlapplys = XLSampleApply.objects.filter(mobile=mobile, outer_id=outer_id).order_by('-created')
        xlapply = None

        if xlapplys.exists():
            xlapply = xlapplys[0]

        # 获取自己的正式使用订单
        xls_orders = XLSampleOrder.objects.filter(customer_id=customer.id, outer_id=outer_id).order_by('-created')

        if len(xls_orders) >= 1:  # 已经有试用订单
            xls_order = xls_orders[0]
            xls_order.sku_code = sku_code  # 将最后一个的sku修改为当前的sku
            xls_order.save()
        else:  # 没有　试用订单　创建　正式　订单记录
            if xlapply:  # 有　试用申请　记录的
                XLSampleOrder.objects.create(xlsp_apply=xlapply.id, customer_id=customer.id,
                                             outer_id=outer_id, sku_code=sku_code)
                xlapply.status = XLSampleApply.ACTIVED  # 激活预申请中的字段
                xlapply.save()
            else:  # 没有试用申请记录的（返回申请页面链接）　提示
                return Response({"code": 2, "share_link": self.share_link.format(1)})  # 和申请页面的链接
        res = self.get_promotion_result(customer.id, outer_id)
        return Response(res)

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


class InviteReletionshipView(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    """ 用户活动邀请粉丝列表 """
    queryset = XLReferalRelationship.objects.all()
    serializer_class = None
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def list(self, request, *args, **kwargs):
        return Response([])
