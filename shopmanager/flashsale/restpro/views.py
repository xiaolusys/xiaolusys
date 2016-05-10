# -*- coding:utf8 -*-
import logging
import hashlib
import os, urlparse
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from flashsale.apprelease.models import AppRelease
from .views_refund import refund_Handler

from flashsale.pay.models import SaleTrade, Customer

from . import permissions as perms
from . import serializers

from flashsale.pay.models import SaleRefund, District, UserAddress, SaleOrder
from flashsale.xiaolumm.models import XiaoluMama
from django.forms import model_to_dict
import json

from qiniu import Auth

logger = logging.getLogger(__name__)


class SaleRefundViewSet(viewsets.ModelViewSet):
    """
    ### 退款API:
    - {prefix}/method: get 获取用户的退款单列表
    - {prefix}/method: post 创建用户的退款单
        -  创建退款单
        >`id`:sale order id
        > `reason`:退货原因
        > `num`:退货数量
        > `sum_price` 申请金额
        > `description`: 申请描述
        > `proof_pic`: 佐证图片（字符串格式网址链接，多个使用＇，＇隔开）
        -  修改退款单
        > `id`: sale order id
        > `modify`:   1
        > `reason`:   退货原因
        > `num`:  退货数量
        > `sum_price`:    申请金额
        > `description`:  申请描述
        -  添加退款单物流信息
        > `id`:   sale order id
        > `modify`:   2
        > `company`:  物流公司
        > `sid`:  物流单号
        -  修改数量获取退款金额
        > `id`: sale order id
        > `modify`:   3
        > `num`:  退货数量
        > `:return`:apply_fee 申请金额
    - {prefix}/{{ order_id }}/get_by_order_id/method:get  根据订单id 获取指定的退款单
        -  返回
        > `feedback`:  驳回原因
        > `id`: id
        > `buyer_id`: 用户id
        > `reason`: 买家申请原因
    - {prefix}/qiniu_token: get 获取用户的退款单列表
    """
    queryset = SaleRefund.objects.all()
    serializer_class = serializers.SaleRefundSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(buyer_id=customer.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.order_by('created')[::-1]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        content = request.REQUEST
        oid = int(content.get("id", 0))
        order = get_object_or_404(SaleOrder, id=oid)
        # 如果Order已经付款 refund_type = BUYER_NOT_RECEIVED
        # 如果Order 仅仅签收状态才可以退货  refund_type = BUYER_RECEIVED
        second_kill = order.second_kill_title()
        if second_kill:
            raise exceptions.APIException(u'秒杀商品暂不支持退单，请见谅！')
        elif order.status not in (SaleOrder.TRADE_BUYER_SIGNED, SaleOrder.WAIT_SELLER_SEND_GOODS):
            raise exceptions.APIException(u'订单状态不予退款或退货')

        res = refund_Handler(request)
        return Response(res)

    @detail_route(methods=["get"])
    def get_by_order_id(self, request, pk=None):
        order_id = pk  # 获取order_id
        queryset = self.filter_queryset(self.get_owner_queryset(request)).filter(order_id=order_id)
        refund_dic = {}
        if queryset.exists():
            sale_refund = queryset[0]
            refund_dic = model_to_dict(sale_refund, fields=["id", "feedback", "buyer_id", "reason"])
        return Response(refund_dic)

    @list_route(methods=["get"])
    def qiniu_token(self, request, **kwargs):
        q = Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)
        token = q.upload_token("xiaolumm", expires=3600)
        return Response({'uptoken': token})


class UserAddressViewSet(viewsets.ModelViewSet):
    """
    - author： kaineng .fang  2015-8--
    - 方法及其目的
        - /{id}/delete_address（）：删除某个地址 （post  方法)
        - /{id}/change_default：选择收获地址  (post方法）   更改默认地址
        - /create_address：创建新的收获地址（post方法）
            ```
            data: {
                "receiver_state": receiver_state,
                "receiver_city": receiver_city,
                "receiver_district": receiver_district,
                "receiver_address": receiver_address,
                "receiver_name": receiver_name,
                "receiver_mobile": receiver_mobile,
            }
            ```
        - /get_one_addres： 得到要修改的那一个地址的信息（get请求） data{"id":}
        - /{id}/update: 修改地址（post）
            ```
            data: {
                id：id
                "receiver_state": receiver_state,
                "receiver_city": receiver_city,
                "receiver_district": receiver_district,
                "receiver_address": receiver_address,
                "receiver_name": receiver_name,
                "receiver_mobile": receiver_mobile,
            }
            ```
    """
    queryset = UserAddress.objects.all()
    serializer_class = serializers.UserAddressSerializer  # Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(cus_uid=customer.id, status=UserAddress.NORMAL).order_by('-default')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # fang kaineng  2015-7-31

    @detail_route(methods=['post'])
    def update(self, request, pk, *args, **kwargs):
        customer = get_object_or_404(Customer, user=request.user)
        content = request.REQUEST
        receiver_state = content.get('receiver_state', '').strip()
        receiver_city = content.get('receiver_city', '').strip()
        receiver_district = content.get('receiver_district', '').strip()
        receiver_address = content.get('receiver_address', '').strip()
        receiver_name = content.get('receiver_name', '').strip()
        receiver_mobile = content.get('receiver_mobile', '').strip()
        default = content.get('default') or ''
        if default == 'true':
            default = True
        else:
            default = False
        try:
            new_address, state = UserAddress.objects.get_or_create(
                cus_uid=customer.id,
                receiver_name=receiver_name,
                receiver_state=receiver_state,
                receiver_city=receiver_city,
                receiver_district=receiver_district,
                receiver_address=receiver_address,
                receiver_mobile=receiver_mobile
            )
            if state:  # 创建成功在将原来的地址改为删除状态 (保留地址)
                new_address.default = UserAddress.objects.get(pk=pk).default  # 赋值原来的默认地址选择
                UserAddress.objects.filter(pk=pk).update(status=UserAddress.DELETE)
            else:  # 如果找到了一模一样的  更新该地址 到 正常状态
                UserAddress.objects.filter(pk=new_address.id).update(status=UserAddress.NORMAL)
            if default:  # 选择为默认地址
                new_address.set_default_address()  # 如果是选择设置默认地址则设置默认地址
            return Response({'ret': True, 'code': 0, 'info': '更新成功', "msg": '更新成功'})
        except:
            return Response({'ret': False, 'code': 1, 'info': '更新失败', "msg": '更新失败'})

    @detail_route(methods=["post"])
    def delete_address(self, request, pk=None):
        try:
            instance = self.get_object()
            instance.status = UserAddress.DELETE
            instance.save()
            return Response({'ret': True, "msg": "删除成功", "code": 0})
        except:
            return Response({'ret': False, "msg": "删除出错", "code": 1})

    '''
    @detail_route(methods=['post'])
    def change_default(self, request, pk=None):
        id_default = pk
        result = {}
        try:
            customer = get_object_or_404(Customer, user=request.user)
            addr = UserAddress.normal_objects.get(cus_uid=customer.id, id=id_default)
            res = addr.set_default_address()  # 设置默认地址
            result['ret'] = res
        except:
            result['ret'] = False
        return Response(result)
    '''

    @detail_route(methods=['post'])
    def change_default(self, request, pk=None):
        id_default = pk
        result = {}
        try:
            customer = get_object_or_404(Customer, user=request.user)
            addr = UserAddress.normal_objects.get(cus_uid=customer.id, id=id_default)
            if addr.status == UserAddress.DELETE:
                addr = UserAddress.objects.order_by('-modified')[0]
                res = addr.set_default_address()
            else:
                res = addr.set_default_address()  # 设置默认地址
            result['ret'] = res
        except:
            result['ret'] = False
        return Response(result)

    @list_route(methods=['post'])
    def create_address(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        customer_id = customer.id  # 获取用户id
        content = request.REQUEST
        default = content.get('default') or ''
        receiver_state = content.get('receiver_state', '').strip()
        receiver_city = content.get('receiver_city', '').strip()
        receiver_district = content.get('receiver_district', '').strip()
        receiver_address = content.get('receiver_address', '').strip()
        receiver_name = content.get('receiver_name', '').strip()
        receiver_mobile = content.get('receiver_mobile', '').strip()
        try:
            address, state = UserAddress.objects.get_or_create(cus_uid=customer_id, receiver_name=receiver_name,
                                                               receiver_state=receiver_state, default=False,
                                                               receiver_city=receiver_city,
                                                               receiver_district=receiver_district,
                                                               receiver_address=receiver_address,
                                                               receiver_mobile=receiver_mobile)
            if default == 'true':  # 设置为默认地址
                address.set_default_address()
            result = {'ret': True, "msg": "添加成功", 'code': 0}
        except:
            result = {'ret': False, "msg": "添加出错", "code": 1}
        return Response(result)

    @list_route(methods=['get'])
    def get_one_address(self, request):
        id = request.GET.get("id")
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        qs = queryset.filter(id=id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


from rest_framework_extensions.cache.decorators import cache_response


class DistrictViewSet(viewsets.ModelViewSet):
    """
    #### 地理区域信息接口及参数：
    -   /province_list：省列表
    -   /city_list：根据省获得市
    >  id:即province ID
    -   /country_list:根据市获得区或者县
    >  id:即country ID
    """
    queryset = District.objects.all()
    serializer_class = serializers.DistrictSerializer  # Create your views here.
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def calc_distirct_cache_key(self, view_instance, view_method,
                                request, args, kwargs):
        key_vals = ['id']
        key_maps = kwargs or {}
        for k, v in request.GET.copy().iteritems():
            if k in key_vals and v.strip():
                key_maps[k] = v

        return hashlib.sha256(u'.'.join([
            view_instance.__module__,
            view_instance.__class__.__name__,
            view_method.__name__,
            json.dumps(key_maps, sort_keys=True).encode('utf-8')
        ])).hexdigest()

    @cache_response(timeout=24 * 60 * 60, key_func='calc_distirct_cache_key')
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @cache_response(timeout=24 * 60 * 60, key_func='calc_distirct_cache_key')
    @list_route(methods=['get'])
    def province_list(self, request, *args, **kwargs):
        queryset = District.objects.filter(grade=1)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @cache_response(timeout=24 * 60 * 60, key_func='calc_distirct_cache_key')
    @list_route(methods=['get'])
    def city_list(self, request, *args, **kwargs):
        content = request.REQUEST
        province_id = content.get('id', None)
        if province_id == u'0':
            return Response({"result": False})
        else:
            queryset = District.objects.filter(parent_id=province_id)
            serializer = self.get_serializer(queryset, many=True)
            return Response({"result": True, "data": serializer.data})

    @cache_response(timeout=24 * 60 * 60, key_func='calc_distirct_cache_key')
    @list_route(methods=['get'])
    def country_list(self, request, *args, **kwargs):
        content = request.REQUEST
        city_id = content.get('id', None)
        if city_id == u'0':
            return Response({"result": False})
        else:
            queryset = District.objects.filter(parent_id=city_id)
            serializer = self.get_serializer(queryset, many=True)
            return Response({"result": True, "data": serializer.data})


from core.weixin.mixins import WeixinAuthMixin


class AppDownloadLinkViewSet(WeixinAuthMixin, viewsets.ModelViewSet):
    """
    获取有效App下载地址
    """
    queryset = AppRelease.objects.all()
    serializer_class = serializers.DistrictSerializer
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def get_app_download_link(self, request):
        """ 返回有效的app下载地址 """
        cotent = request.REQUEST
        mm_linkid = cotent.get('mm_linkid') or None
        if mm_linkid is None:
            cookies = request.COOKIES
            mm_linkid = cookies.get("mm_linkid")
        download_url = urlparse.urljoin(settings.M_SITE_URL, 'sale/promotion/appdownload/')  # 如果没有找到
        if mm_linkid is None:
            return Response({'download_url': download_url})
        else:  # 有推荐代理的情况才记录
            from_customer = None
            try:
                xlmms = XiaoluMama.objects.filter(pk=mm_linkid, status=XiaoluMama.EFFECT,
                                                  charge_status=XiaoluMama.CHARGED)
                if xlmms.exists():
                    xlmm = xlmms[0]
                    from_customer = Customer.objects.get(unionid=xlmm.openid)
            except:
                return Response({'download_url': download_url})
            # 带上参数跳转到下载页面
            if from_customer:
                download_url = urlparse.urljoin(settings.M_SITE_URL,
                                                'sale/promotion/appdownload/?from_customer={0}'.format(
                                                    from_customer.id))
            return Response({'download_url': download_url})
