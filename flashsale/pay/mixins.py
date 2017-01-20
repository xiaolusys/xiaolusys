# coding=utf-8
import re
import urlparse

from django.conf import settings
from mall.xiaolupay import apis as xiaolupay

from rest_framework import exceptions

from . import constants
from .models import Customer, ShoppingCart, SaleTrade, SaleOrder, genTradeUniqueid
from flashsale.xiaolumm.models import XiaoluMama

from common.modelutils import update_model_fields

UUID_RE = re.compile('^[a-z]{2}[0-9]{6}[a-z0-9-]{10,14}$')


class PayInfoMethodMixin(object):
    """ 支付信息方法Mixin类 """

    def get_trade_uuid(self):
        return genTradeUniqueid()

    def is_from_weixin(self, request):
        if hasattr(self, '_isfromweixin'):
            return self._isfromweixin
        agent = request.META.get('HTTP_USER_AGENT', None)
        self._isfromweixin = False
        if agent and agent.find('MicroMessenger') > -1:
            self._isfromweixin = True
        return self._isfromweixin

    def get_user_profile(self, request):
        if hasattr(self, '_customer'):
            return self._customer
        self._customer = Customer.objects.normal_customer.filter(user=request.user).first()
        return self._customer

    def get_xiaolumm(self, request):
        if hasattr(self, '_xiaolumm'):
            return self._xiaolumm
        customer = self.get_user_profile(request)
        xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
        if xiaolumms.exists():
            self._xiaolumm = xiaolumms[0]
        else:
            self._xiaolumm = None
        return self._xiaolumm

    def calc_mama_discount_fee(self, product_sku, xlmm):
        return product_sku.calc_discount_fee(xlmm=xlmm)

    def calc_deposite_amount_params(self, request, product, **kwargs):
        """ 计算商品规格支付信息 """

        def get_payable_channel_params(customer, xlmm, is_deposite_order, total_payment):
            wallet_payable = False
            wallet_cash = 0
            xlmm = self.get_xiaolumm(request)
            if xlmm:
                wallet_payable = (xlmm.cash > 0 and
                                  total_payment >= 0 and
                                  xlmm.cash >= int(total_payment * 100) and
                                  not is_deposite_order)
                wallet_cash = xlmm.cash_money
            weixin_payable = False
            if customer.unionid:
                weixin_payable = self.is_from_weixin(request)
            return {'wallet_cash': wallet_cash,
                    'weixin_payable': weixin_payable,
                    'alipay_payable': True,
                    'wallet_payable': wallet_payable,
                    }

        product_sku = product
        total_fee = float(product_sku.agent_price) * 1
        post_fee = 0
        discount_fee = 0

        customer = self.get_user_profile(request)
        xlmm = self.get_xiaolumm(request)
        if xlmm:
            discount_fee = self.calc_mama_discount_fee(product_sku, xlmm)

        total_payment = total_fee + post_fee - discount_fee
        order_type = SaleTrade.SALE_ORDER
        is_deposite_order = False
        if product.is_deposite():
            order_type = SaleTrade.DEPOSITE_ORDER
            is_deposite_order = True

        payable_params = get_payable_channel_params(customer, xlmm, is_deposite_order, total_payment)
        payable_params.update({
            'order_type': order_type,
            'total_fee': round(total_fee, 2),
            'post_fee': round(post_fee, 2),
            'discount_fee': round(discount_fee, 2),
            'total_payment': round(total_payment, 2),
        })
        return payable_params

    def is_valid_uuid(self, uuid):
        return UUID_RE.match(uuid)

    def pingpp_charge(self, sale_trade, **kwargs):
        """ pingpp支付实现 """
        payment = int(sale_trade.payment * 100)
        buyer_openid = sale_trade.openid
        order_no = sale_trade.tid
        channel = sale_trade.channel
        if channel == SaleTrade.WX_PUB and not buyer_openid:
            raise ValueError(u'请先微信授权登陆后再使用微信支付')
        
        success_url = urlparse.urljoin(settings.M_SITE_URL,
                                       kwargs.get('success_url', constants.MALL_PAY_SUCCESS_URL))
        cancel_url = urlparse.urljoin(settings.M_SITE_URL,
                                      kwargs.get('cancel_url', constants.MALL_PAY_CANCEL_URL))
        extra = {}
        if channel == SaleTrade.WX_PUB:
            extra = {'open_id': buyer_openid, 'trade_type': 'JSAPI'}

        elif channel == SaleTrade.ALIPAY_WAP:
            extra = {"success_url": success_url,
                     "cancel_url": cancel_url}

        elif channel == SaleTrade.UPMP_WAP:
            extra = {"result_url": success_url}

        params = {'order_no': '%s' % order_no,
                  'app': dict(id=settings.PINGPP_APPID),
                  'channel': channel,
                  'currency': 'cny',
                  'amount': '%d' % payment,
                  'client_ip': settings.PINGPP_CLENTIP,
                  'subject': u'小鹿美美平台交易',
                  'body': u'订单ID(%s),订单金额(%.2f)' % (sale_trade.id, sale_trade.payment),
                  'metadata': dict(color='red'),
                  'extra': extra}
        charge = xiaolupay.Charge.create(**params)
        sale_trade.charge = charge.id
        update_model_fields(sale_trade, update_fields=['charge'])
        return charge

    def create_Saletrade(self, form, address, customer, order_type=SaleTrade.SALE_ORDER):
        """ 创建特卖订单方法 """
        tuuid = form.get('uuid')
        if not self.is_valid_uuid(tuuid):
            raise exceptions.APIException(u'订单UUID异常')
        sale_trade, state = SaleTrade.objects.get_or_create(
            tid=tuuid, buyer_id=customer.id)

        if sale_trade.status not in (SaleTrade.WAIT_BUYER_PAY,
                                     SaleTrade.TRADE_NO_CREATE_PAY):
            raise exceptions.APIException(u'订单不可支付')

        params = {'channel': form.get('channel')}
        if address:
            params.update({
                'receiver_name': address.receiver_name,
                'receiver_state': address.receiver_state,
                'receiver_city': address.receiver_city,
                'receiver_district': address.receiver_district,
                'receiver_address': address.receiver_address,
                'receiver_zip': address.receiver_zip,
                'receiver_phone': address.receiver_phone,
                'receiver_mobile': address.receiver_mobile,
            })

        if state:
            cart_ids = [i for i in form.get('cart_ids', '').split(',') if i.isdigit()]
            cart_qs = ShoppingCart.objects.filter(
                id__in=cart_ids,
                buyer_id=customer.id
            )

            is_boutique = False
            for cart in cart_qs:
                mp = cart.get_modelproduct()
                if mp and mp.is_boutique:
                    is_boutique = True
                if mp and mp.is_boutique_coupon:
                    order_type = SaleTrade.ELECTRONIC_GOODS_ORDER

            from shopapp.weixin.options import get_openid_by_unionid
            openid = get_openid_by_unionid(customer.unionid, settings.WX_PUB_APPID)
            params.update({
                'is_boutique': is_boutique,
                'order_type': order_type,
                'buyer_nick': customer.nick,
                'buyer_message': form.get('buyer_message', ''),
                'payment': float(form.get('payment')),
                'pay_cash': float(form.get('payment')),
                'total_fee': float(form.get('total_fee')),
                'post_fee': float(form.get('post_fee')),
                'discount_fee': float(form.get('discount_fee')),
                'charge': '',
                'status': SaleTrade.WAIT_BUYER_PAY,
                'openid': openid,
                'extras_info': {'mm_linkid': form.get('mm_linkid', '0'), 'ufrom': form.get('ufrom', '')
                                , 'wallet_renew_deposit': form.get('wallet_renew_deposit', '')}
            })
        for k, v in params.iteritems():
            hasattr(sale_trade, k) and setattr(sale_trade, k, v)
        sale_trade.save()
        return sale_trade, state

    def create_deposite_trade(self, form, address, customer):
        return self.create_Saletrade(form, address, customer, order_type=SaleTrade.DEPOSITE_ORDER)

    def create_SaleOrder_By_Productsku(self, saletrade, product, sku, num):
        """ 根据商品明细创建订单明细方法 """
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
            pic_path=product.pic_path,
            sku_name=sku.properties_alias,
            status=SaleTrade.WAIT_BUYER_PAY
        )
