# -*- coding:utf-8 -*-

import logging
import re
import urlparse
import json

from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.http import Http404
from django.core.exceptions import MultipleObjectsReturned

from rest_framework import authentication
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.views import APIView

from core.weixin.mixins import WeixinAuthMixin
from shopapp.weixin import options
from shopapp.weixin.models import WeiXinAccount
from flashsale.pay.mixins import PayInfoMethodMixin
from flashsale.pay.models import Customer, SaleTrade, SaleOrder, UserAddress
from flashsale.pay.models import ModelProduct
from flashsale.xiaolupay import apis as xiaolupay
from flashsale.restpro import constants as CONS

from ..models import BitVIP

logger = logging.getLogger(__name__)

UUID_RE = re.compile('^[a-z]{2}[0-9]{6}[a-z0-9-]{10,14}$')

class BitMallView(WeixinAuthMixin, APIView):
    """ 比特优品申请成为代理 """
    authentication_classes = (authentication.SessionAuthentication,)
    # permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "bitmall/step-1.html"

    def get(self, request):

        content = request.GET
        parent = content.get('parent')

        response = Response({
            'openid': None,
            'unionid': None,
            'xiaolumm': None,
            "parent_bid": parent
        })
        # self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response

class BitMallRegStatusView(WeixinAuthMixin, APIView):
    """ 比特优品申请成为代理 """
    authentication_classes = (authentication.SessionAuthentication,)
    # permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "bitmall/step-3.html"

    def get(self, request):

        content = request.GET
        order_no = content.get('order_no')

        response = Response({
            'order': SaleTrade.objects.get(tid=order_no),
        })
        # self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response

class BitMallRegisterView(WeixinAuthMixin, PayInfoMethodMixin, APIView):
    """ 比特优品申请成为代理 """
    authentication_classes = (authentication.SessionAuthentication,)
    # permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    template_name = "bitmall/step-2.html"
    APP_KEY = settings.WX_HGT_APPID


    def get_modelproduct(self):
        return ModelProduct.objects.get(id=26380)

    def get_product_info(self):
        p = self.get_modelproduct()
        return {
            'id': p.product.id,
            'name': p.name,
            'head_img': p.head_img_url,
            'price': p.lowest_agent_price,
            'num': 1,
            'sku_id': p.product.normal_skus.first().id
        }

    def get(self, request):

        self.set_appid_and_secret(self.APP_KEY, WeiXinAccount.get_wxpub_account_secret(self.APP_KEY))
        openid, unionid = self.get_openid_and_unionid(request)
        if not self.valid_openid(openid) or not self.valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)

        dj_user = authenticate(request=request, unionid=unionid, openid=openid)
        if not dj_user or dj_user.is_anonymous:
            raise Http404(u'授权用户信息不存在')

        login(request, dj_user)
        customer = Customer.objects.filter(user=dj_user, unionid=unionid).first()
        if not customer:
            customer, state = Customer.objects.get_or_create(user=dj_user, unionid=unionid)

        parent = request.GET.get(u'parent')
        parent = None
        if parent:
            parent = get_object_or_404(BitVIP, id=parent)

        bit_vip = BitVIP.objects.filter(user=dj_user).first()
        if not bit_vip:
            BitVIP.objects.create(
                user=dj_user,
                parent=parent
            )

        elif not bit_vip.parent:
            bit_vip.parent = parent
            bit_vip.save(update_fields=['parent'])

        params = {
            'order_no': SaleTrade.gen_unikey(),
            'customer': customer,
            'openid': openid,
            'unionid': unionid,
            'bit_vip': bit_vip,
        }

        # get activity product
        params['product'] = self.get_product_info()

        # generate pay info
        params.update({
            'channel': SaleTrade.WX_PUB
        })

        response = Response(params)
        self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response

    def create_saletrade(self, order_no, customer, address, **kwargs):

        sale_trade = SaleTrade.objects.create(
            tid=order_no,
            buyer_id=customer.id,
            order_type=SaleTrade.BITMALL_ORDER,
            user_address_id=address.id,
            buyer_nick=customer.nick,
            charge='',
            # 'logistics_company_id': None,
            status=SaleTrade.WAIT_BUYER_PAY,
            pay_status=SaleTrade.SALE_TRADE_PAYING,
            ** kwargs
        )

        return sale_trade

    def create_saleorder(self, saletrade, product, sku, num):
        total_fee = saletrade.total_fee
        rnow_payment = saletrade.payment - saletrade.post_fee
        discount_fee = saletrade.discount_fee
        SaleOrder.objects.create(
            sale_trade=saletrade,
            item_id=product.id,
            sku_id=sku.id,
            num=num,
            outer_id=product.outer_id,
            outer_sku_id=sku.outer_id,
            title=product.name,
            payment=rnow_payment,
            total_fee=total_fee,
            price=sku.agent_price,
            discount_fee=discount_fee,
            pic_path=sku.pic_path,
            sku_name=sku.properties_alias,
            status=SaleTrade.WAIT_BUYER_PAY
        )

    def get_or_create_address(self, customer, **kwargs):

        try:
            address, state = UserAddress.objects.get_or_create(
                cus_uid=customer.id,
                **kwargs
            )
        except MultipleObjectsReturned:
            addrs = UserAddress.objects.filter(
                cus_uid=customer.id,
                status=UserAddress.NORMAL,
                **kwargs
            )
            address = addrs.first()
            for addr in addrs[1:]:
                addr.default = False
                addr.status = UserAddress.DELETE
                addr.save(update_fields=['default', 'status'])

        if not address.default:
            address.default = True
            address.status = UserAddress.NORMAL
            address.save(update_fields=['default', 'status'])

        return address

    def pingpp_charge(self, sale_trade, **kwargs):
        """
        pingpp支付实现
        """

        payment = sale_trade.get_cash_payment()
        if payment <= 0:
            raise Exception(u'%s支付金额不能小于0' % sale_trade.get_channel_display().replace(u'支付', u''))

        order_no = sale_trade.tid
        channel = sale_trade.channel
        order_success_url = CONS.MALL_PAY_SUCCESS_URL.format(order_id=sale_trade.id, order_tid=sale_trade.tid)

        # app_id = settings.WX_HGT_APPID
        buyer_openid = sale_trade.openid

        payback_url = urlparse.urljoin(settings.M_SITE_URL, order_success_url)
        cancel_url = urlparse.urljoin(settings.M_SITE_URL, CONS.MALL_PAY_CANCEL_URL)

        extra = {}
        if channel in (SaleTrade.WX_PUB, SaleTrade.WEAPP):
            extra = {'open_id': buyer_openid, 'trade_type': 'JSAPI'}
        elif channel == SaleTrade.ALIPAY_WAP:
            extra = {"success_url": payback_url, "cancel_url": cancel_url}
        elif channel == SaleTrade.UPMP_WAP:
            extra = {"result_url": payback_url}

        params = {
            'order_no': '%s' % order_no,
            'app': dict(id=settings.PINGPP_APPID),
            'channel': channel,
            'currency': 'cny',
            'amount': '%d' % payment,
            'client_ip': settings.PINGPP_CLENTIP,
            'subject': u'小鹿美美平台交易',
            'body': u'用户订单金额[%s, %s, %.2f]' % (
                sale_trade.buyer_id,
                sale_trade.id,
                sale_trade.payment),
            'metadata': dict(color='red'),
            'extra': extra
        }

        charge = xiaolupay.Charge.create(**params)
        sale_trade.charge = charge.id
        sale_trade.save(update_fields=['charge'])
        return charge

    def post(self, request):
        try:
            self.set_appid_and_secret(self.APP_KEY, WeiXinAccount.get_wxpub_account_secret(self.APP_KEY))
            openid, unionid = self.get_openid_and_unionid(request)
            form = request.POST
            order_no = form.get('order_no')
            if not self.valid_openid(openid) or not self.valid_openid(unionid) or not UUID_RE.match(order_no):
                raise ValueError(u'非法请求参数')

            channel = form.get('channel')
            product_num = form.get('num')
            user    = request.user
            customer = Customer.objects.get(user=user)

            form   = request.POST
            fields = ['receiver_name', 'receiver_state', 'receiver_city', 'receiver_district', 'receiver_address', 'receiver_mobile']
            params = dict((k, form.get(k, '')) for k in fields)

            address = self.get_or_create_address(customer, **params)
            mp = self.get_modelproduct()

            params.update({
                'channel': channel,
                'payment': mp.lowest_agent_price,
                'pay_cash': mp.lowest_agent_price,
                'has_budget_paid': False,
                'budget_paid': 0,
                'has_coin_paid': False,
                'coin_paid': 0,
                'total_fee': mp.lowest_agent_price,
                'post_fee': 0,
                'discount_fee': 0,
                'openid': openid,
                'extras_info': {
                    'agent': request.META.get('HTTP_USER_AGENT'),
                    'unionid': unionid
                }
            })

            strade = self.create_saletrade(order_no, customer, address, **params)
            self.create_saleorder(strade, mp.product, mp.product.normal_skus.first(), product_num)

            response = self.pingpp_charge(strade)

        except Exception, exc:
            response = {'code': 1, 'message': exc.message}

        return Response(response, content_type="application/json")