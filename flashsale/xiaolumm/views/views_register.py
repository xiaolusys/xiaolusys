# -*- coding:utf-8 -*-

import logging
import re
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.views import APIView

from core.weixin.mixins import WeixinAuthMixin
from flashsale.pay.mixins import PayInfoMethodMixin
from flashsale.pay.models import Customer, SaleTrade
from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.options import get_openid_by_unionid
from shopback.items.models import Product
from flashsale.pay.models import ProductSku

logger = logging.getLogger(__name__)


class MamaRegisterView(WeixinAuthMixin, PayInfoMethodMixin, APIView):
    """ 小鹿妈妈申请成为代理 """
    authentication_classes = (authentication.SessionAuthentication,)
    # permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "apply/step-1.html"

    def get(self, request):
        """
        mama_id: 推荐人的专属id
        """
        content = request.GET
        mama_id = content.get('mama_id')
        mama_id = re.match("\d+",mama_id).group()
        
        deposite_url = "/m/register/deposite/?mama_id={0}".format(mama_id)
        # 加上装饰器之后已经登陆并注册状态（customer unionid）
        # 必须注册之后才可以成为小鹿代理　　这里使用特卖公众账号授权
        self.set_appid_and_secret(settings.WX_PUB_APPID, settings.WX_PUB_APPSECRET)
        # 获取 openid 和 unionid
        # openid, unionid = self.get_openid_and_unionid(request)
        customer = Customer.objects.get(user=request.user)
        unionid = customer.unionid
        openid  = get_openid_by_unionid(unionid, settings.WX_PUB_APPID)

        logger.info('mama register：%s,%s,%s' % (customer, openid, unionid))
        # if not valid_openid(openid) or not valid_openid(unionid):
        #     redirect_url = self.get_snsuserinfo_redirct_url(request)
        #     return redirect(redirect_url)
        customer_mobile = customer.mobile
        referal = XiaoluMama.objects.filter(id=mama_id).first()
        referal_from = referal.mobile if referal else ''  # 如果推荐人存在则
        if customer_mobile:  # 如果用户存在手机号码
            xlmm = XiaoluMama.objects.filter(openid=unionid).first()
            if xlmm:  # 存在则保存当前登陆用户的手机号码到当前小鹿妈妈的手机号字段
                xlmm.mobile = customer_mobile
                xlmm.save(update_fields=['mobile'])
            else:  # 否则创建当前用户的小鹿妈妈账号 并且是填写资料后状态
                XiaoluMama.objects.create(mobile=customer_mobile,
                                          referal_from=referal_from,
                                          progress=XiaoluMama.PROFILE,
                                          openid=unionid)

        try:
            xiaolumm = XiaoluMama.objects.get(openid=unionid)
        except XiaoluMama.DoesNotExist:
            response = Response({
                'openid': openid,
                'unionid': unionid,
                'xiaolumm': None,
                "mama_id": mama_id
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
                'customer_mobile': customer_mobile,
                "mama_id": mama_id
            })
            self.set_cookie_openid_and_unionid(response, openid, unionid)
            return response

        elif xiaolumm.need_pay_deposite():  # 如果没有已经申请没有支付押金的跳转到支付押金页面
            return redirect(deposite_url)

        else:  # 如果申请了并且交付的代理押金则直接跳转到下载app页面
            download_url = '/sale/promotion/appdownload/'
            return redirect(download_url)

    def post(self, request):
        # 验证码通过才可以进入本函数
        content = request.POST
        mobile = content.get('mobile')
        user = request.user
        customers = Customer.objects.filter(user=user)
        if not customers.exists():  # 这个不可能存在
            return redirect('./')

        customer = customers.first()
        mama_id = content.get('mama_id', 1)
        if customer.mobile:  # 如果用户的手机号码存在
            # 比较提交的号码与当前用户的号码是否一致
            if customer.mobile != mobile:
                logger.warn(u'代理提交资料时,号码与客户列表号码不一致 %s'%customer.id)
        else:  # 没有手机号
            customer.mobile = mobile  # 保存用户的手机号码
            customer.save()
        if not customer.unionid:
            logger.warn(u'邀请代理:用户没有uninoid %s'%customer.id)

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
        deposite_url = "/m/register/deposite/?mama_id={0}".format(mama_id)
        return redirect(deposite_url)


class PayDepositeView(PayInfoMethodMixin, APIView):
    """ 小鹿妈妈支付押金 """
    authentication_classes = (authentication.SessionAuthentication,)
    # permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    template_name = 'apply/step-2.html'

    def get_deposite_product(self):
        return Product.objects.get(id=2731)

    def get_full_link(self, link):
        return urlparse.urljoin(settings.M_SITE_URL, link)

    def get(self, request):
        content = request.GET
        mama_id = content.get('mama_id', '1')
        xlmm = self.get_xiaolumm(request)
        register_url = "/m/register/?mama_id={0}".format(mama_id)
        if not xlmm or xlmm.progress == XiaoluMama.NONE:  # 为申请或者没有填写资料跳转到邀请函页面
            return redirect(register_url)

        if mama_id == xlmm.id or not xlmm.need_pay_deposite():
            download_url = '/sale/promotion/appdownload/'
            return redirect(download_url)

        product = self.get_deposite_product()
        sku_188 = product.normal_skus.filter(outer_id='1').first()
        sku_id = sku_188.id
        deposite_params = self.calc_deposite_amount_params(request, sku_188)
        return Response({
            'uuid': self.get_trade_uuid(),
            'xlmm': xlmm,
            'product': product,
            'sku_id': sku_id,
            'payinfos': deposite_params,
            'referal_mamaid': mama_id,
            'success_url': self.get_full_link(reverse('mama_registerok')),
            'cancel_url': self.get_full_link(reverse('mama_registerfail') + '?mama_id=' + mama_id)
        })

    def post(self, request, *args, **kwargs):
        CONTENT = request.POST.copy()
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
        # addr_id  = CONTENT.get('addr_id')
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
    authentication_classes = (authentication.SessionAuthentication,)
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
        response = {'mama_id': request.GET.get('mama_id')}
        return Response(response)


from flashsale.xiaolumm.models.models_fortune import ReferalRelationship


class MamaInvitationRes(APIView):
    """
    代理邀请结果页面
    """
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "apply/step-4.html"

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

        num_handred = referal_count / 100
        num_ten = referal_count % 100 / 10
        num_unit = referal_count % 10
        agencylevel = xlmm.agencylevel
        response = Response(
            {"num_handred": num_handred, "num_ten": num_ten, "agencylevel": agencylevel,
             'num_unit': num_unit, 'referals': referals, 'xlmm': xlmm})
        return response
