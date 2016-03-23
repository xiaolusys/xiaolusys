# -*- coding:utf-8 -*-

import json
import datetime
import urllib
import urlparse
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.views.generic import View
from django.template import RequestContext
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework import exceptions

from core.weixin.mixins import WeixinAuthMixin

from flashsale.pay.options import get_user_unionid, valid_openid
from flashsale.pay.mixins import PayInfoMethodMixin
from flashsale.pay.models import Customer, SaleTrade, SaleOrder, Register
from shopback.items.models import ProductSku
from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.models import WeiXinUser
from shopback.items.models import Product

import logging

logger = logging.getLogger('django.request')
from flashsale.restpro.v2.views_verifycode_login import validate_mobile, \
    get_register, check_day_limit, should_resend_code, validate_code
from shopapp.smsmgr.tasks import task_register_code


class SendCode(APIView):
    """ 邀请的页面发送验证码 """
    def post(self, request):
        content = request.REQUEST
        mobile = content.get('mobile')
        if not validate_mobile(mobile):
            return Response({"code": 1, "message": u"手机号码有误！"})
        reg, created = get_register(mobile)
        if not created:
            if check_day_limit(reg):
                return Response({"code": 2, "message": u"当日验证次数超过限制!"})
            if not should_resend_code(reg):
                return Response({"code": 3, "message": u"验证码刚发过咯，请等待下哦！"})
        user = request.user
        customer = 0
        if user and user.is_authenticated():
            customer = Customer.objects.get(user=user)
        reg.cus_uid = customer.id if customer else 0
        reg.verify_code = reg.genValidCode()
        reg.code_time = datetime.datetime.now()
        reg.save()
        task_register_code.s(mobile, "3")()
        return Response({"code": 0, "message": u"验证码已发送！"})


class VerifyCode(APIView):
    def post(self, request):
        """
        邀请代理时候验证码校验
        注意：测试时候默认已经注册了unionid的Customer
        """
        content = request.REQUEST
        mobile = content.get("mobile", '')
        unionid = content.get('unionid', '')
        sms_code = content.get('sms_code', '')

        if not valid_openid(unionid):
            return Response({"code": 1, "message": u"请在微信打开此页面！"})
        if not validate_mobile(mobile):
            return Response({"code": 2, "message": u"手机号码有误！"})
        if not validate_code(mobile, sms_code):
            return Response({"rcode": 4, "msg": u"验证码不对或过期啦！"})
        return Response({'code': 0, 'message': u'验证成功！'})


class MamaRegisterView(WeixinAuthMixin, PayInfoMethodMixin, APIView):
    """ 小鹿妈妈申请成为代理 """
    authentication_classes = (authentication.SessionAuthentication, )
    # permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.TemplateHTMLRenderer, )
    template_name = "apply/step-1.html"

    def get(self, request, mama_id):
        """
        mama_id: 推荐人的专属id
        """
        # 加上装饰器之后已经登陆并注册状态（customer unionid）
        # 必须注册之后才可以成为小鹿代理　　这里使用特卖公众账号授权
        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)
        # 获取 openid 和 unionid
        openid, unionid = self.get_openid_and_unionid(request)
        if not valid_openid(openid) or not valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)
        customer = Customer.objects.get(user=request.user)
        customer_mobile = customer.mobile

        try:
            xiaolumm = XiaoluMama.objects.get(openid=unionid)
        except XiaoluMama.DoesNotExist:
            response = Response({
                'openid': openid,
                'unionid': unionid,
                'xiaolumm': None
            })
            self.set_cookie_openid_and_unionid(response, openid, unionid)
            return response

        except Exception, exc:
            logger.error(exc.message, exc_info=True)
            raise exc

        if xiaolumm.progress == XiaoluMama.NONE:  # 如果没有申请 返回填写资料页面
            response = Response({
                'openid': openid,
                'unionid': unionid,
                'xiaolumm': xiaolumm,
                'customer_mobile': customer_mobile
            })
            self.set_cookie_openid_and_unionid(response, openid, unionid)
            return response

        elif xiaolumm.need_pay_deposite():  # 如果没有已经申请没有支付押金的跳转到支付押金页面
            return redirect(reverse('mama_deposite', kwargs={'mama_id': mama_id}))

        else:  # 如果申请了并且交付的代理押金则直接跳转到代理的主页
            return redirect(reverse('mama_homepage'))

    def post(self, request, mama_id):
        # 验证码通过才可以进入本函数
        content = request.REQUEST
        mobile = content.get('mobile')
        user = request.user
        customers = Customer.objects.filter(user=user)

        if not customers.exists():  # 这个不可能存在
            return redirect('./')
        customer = customers[0]
        customer.mobile = mobile  # 保存用户的手机号码
        customer.save()

        xlmm, state = XiaoluMama.objects.get_or_create(openid=customer.unionid)
        parent_mobile = xlmm.referal_from  # 取出当前代理的推荐人
        if int(mama_id) > 0 and not parent_mobile:  # 如果推荐人存在并且当前的代理没有推荐人则把推荐人字段写到当前代理的推荐人字段
            parent_xlmm = XiaoluMama.objects.filter(id=mama_id)
            if parent_xlmm.exists():
                parent = parent_xlmm[0]
                parent_mobile = parent.mobile

        xlmm.progress = XiaoluMama.PROFILE
        xlmm.referal_from = parent_mobile
        xlmm.mobile = mobile
        xlmm.save()

        return redirect(reverse('mama_deposite', kwargs={'mama_id': mama_id}))


class PayDepositeView(PayInfoMethodMixin, APIView):
    """ 小鹿妈妈支付押金 """
    #     authentication_classes = (authentication.TokenAuthentication,)
    #     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    template_name = 'apply/step-2.html'

    def get_deposite_product(self):
        return Product.objects.get(id=2731)

    def get_full_link(self, link):
        return urlparse.urljoin(settings.M_SITE_URL, link)

    def get(self, request, mama_id):
        xlmm = self.get_xiaolumm(request)
        if not xlmm:
            return redirect(reverse('mama_register', kwargs={'mama_id': mama_id}))

        if mama_id == xlmm.id or not xlmm.need_pay_deposite():
            return redirect(reverse('mama_homepage'))

        product = self.get_deposite_product()
        deposite_params = self.calc_deposite_amount_params(request, product)
        return Response({
            'uuid': self.get_trade_uuid(),
            'xlmm': xlmm,
            'product': product,
            'payinfos': deposite_params,
            'referal_mamaid': mama_id,
            'success_url': self.get_full_link(reverse('mama_registerok')),
            'cancel_url': self.get_full_link(reverse('mama_registerfail') + '?mama_id=' + mama_id)
        })

    def post(self, request, *args, **kwargs):
        CONTENT = request.REQUEST.copy()
        item_id = CONTENT.get('item_id')
        sku_id = CONTENT.get('sku_id')
        sku_num = int(CONTENT.get('num', '1'))

        customer = get_object_or_404(Customer, user=request.user)
        product = get_object_or_404(Product, id=item_id)
        product_sku = get_object_or_404(ProductSku, id=sku_id)
        payment = int(float(CONTENT.get('payment', '0')) * 100)
        post_fee = int(float(CONTENT.get('post_fee', '0')) * 100)
        discount_fee = int(float(CONTENT.get('discount_fee', '0')) * 100)
        bn_totalfee = int(product_sku.agent_price * sku_num * 100)

        if product_sku.free_num < sku_num or product.shelf_status == Product.DOWN_SHELF:
            raise exceptions.ParseError(u'商品已被抢光啦！')

        bn_payment = bn_totalfee + post_fee - discount_fee
        if post_fee < 0 or payment <= 0 or abs(payment - bn_payment) > 10:
            raise exceptions.ParseError(u'付款金额异常')
        #         addr_id  = CONTENT.get('addr_id')
        #         address  = get_object_or_404(UserAddress,id=addr_id,cus_uid=customer.id)
        address = None
        channel = CONTENT.get('channel')
        if channel not in dict(SaleTrade.CHANNEL_CHOICES):
            raise exceptions.ParseError(u'付款方式有误')

        try:
            lock_success = Product.objects.lockQuantity(product_sku, sku_num)
            if not lock_success:
                raise exceptions.APIException(u'商品库存不足')
            sale_trade, state = self.create_deposite_trade(CONTENT, address, customer)
            if state:
                self.create_SaleOrder_By_Productsku(sale_trade, product, product_sku, sku_num)
        except exceptions.APIException, exc:
            raise exc

        except Exception, exc:
            logger.error(exc.message, exc_info=True)
            Product.objects.releaseLockQuantity(product_sku, sku_num)
            raise exceptions.APIException(u'订单生成异常')

        response_charge = self.pingpp_charge(sale_trade, **CONTENT)

        return Response(response_charge)


class MamaSuccessView(APIView):
    #     authentication_classes = (authentication.TokenAuthentication,)
    #     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "apply/mama_success.html"

    def get(self, request):
        response = {}
        return Response(response)


class MamaFailView(APIView):
    #     authentication_classes = (authentication.TokenAuthentication,)
    #     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "apply/mama_fail.html"

    def get(self, request):
        response = {'mama_id': request.REQUEST.get('mama_id')}
        return Response(response)

from .models_fortune import ReferalRelationship


class MamaInvitationRes(APIView):
    """
    代理邀请结果页面
    """
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "apply/mama_invitation_res.html"

    def get(self, request):
        """ app内展示 """

        user = request.user
        customer = Customer.objects.get(user=user)
        xlmm = customer.getXiaolumm()
        if not xlmm:
            return Response({"num_handred": 0, "num_ten": 0,
             'num_unit': 0})
        #
        # referals = XiaoluMama.objects.filter(referal_from=xlmm.mobile, charge_status=XiaoluMama.CHARGED)
        # referal_count = referals.count()
        referals = ReferalRelationship.objects.filter(referal_from_mama_id=xlmm.id)
        referal_count = referals.count()

        num_handred = referal_count/100
        num_ten = referal_count % 100 / 10
        num_unit = referal_count % 10

        response = Response(
            {"num_handred": num_handred, "num_ten": num_ten,
             'num_unit': num_unit, 'referals': referals, 'xlmm': xlmm})
        return response