# coding=utf-8
from __future__ import unicode_literals
import re
import time
import datetime
import urlparse
import decimal

from django.db import models, transaction, IntegrityError
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import transaction

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from flashsale.pay.apis.v1.order import get_user_skunum_by_last24hours
from flashsale.pay.models import (
    SaleTrade,
    SaleOrder,
    Customer,
    UserBudget,
    BudgetLog,
    ShoppingCart,
    UserAddress,
    gen_uuid_trade_tid,
    TeamBuy
)
from flashsale.coupon.models import UserCoupon
from flashsale.restpro import permissions as perms
from .. import serializers
from shopback.items.models import Product, ProductSku
from shopback.base import log_action, ADDITION, CHANGE
from shopback.logistics.models import LogisticsCompany
from shopapp.weixin import options
from common.utils import update_model_fields
from flashsale.restpro import constants as CONS

from flashsale.xiaolumm.models import XiaoluMama,CarryLog
from flashsale.pay.tasks import confirmTradeChargeTask, notifyTradePayTask, tasks_set_address_priority_logistics_code
from mall.xiaolupay import apis as xiaolupay

import logging
logger = logging.getLogger(__name__)


UUID_RE = re.compile('^[a-z]{2}[0-9]{6}[a-z0-9-]{10,14}$')

def is_from_weixin(request):
    user_agent = request.META.get('HTTP_USER_AGENT')
    if user_agent and re.search('MicroMessenger', user_agent, re.IGNORECASE):
        return True
    return False

def get_channel_list(request, customer):
    content = request.GET
    is_in_weixin = is_from_weixin(request)
    is_in_wap = content.get('device', 'wap') == 'wap'
    channel_list = []
    if is_in_wap:
        if is_in_weixin and customer.unionid:
            channel_list.append({'id': 'wx_pub', 'name': u'微信支付', 'payable': True, 'msg': ''})
        channel_list.append({'id': 'alipay_wap', 'name': u'支付宝', 'payable': True, 'msg': ''})
    else:
        channel_list.append({'id': 'wx', 'name': u'微信支付', 'payable': True, 'msg': ''})
        channel_list.append({'id': 'alipay', 'name': u'支付宝', 'payable': True, 'msg': ''})
    return channel_list

class SaleTradeViewSet(viewsets.ModelViewSet):
    """
    ###特卖订单REST API接口：
    - payment (实付金额) = total_fee (商品总金额) + post_fee (邮费) - discount_fee (优惠金额)
    - {path}/waitpay[.formt]:获取待支付订单；
    - {path}/waitsend[.formt]:获取待发货订单；
    - {path}/confirm_sign[.formt]: 确认收货;
    - {path}/remind_send[.formt]: 提醒发货;
    - {path}/undisplay[.formt]: 删除订单记录;
    - {path}/{pk}: 获取订单详情, 请传入参数 device :支付类型 (app ,app支付), (wap, wap支付), (web, 网页支付);
    - {path}/{pk}/charge[.formt]:支付待支付订单,可传入支付方式: channel;
    - {path}/shoppingcart_create[.formt]:pingpp创建订单接口
    > - cart_ids：购物车明细ID，如 `100,101,...`
    > - addr_id:客户地址ID
    > - channel:支付方式
    > - payment：付款金额
    > - post_fee：快递费用
    > - discount_fee：优惠折扣
    > - total_fee：总费用
    > - pay_extras：附加支付参数，eg. pid:2:couponid:226026:value:10.0;pid:1:value:2.0;pid:3:budget:37.9;
    > - uuid：系统分配唯一ID
    > - logistics_company_id: 快递公司id
    > - 返回结果：{'code':0,'info':'ok','charge':{...}},请求成功code=0,失败code大于0,错误信息info
    - {path}/buynow_create[.formt]:立即支付订单接口
    > - item_id：商品ID，如 `100,101,...`
    > - sku_id:规格ID
    > - num:购买数量
    > - pay_extras：附加支付参数，eg. pid:2:couponid:226026:value:10.0;pid:1:value:2.0;pid:3:budget:37.9;
    > - logistics_company_id: 快递公司id
    > - 其它参数(不包含cart_ids)如上
    """
    queryset = SaleTrade.objects.all()
    serializer_class = serializers.SaleTradeSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)

    filter_fields = ('tid',)
    paginate_by = 15
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    def get_owner_queryset(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        return self.queryset.filter(buyer_id=customer.id).order_by('-created')

    def get_customer(self, request):
        if not hasattr(self, '__customer__'):
            self.__customer__ = Customer.objects.filter(user=request.user).exclude(status=Customer.DELETE).first()
        return self.__customer__

    def get_xlmm(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        if not customer.unionid.strip():
            return None
        xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
        return xiaolumms.count() > 0 and xiaolumms[0] or None

    def list(self, request, *args, **kwargs):
        """ 获取用户订单列表 """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """ 获取用户订单及订单明细列表 """
        instance   = self.get_object()
        is_paid    = instance.is_paid
        if instance.is_payable() and instance.charge:
            try:
                charge = xiaolupay.Charge.retrieve(instance.tid)
                if charge and charge.paid:
                    is_paid = True
                    notifyTradePayTask.delay(charge)
            except Exception,exc:
                logger.error('%s'%exc, exc_info=True)

        data = serializers.SaleTradeDetailSerializer(instance, context={'request': request, 'is_paid': is_paid}).data
        data['extras'].update(channels=get_channel_list(request, self.get_customer(request)))
        return Response(data)

    @list_route(methods=['get'])
    def waitpay(self, request, *args, **kwargs):
        """ 获取用户待支付订单列表 """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.filter(status=SaleTrade.WAIT_BUYER_PAY)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def waitsend(self, request, *args, **kwargs):
        """ 获取用户待发货订单列表 """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.filter(status__in=(SaleTrade.WAIT_SELLER_SEND_GOODS,
                                               SaleTrade.WAIT_BUYER_CONFIRM_GOODS))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def check_before_charge(self, sale_trade):
        """ 支付前参数检查,如优惠券状态检查 """
        coupon_ids = sale_trade.extras_info.get('coupon', [])
        for coupon_id in coupon_ids:
            user_coupon = UserCoupon.objects.get(id=coupon_id, customer_id=sale_trade.buyer_id)
            if sale_trade.tid != user_coupon.trade_tid:
                user_coupon.coupon_basic_check()  # 优惠券基础检查

    def wallet_charge(self, sale_trade, check_coupon=True,  **kwargs):
        """ 妈妈钱包支付实现 """
        if check_coupon:
            self.check_before_charge(sale_trade)

        buyer         = Customer.objects.get(pk=sale_trade.buyer_id)
        payment       = round(sale_trade.payment * 100)
        buyer_unionid = buyer.unionid
        strade_id     = sale_trade.id
        buyer_nick    = sale_trade.buyer_nick
        channel       = sale_trade.channel

        xlmm = XiaoluMama.objects.get(openid=buyer_unionid)
        urows = XiaoluMama.objects.filter(
            openid=buyer_unionid,
            cash__gte=payment
        ).update(cash=models.F('cash') - payment)
        logger.info('wallet charge:saletrade=%s, updaterows=%d'%(sale_trade, urows))
        if urows == 0 :
            raise Exception(u'妈妈钱包余额不足')

        CarryLog.objects.create(xlmm=xlmm.id,
                                order_num=strade_id,
                                buyer_nick=buyer_nick,
                                value=payment,
                                log_type=CarryLog.ORDER_BUY,
                                carry_type=CarryLog.CARRY_OUT)
        #确认付款后保存
        confirmTradeChargeTask.delay(strade_id)
        return {'channel':channel,'success':True,'id':sale_trade.id,'info':'订单支付成功', 'from_page': 'order_commit'}

    def budget_charge(self, sale_trade, check_coupon=True, **kwargs):
        """
        小鹿钱包支付实现
        """
        with transaction.atomic():
            buyer = Customer.objects.select_for_update().get(pk=sale_trade.buyer_id)
            if check_coupon:
                self.check_before_charge(sale_trade)

            payment = round(sale_trade.payment * 100)
            strade_id = sale_trade.id
            channel = sale_trade.channel

            if payment > 0:
                user_budget = UserBudget.objects.filter(user=buyer, amount__gte=payment).first()
                if not user_budget:
                    raise Exception(u'小鹿钱包余额不足')
                try:
                    BudgetLog.objects.create(
                        customer_id=buyer.id,
                        referal_id=strade_id,
                        flow_amount=payment,
                        budget_log_type=BudgetLog.BG_CONSUM,
                        budget_type=BudgetLog.BUDGET_OUT,
                        status=BudgetLog.CONFIRMED,
                        uni_key='st_%s'%sale_trade.id
                    )
                except IntegrityError, exc:
                    logger.error(str(exc), exc_info=True)

        # 确认付款后保存
        confirmTradeChargeTask(strade_id)

        if sale_trade.order_type == SaleTrade.TEAMBUY_ORDER:
            success_url = CONS.TEAMBUY_SUCCESS_URL.format(order_tid=sale_trade.tid) + '?from_page=order_commit'
        else:
            success_url = CONS.MALL_PAY_SUCCESS_URL.format(order_id=sale_trade.id, order_tid=sale_trade.tid)
            success_url += '?from_page=order_commit'

        return {
            'channel': channel,
            'success': True,
            'id': sale_trade.id,
            'info': u'订单支付成功',
            'order_no': sale_trade.tid,
            'success_url': success_url,
            'fail_url': CONS.MALL_PAY_CANCEL_URL,
            'type': sale_trade.order_type
        }

    def pingpp_charge(self, sale_trade, check_coupon=True, **kwargs):
        """
        pingpp支付实现
        """
        if check_coupon:
            self.check_before_charge(sale_trade)

        payment = sale_trade.get_cash_payment()

        if payment <= 0:
            raise Exception(u'%s支付金额不能小于0' % sale_trade.get_channel_display().replace(u'支付', u''))

        order_no = sale_trade.tid
        buyer_openid = sale_trade.openid
        channel = sale_trade.channel
        order_success_url = CONS.MALL_PAY_SUCCESS_URL.format(order_id=sale_trade.id, order_tid=sale_trade.tid)

        if channel == SaleTrade.WX_PUB and not buyer_openid:
            raise ValueError(u'请先微信授权登陆后再使用微信支付')

        if sale_trade.order_type == SaleTrade.TEAMBUY_ORDER:
            order_success_url = CONS.TEAMBUY_SUCCESS_URL.format(order_tid=sale_trade.tid) + '?from_page=order_commit'

        payback_url = urlparse.urljoin(settings.M_SITE_URL, order_success_url)
        cancel_url = urlparse.urljoin(settings.M_SITE_URL, CONS.MALL_PAY_CANCEL_URL)

        if sale_trade.has_budget_paid:
            with transaction.atomic():
                ubudget = UserBudget.objects.get(user=sale_trade.buyer_id)
                budget_charge_create = ubudget.charge_pending(sale_trade.id, sale_trade.budget_payment)
                if not budget_charge_create:
                    logger.error('budget payment err:tid=%s, payment=%s, budget_payment=%s' % (
                        sale_trade.tid, sale_trade.payment, sale_trade.budget_payment))
                    raise Exception(u'钱包余额不足')

        extra = {}
        if channel == SaleTrade.WX_PUB:
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
        update_model_fields(sale_trade, update_fields=['charge'])
        return charge

    def get_mama_referal_params(self, request):
        form = request.data
        mama_linkid = form.get('mm_linkid', None)
        ufrom = form.get('ufrom', '0')
        if not mama_linkid:
            cookies = request.COOKIES
            mama_linkid = cookies.get('mm_linkid', 0)
            ufrom = cookies.get('ufrom', '')
        # 由于老版本原因，可能mmlinkdid传的是null或undefined，那么需要容错
        import types
        if (type(mama_linkid) is types.StringType) and (not mama_linkid.isdigit()):
            mama_linkid = 0
        return {'mm_linkid': mama_linkid, 'ufrom': ufrom}

    def create_Saletrade(self, request, form, address, customer, order_type=SaleTrade.SALE_ORDER):
        """
        创建特卖订单方法
        """
        tuuid = form.get('uuid')
        assert UUID_RE.match(tuuid), u'订单UUID异常'
        # lock on customer record
        customer = Customer.objects.select_for_update().get(id=customer.id)
        sale_trade = SaleTrade.objects.filter(tid=tuuid).first()
        if sale_trade and sale_trade.buyer_id != customer.id:
            raise Exception(u'该订单号被重用: %s'%request.POST.dict())

        if sale_trade:
            return sale_trade, False

        sale_trade = SaleTrade(tid=tuuid, buyer_id=customer.id)
        channel = form.get('channel')

        is_boutique = False
        cart_ids = form.get('cart_ids', '')
        if cart_ids:
            cart_ids = [i for i in cart_ids.split(',') if i.isdigit()]
            cart_qs = ShoppingCart.objects.filter(
                id__in=cart_ids,
                buyer_id=customer.id
            )

            if cart_qs.count() == 1 and cart_qs[0].type == ShoppingCart.TEAMBUY:
                order_type = SaleTrade.TEAMBUY_ORDER

            # 　设置订单精品汇参数

            for cart in cart_qs:
                mp = cart.get_modelproduct()
                if mp and mp.is_boutique:
                    is_boutique = True
                if mp and mp.is_boutique_coupon:
                    order_type = SaleTrade.ELECTRONIC_GOODS_ORDER

        item_id = form.get('item_id')
        if item_id:
            mp = Product.objects.get(id=item_id).product_model
            if mp and mp.is_boutique:
                is_boutique = True
            if mp and mp.is_boutique_coupon:
                order_type = SaleTrade.ELECTRONIC_GOODS_ORDER

        params = {
            'channel': channel,
            'order_type': order_type,
        }

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
                'user_address_id': address.id,
            })

        if order_type == SaleTrade.TEAMBUY_ORDER:
            try:
                teambuy = TeamBuy.objects.filter(id=form.get('teambuy_id')).first()
            except:
                teambuy = None

        buyer_openid = options.get_openid_by_unionid(customer.unionid, settings.WX_PUB_APPID)
        buyer_openid = buyer_openid or customer.openid
        payment = round(float(form.get('payment')), 2)
        pay_extras = form.get('pay_extras', '')
        budget_payment = self.calc_extra_budget(pay_extras)
        coupon_ids = self.parse_coupon_ids_from_pay_extras(pay_extras)

        if not coupon_ids:
            coupon_id = form.get('coupon_id', None)
            if coupon_id:
                coupon_ids.append(coupon_id)

        logistics_company_id = form.get('logistics_company_id', '').strip()
        logistic_company = None

        if address and logistics_company_id and logistics_company_id != '0':
            if logistics_company_id.replace('-', '').isdigit():
                logistic_company = LogisticsCompany.objects.get(id=logistics_company_id)
            else:
                logistic_company = LogisticsCompany.objects.get(code=logistics_company_id)
            tasks_set_address_priority_logistics_code.delay(address.id, logistic_company.id)

        params.update({
            'buyer_nick': customer.nick,
            'buyer_message': form.get('buyer_message', ''),
            'payment': payment,
            'pay_cash': max(0, round(payment * 100 - budget_payment) / 100.0),
            'has_budget_paid': budget_payment > 0,
            'total_fee': round(float(form.get('total_fee')), 2),
            'post_fee': round(float(form.get('post_fee')), 2),
            'discount_fee': round(float(form.get('discount_fee')), 2),
            'charge': '',
            'logistics_company_id':  logistic_company and logistic_company.id or None,
            'status': SaleTrade.WAIT_BUYER_PAY,
            'openid': buyer_openid,
            'is_boutique': is_boutique,
            'extras_info': {
                'coupon': coupon_ids,
                'pay_extras': pay_extras,
                'agent': request.META.get('HTTP_USER_AGENT')
            }
        })
        params['extras_info'].update(self.get_mama_referal_params(request))
        for k, v in params.iteritems():
            hasattr(sale_trade, k) and setattr(sale_trade, k, v)
        if order_type == SaleTrade.TEAMBUY_ORDER:
            sale_trade.extras_info['teambuy_id'] = teambuy.id if teambuy else ''

        try:
            sale_trade.save()
        except IntegrityError:
            sale_trade = SaleTrade.objects.filter(tid=tuuid).first()
            return sale_trade, False

        # record prepay stats
        from django_statsd.clients import statsd
        dt_str = datetime.datetime.now().strftime('%Y.%m.%d')
        statsd.incr('xiaolumm.prepay_count.%s'%dt_str)
        statsd.incr('xiaolumm.prepay_amount.%s'%dt_str, sale_trade.payment)

        return sale_trade, True

    def create_Saleorder_By_Shopcart(self, saletrade, cart_qs):
        """ 根据购物车创建订单明细方法 """
        total_fee = saletrade.total_fee
        total_payment = saletrade.payment - saletrade.post_fee
        discount_fee = saletrade.discount_fee
        for cart in cart_qs:
            product = Product.objects.get(id=cart.item_id)
            sku = ProductSku.objects.get(id=cart.sku_id)
            cart_total_fee = cart.price * cart.num
            cart_payment  = float('%.2f'%(total_payment / total_fee * cart_total_fee))
            cart_discount = float('%.2f'%(discount_fee / total_fee * cart_total_fee))
            SaleOrder.objects.create(
                 sale_trade=saletrade,
                 item_id=cart.item_id,
                 sku_id=cart.sku_id,
                 num=cart.num,
                 outer_id=product.outer_id,
                 outer_sku_id=sku.outer_id,
                 title=product.name,
                 payment=cart_payment,
                 discount_fee=cart_discount,
                 total_fee=cart_total_fee,
                 price=cart.price,
                 pic_path=product.pic_path,
                 sku_name=sku.properties_alias,
                 status=SaleTrade.WAIT_BUYER_PAY
            )

        #关闭购物车
        for cart in cart_qs:
            cart.close_cart(release_locknum=False)

    def create_SaleOrder_By_Productsku(self,saletrade,product,sku,num):
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

    def parse_entry_params(self, pay_extras):
        """
        解析 pay_extras

        示例
        pid:1:value:2,pid:2:couponid:305463/305463/305463:value:50.00,pid:3:budget:46.00
        pid:1:value:2;pid:2:value:3:conponid:2
        """

        if not pay_extras:
            return []

        pay_list = [e for e in re.split(',|;', pay_extras) if e.strip()]
        extra_list = []
        already_exists_pids = []

        for k in pay_list:
            pdict = {}
            keys = k.split(':')
            for i in range(0, len(keys) / 2):
                pdict.update({keys[2*i]: keys[2*i+1]})

            if pdict.get('pid') and pdict['pid'] not in already_exists_pids:
                extra_list.append(pdict)
                already_exists_pids.append(pdict['pid'])
        return extra_list

    def parse_pay_extras_to_dict(self, pay_extras):
        """
        [{'pid': 1, 'value': 2}] => {1: {'pid':1, 'value': 2}}
        """
        extra_list = self.parse_entry_params(pay_extras)
        d = {}
        for item in extra_list:
            d[item['pid']] = item
        return d

    def parse_coupon_ids_from_pay_extras(self, pay_extras):
        """
        从pay_extras获取优惠券id
        """
        extras = self.parse_pay_extras_to_dict(pay_extras)
        couponid_str = extras.get(CONS.ETS_COUPON, {}).get('couponid', '')
        coupon_ids = couponid_str.split('/')
        coupon_ids = filter(lambda x: x, coupon_ids)
        return coupon_ids

    def calc_counpon_discount(self, coupon_id, item_ids, buyer_id, payment, order_no='',**kwargs):
        """
        计算优惠券折扣
        payment（单位分）按原始支付金额计算优惠信息
        """
        user_coupon = UserCoupon.objects.filter(id=coupon_id, customer_id=buyer_id).first()

        if not user_coupon:
            raise exceptions.APIException(u'优惠券未找到')

        if user_coupon.trade_tid == order_no :
            return round(user_coupon.value * 100)

        user_coupon.check_user_coupon(product_ids=item_ids, use_fee=payment / 100.0)
        return round(user_coupon.value * 100)

    def get_coupon_template_ids(self, coupon_ids):
        """
        根据优惠券id获取优惠券模板id
        """
        template_ids = UserCoupon.objects.filter(id__in=coupon_ids).values('template_id')
        template_ids = list(set([x['template_id'] for x in template_ids]))
        return template_ids

    def calc_extra_discount(self, pay_extras, **kwargs):
        """　
        优惠信息(分)
        """
        pay_extra_list = self.parse_entry_params(pay_extras)
        discount_fee = 0

        for param in pay_extra_list:
            pid = param['pid']

            # 优惠券
            if pid == CONS.ETS_COUPON and CONS.PAY_EXTRAS[pid].get('type') == CONS.DISCOUNT:
                coupon_ids = param.get('couponid', '').split('/')

                # 检查多张优惠券必须为同一类型优惠券，不同类型优惠券不许同时使用
                coupon_template_ids = self.get_coupon_template_ids(coupon_ids)
                if len(coupon_template_ids) > 1:
                    raise Exception('优惠券不是同一模板')

                for coupon_id in coupon_ids:
                    if not coupon_id or not coupon_id.isdigit():
                        continue
                    coupon_id = int(coupon_id)
                    discount_fee += self.calc_counpon_discount(coupon_id, **kwargs)

            # caution APP立减2元，立减金额不依客户端传入金额做计算
            if pid == CONS.ETS_APPCUT and float(param['value']) > 0 and CONS.PAY_EXTRAS[pid].get('type') == CONS.DISCOUNT:
                discount_fee += CONS.PAY_EXTRAS[pid]['value'] * 100

        return round(discount_fee)

    def calc_extra_budget(self, pay_extras, **kwargs):
        """　支付余额(分) """
        pay_extra_list = self.parse_entry_params(pay_extras)
        pay_extra_dict = dict([(p['pid'], p) for p in pay_extra_list if p.get('pid')])
        budget_amount = 0
        for param in pay_extra_dict.values():
            pid = param['pid']
            if pid in CONS.PAY_EXTRAS and CONS.PAY_EXTRAS[pid].get('type') == CONS.BUDGET:
                budget_amount += round(float(param['budget']) * 100)
        return budget_amount

    def logger_request(self, request):
        data = request.POST.dict()
        cookies = dict([(k, v) for k, v in request.COOKIES.items() if k in ('mm_linkid', 'ufrom')])
        logger.info({
            'code': 0,
            'info': u'付款请求v2', 
            'channel': data.get('channel'),
            'http_referal': request.META.get('HTTP_REFERER'),
            'user_agent':request.META.get('HTTP_USER_AGENT'), 
            'action': 'trade_create', 
            'order_no': data.get('uuid'), 
            'data': str(data),
            'cookies':cookies,
        })

    def check_use_coupon_only_buynow(self, product, cart_discount, cart_total_fee, coupon_template_id):
        """
            bunow检测是否只允许优惠券购买商品，参数是否异常
            """
        use_coupon_only = False
        mp = product.get_product_model()
        # 包含只允许优惠券购买的商品
        if mp and mp.extras.get('payinfo', {}).get('use_coupon_only', False):
            use_coupon_only = True

        if use_coupon_only:
            coupon_template_ids = product.get_product_model().extras.get('payinfo', {}).get('coupon_template_ids', [])
            if coupon_template_id and (coupon_template_id not in coupon_template_ids):  # 商品和优惠券相对应
                return Response({'code': 22, 'info': u'该商品属于特价精品汇商品，请使用精品汇优惠券。如需购券，请查看精品汇商品说明和咨询客服。'})

            #if cart_discount < cart_total_fee:  # 优惠券价格 < 购物车需支付价格
            #    return Response({'code': 23, 'info': u'精品汇优惠券不足，请购买优惠券或减少商品购买数量'})

        return False

    def check_use_coupon_only(self, cart_qs, cart_discount, cart_total_fee, coupon_template_id):
        """
        检测是否只允许优惠券购买商品，参数是否异常
        """
        use_coupon_only = False
        for cart in cart_qs:
            mp = cart.get_modelproduct()
            # 包含只允许优惠券购买的商品
            if mp and mp.extras.get('payinfo', {}).get('use_coupon_only', False):
                use_coupon_only = True
                break

        if use_coupon_only:
            if cart_qs.count() > 1:  # 商品种类大于一种
                return Response({'code': 21, 'info': u'该精品汇商品只能单独购买'})

            cart = cart_qs[0]
            coupon_template_ids = cart.get_modelproduct().extras.get('payinfo', {}).get('coupon_template_ids', [])
            if coupon_template_id and (coupon_template_id not in coupon_template_ids):  # 商品和优惠券相对应
                return Response({'code': 22, 'info': u'该商品属于特价精品汇商品，请使用精品汇优惠券。如需购券，请查看精品汇商品说明和咨询客服。'})

            #if cart_discount < cart_total_fee:  # 优惠券价格 < 购物车需支付价格
            #    return Response({'code': 23, 'info': u'精品汇优惠券不足，请购买优惠券或减少商品购买数量'})

        return False

    def check_mixed_virtual_goods(self, cart_qs, customer):
        """
        检测购买精品券虚拟商品时，不能搭配普通商品，只能全部为虚拟商品，否则返回参数异常
        """

        virtual_num = 0
        goods_num = 0
        elite_score = 0
        for cart in cart_qs:
            mp = cart.get_modelproduct()
            # 包含virtual的商品
            from flashsale.pay.models.product import ModelProduct
            if mp and (mp.product_type == ModelProduct.VIRTUAL_TYPE):
                virtual_num += 1
                elite_score += cart.num * cart.product.elite_score
                goods_num += cart.num

        if virtual_num > 0:
            if virtual_num != cart_qs.count():
                return Response({'code': 24, 'info': u'购买精品券或虚拟商品时，只能单独购买，不能与普通商品搭配'})
            if (goods_num < 5) and (elite_score < 30):
                return Response({'code': 25, 'info': u'购买精品券最低购买5张或者30积分，您本次购买没有达到要求，请在购物车重新添加精品券'})
            mm = customer.getXiaolumm()
            if not (mm and (mm.referal_from == XiaoluMama.DIRECT)):
                return Response({'code': 26, 'info': u'您没有直接购券权限，请在购券界面提交申请'})
        return False

    @list_route(methods=['post'])
    def shoppingcart_create(self, request, *args, **kwargs):
        """
        购物车订单支付接口
        """
        self.logger_request(request)
        user_agent = request.META.get('HTTP_USER_AGENT')
        content = request.data
        tuuid = content.get('uuid')
        customer = Customer.objects.filter(user=request.user).first()
        cart_ids = [i for i in content.get('cart_ids', '').split(',') if i.isdigit()]
        cart_qs = ShoppingCart.objects.filter(
            id__in=cart_ids,
            buyer_id=customer.id
        )

        # 这里不对购物车状态进行过滤，防止订单创建过程中购物车状态发生变化
        if cart_qs.count() != len(cart_ids):
            logger.warn({
                'code': 1,
                'message': u'购物车已结算',
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % content
            })
            return Response({'code': 1, 'info': u'购物车已结算'})

        total_fee = round(float(content.get('total_fee', '0')) * 100)
        payment = round(float(content.get('payment', '0')) * 100)
        post_fee = round(float(content.get('post_fee', '0')) * 100)
        discount_fee = round(float(content.get('discount_fee', '0')) * 100)
        pay_extras = content.get('pay_extras')
        cart_total_fee = 0
        cart_discount = 0
        order_type = content.get('order_type')

        if not order_type:
            order_type = SaleTrade.SALE_ORDER
        else:
            order_type = int(order_type)

        # 计算购物车价格
        item_ids = []
        for cart in cart_qs:
            if not cart.is_good_enough():
                logger.warn({
                    'code': 2,
                    'message': u'商品刚被抢光了',
                    'action':'trade_create',
                    'user_agent': user_agent,
                    'order_no': tuuid,
                    'data': '%s' % content
                })
                return Response({'code': 2, 'info': u'商品刚被抢光了'})
            cart_total_fee += round(cart.price * cart.num * 100)
            item_ids.append(cart.item_id)

        extra_params = {
            'item_ids': item_ids,
            'buyer_id': customer.id,
            'payment':  cart_total_fee - cart_discount,
            'order_no': tuuid,
        }

        # 计算折扣
        try:
            cart_discount += self.calc_extra_discount(pay_extras, **extra_params)
        except Exception, exc:
            logger.warn({
                'code': 3,
                'message': exc,
                'action':'trade_create',
                'user_agent': user_agent,
                'order_no': tuuid,
                'data': '%s' % content
            })
            return Response({'code': 3, 'info': exc.message})

        cart_discount = min(cart_discount, cart_total_fee)
        if discount_fee > cart_discount:
            logger.warn({
                'code': 4,
                'message': u'优惠金额异常:discount_fee=%s, cart_discount=%s' % (discount_fee, cart_discount),
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % content
            })
            return Response({'code': 4, 'info': u'优惠金额异常'})

        # 计算购物车需要支付价格 = 购物车价格 + 邮费 - 折扣
        cart_payment = cart_total_fee + post_fee - cart_discount
        if (post_fee < 0 or payment < 0 or abs(payment - cart_payment) > 10 or abs(total_fee - cart_total_fee) > 10):
            logger.warn({
                'code': 11,
                'message': u'付款金额异常:payment=%s, cart_payment=%s' % (payment, cart_payment),
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % content
            })
            return Response({'code': 11, 'info': u'付款金额异常'})

        # 检测组合虚拟商品购买时，不能跟普通商品搭配
        error = self.check_mixed_virtual_goods(cart_qs, customer)
        if error:
            return error

        # 检测是否只允许优惠券购买商品，参数是否异常
        coupon_ids = self.parse_coupon_ids_from_pay_extras(pay_extras)
        coupon_template_ids = self.get_coupon_template_ids(coupon_ids)
        coupon_template_id = coupon_template_ids[0] if coupon_template_ids else None
        error = self.check_use_coupon_only(cart_qs, cart_discount, cart_total_fee, coupon_template_id)
        if error:
            return error

        # 检查收货地址
        if order_type != SaleTrade.ELECTRONIC_GOODS_ORDER:
            addr_id = content.get('addr_id') or None
            address = UserAddress.objects.filter(id=addr_id, cus_uid=customer.id).first()
            if not address:
                logger.warn({
                    'code': 7,
                    'message': u'请选择收货地址',
                    'user_agent': user_agent,
                    'action':'trade_create',
                    'order_no': tuuid,
                    'data': '%s' % content
                })
                return Response({'code': 7, 'info': u'请选择收货地址'})
        else:
            address = None

        # 检查付款方式
        channel = content.get('channel')
        if channel not in dict(SaleTrade.CHANNEL_CHOICES):
            logger.warn({
                'code': 5,
                'message': u'付款方式有误',
                'channel': channel,
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % content
            })
            return Response({'code': 5, 'info': u'付款方式有误'})

        # 创建订单
        try:
            with transaction.atomic():
                sale_trade, state = self.create_Saletrade(request, content, address, customer, order_type=order_type)
                if state:
                    self.create_Saleorder_By_Shopcart(sale_trade, cart_qs)
        except Exception, exc:
            logger.error({
                'code': 8,
                'message': u'订单创建异常:%s' % exc,
                'channel': channel,
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % content
            })
            return Response({'code': 8, 'info': u'订单创建异常'})

        try:
            if channel == SaleTrade.WALLET:
                # 妈妈钱包支付 2016-4-23 关闭代理钱包支付功能
                return Response({'code': 10, 'info': u'妈妈钱包支付功能已取消'})
                # response_charge = self.wallet_charge(sale_trade)
            elif channel == SaleTrade.BUDGET:
                # 小鹿钱包
                response_charge = self.budget_charge(sale_trade)
            else:
                # pingpp 支付
                response_charge = self.pingpp_charge(sale_trade)
            if sale_trade.order_type == 3:
                order_success_url = CONS.TEAMBUY_SUCCESS_URL.format(order_tid=sale_trade.tid) \
                                    + '?from_page=order_commit'
            else:
                order_success_url = CONS.MALL_PAY_SUCCESS_URL.format(order_id=sale_trade.id, order_tid=sale_trade.tid)
        except IntegrityError, exc:
            logger.error({
                'code': 9,
                'message': u'订单重复提交:%s' % exc,
                'channel': channel,
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % content
            }, exc_info=True)
            return Response({'code': 9, 'info': u'订单重复提交'})
        except Exception, exc:
            logger.error({
                'code': 6,
                'message': u'未知支付异常:%s' % exc,
                'channel': channel,
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % content
            }, exc_info=True)
            return Response({'code': 6, 'info': str(exc) or u'未知支付异常'})

        return Response({
            'code': 0,
            'info': u'支付请求成功',
            'channel': channel,
            'trade': {
                'id': sale_trade.id,
                'tid': sale_trade.tid,
                'channel': channel,
                'type': sale_trade.order_type
            },
            'charge': response_charge,
            'success_url': order_success_url,
            'fail_url': CONS.MALL_PAY_CANCEL_URL
        })

    @list_route(methods=['post'])
    def buynow_create(self, request, *args, **kwargs):
        """ 立即购买订单支付接口 """
        self.logger_request(request)
        CONTENT  = request.data
        user_agent = request.META.get('HTTP_USER_AGENT')
        tuuid = CONTENT.get('uuid')
        item_id  = CONTENT.get('item_id')
        sku_id   = CONTENT.get('sku_id')
        sku_num  = int(CONTENT.get('num','1'))
        pay_extras = CONTENT.get('pay_extras')
        order_type   = int(CONTENT.get('order_type', 0))
        teambuy_id = CONTENT.get('teambuy_id')
        customer        = get_object_or_404(Customer,user=request.user)
        product         = get_object_or_404(Product,id=item_id)
        product_sku     = get_object_or_404(ProductSku,id=sku_id)
        if order_type == SaleTrade.TEAMBUY_ORDER and teambuy_id:
            teambuy = get_object_or_404(TeamBuy, id=teambuy_id)
        total_fee       = round(float(CONTENT.get('total_fee','0')) * 100)
        payment         = round(float(CONTENT.get('payment','0')) * 100)
        post_fee        = round(float(CONTENT.get('post_fee','0')) * 100)
        discount_fee    = round(float(CONTENT.get('discount_fee','0')) * 100)
        bn_totalfee     = round(product_sku.agent_price * sku_num * 100)

        xlmm            = self.get_xlmm(request)
        user_skunum = get_user_skunum_by_last24hours(customer, product_sku)
        lockable = Product.objects.isQuantityLockable(product_sku, sku_num + user_skunum)
        if not lockable:
            logger.warn({
                'code': 12,
                'message': u'该商品已限购',
                'action':'trade_create',
                'user_agent': user_agent,
                'order_no': tuuid,
                'data': '%s' % CONTENT
            })
            return Response({'code': 2, 'info': u'该商品已限购'})

        bn_discount     = product_sku.calc_discount_fee(xlmm) * sku_num
        if product_sku.free_num < sku_num or product.shelf_status == Product.DOWN_SHELF:
            logger.warn({
                'code': 2,
                'message': u'商品刚被抢光了',
                'action':'trade_create',
                'user_agent': user_agent,
                'order_no': tuuid,
                'data': '%s' % CONTENT
            })
            return Response({'code': 2, 'info': u'商品刚被抢光了'})

        # 计算折扣
        item_ids = []
        item_ids.append(item_id)
        extra_params = {
            'item_ids': item_ids,
            'buyer_id': customer.id,
            'payment': bn_totalfee - bn_discount,
            'order_no': tuuid,
        }
        try:
            bn_discount += self.calc_extra_discount(pay_extras, **extra_params)
        except Exception, exc:
            logger.warn({
                'code': 3,
                'message': exc,
                'action':'trade_create',
                'user_agent': user_agent,
                'order_no': tuuid,
                'data': '%s' % CONTENT
            })
            return Response({'code': 3, 'info': exc.message})

        bn_discount = min(bn_discount, bn_totalfee)
        if discount_fee > bn_discount:
            logger.warn({
                'code': 4,
                'message': u'优惠金额异常:discount_fee=%s, cart_discount=%s' % (discount_fee, bn_discount),
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % CONTENT
            })
            return Response({'code': 4, 'info': u'优惠金额异常'})

        bn_payment = bn_totalfee + post_fee - bn_discount
        if (post_fee < 0 or payment < 0 or abs(payment - bn_payment) > 10
            or abs(total_fee - bn_totalfee) > 10):
            logger.warn({
                'code': 11,
                'message': u'付款金额异常:payment=%s, cart_payment=%s' % (payment, bn_payment),
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % CONTENT
            })
            return Response({'code': 11, 'info': u'付款金额异常'})

        # 检测是否只允许优惠券购买商品，参数是否异常
        coupon_ids = self.parse_coupon_ids_from_pay_extras(pay_extras)
        coupon_template_ids = self.get_coupon_template_ids(coupon_ids)
        coupon_template_id = coupon_template_ids[0] if coupon_template_ids else None
        error = self.check_use_coupon_only_buynow(product, bn_discount, bn_totalfee, coupon_template_id)
        if error:
            return error

        # 检查收货地址
        if order_type != SaleTrade.ELECTRONIC_GOODS_ORDER:
            addr_id = CONTENT.get('addr_id') or None
            address = UserAddress.objects.filter(id=addr_id, cus_uid=customer.id).first()
            if not address:
                logger.warn({
                    'code': 7,
                    'message': u'请选择收货地址',
                    'user_agent': user_agent,
                    'action':'trade_create',
                    'order_no': tuuid,
                    'data': '%s' % CONTENT
                })
                return Response({'code': 7, 'info': u'请选择收货地址'})
        else:
            address = None

        channel  = CONTENT.get('channel')
        if channel not in dict(SaleTrade.CHANNEL_CHOICES):
            logger.warn({
                'code': 5,
                'message': u'付款方式有误',
                'channel': channel,
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % CONTENT
            })
            return Response({'code': 5, 'info': u'付款方式有误'})
        sku = ProductSku.objects.get(id=sku_id)
        try:
            # lock_success =  Product.objects.lockQuantity(product_sku,sku_num)
            if sku_num > sku.free_num:
                logger.warn({
                    'code': 2,
                    'message': u'商品刚被抢光了',
                    'action':'trade_create',
                    'user_agent': user_agent,
                    'order_no': tuuid,
                    'data': '%s' % CONTENT
                })
                return Response({'code': 2, 'info': u'商品刚被抢光了'})
            with transaction.atomic():
                sale_trade,state = self.create_Saletrade(request, CONTENT, address, customer, order_type)
                if state:
                    self.create_SaleOrder_By_Productsku(sale_trade, product, product_sku, sku_num)
        except exceptions.APIException,exc:
            raise exc
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            Product.objects.releaseLockQuantity(product_sku, sku_num)
            logger.error({
                'code': 8,
                'message': u'订单创建异常:%s' % exc,
                'channel': channel,
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % CONTENT
            })
            return Response({'code': 8, 'info': u'订单创建异常'})

        try:
            if channel == SaleTrade.WALLET:
                # 妈妈钱包支付 2016-4-23 关闭代理钱包支付功能
                return Response({'code': 10, 'info': u'妈妈钱包支付功能已取消'})
                # response_charge = self.wallet_charge(sale_trade)
            elif channel == SaleTrade.BUDGET:
                #小鹿钱包
                response_charge = self.budget_charge(sale_trade)
            else:
                #pingpp 支付
                response_charge = self.pingpp_charge(sale_trade)

            if sale_trade.order_type == 3:
                order_success_url = CONS.TEAMBUY_SUCCESS_URL.format(order_tid=sale_trade.tid) \
                                    + '?from_page=order_commit'
            else:
                order_success_url = CONS.MALL_PAY_SUCCESS_URL.format(order_id=sale_trade.id, order_tid=sale_trade.tid)
        except IntegrityError, exc:
            logger.error({
                'code': 9,
                'message': u'订单重复提交:%s' % exc,
                'channel': channel,
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % CONTENT
            }, exc_info=True)
            return Response({'code': 9, 'info': u'订单重复提交'})
        except Exception, exc:
            logger.error({
                'code': 6,
                'message': u'未知支付异常:%s' % exc,
                'channel': channel,
                'user_agent': user_agent,
                'action':'trade_create',
                'order_no': tuuid,
                'data': '%s' % CONTENT
            }, exc_info=True)
            return Response({'code': 6, 'info': str(exc) or u'未知支付异常'})

        return Response({
            'code': 0,
            'info': u'支付请求成功',
            'channel': channel,
            'trade': {
                'id': sale_trade.id,
                'tid': sale_trade.tid,
                'channel': channel,
                'type': sale_trade.order_type
            },
            'charge': response_charge,
            'success_url': order_success_url,
            'fail_url': CONS.MALL_PAY_CANCEL_URL
        })

    @detail_route(methods=['post'])
    def charge(self, request, *args, **kwargs):
        """ 待支付订单支付 """
        _errmsg = {SaleTrade.WAIT_SELLER_SEND_GOODS: u'订单无需重复付款',
                   SaleTrade.TRADE_CLOSED_BY_SYS: u'订单已关闭或超时',
                   'default': u'订单不在可支付状态'}
        channel = request.data.get('channel','')
        instance = self.get_object()
        logger.warn('charge:%s, %s' % (instance.tid, request.data))
        if channel and channel != instance.channel:
            instance.channel = channel
            instance.save(update_fields=['channel'])

        if instance.status != SaleTrade.WAIT_BUYER_PAY:
            logger.error('SaleTradeViewSet charge : code=1, %s' % instance.tid)
            return Response({'code': 1, 'info': _errmsg.get(instance.status, _errmsg.get('default'))})

        if not instance.is_payable():
            logger.error('SaleTradeViewSet charge : code=2, %s' % instance.tid)
            return Response({'code': 2, 'info': _errmsg.get(SaleTrade.TRADE_CLOSED_BY_SYS)})

        try:
            if instance.channel == SaleTrade.WALLET:
                # 小鹿钱包支付
                response_charge = self.wallet_charge(instance, check_coupon=False)
            elif instance.channel == SaleTrade.BUDGET:
                # 小鹿钱包
                response_charge = self.budget_charge(instance, check_coupon=False)
            else:
                # pingpp 支付
                response_charge = self.pingpp_charge(instance, check_coupon=False)
        except IntegrityError, exc:
            logger.error('charge duplicate:%s,channel=%s, err=%s' % (
                instance.tid, instance.channel, exc.message), exc_info=True)
            return Response({'code': 9, 'info': u'订单重复提交'})
        except Exception, exc:
            logger.error('charge error:%s, channel=%s, err=%s' % (instance.tid, channel, exc.message), exc_info=True)
            return Response({'code': 6, 'info': exc.message or u'未知支付异常'})

        return Response({'code': 0, 'info': u'支付成功','channel':instance.channel,
                         'trade':{'id':instance.id, 'tid':instance.tid, 'channel':instance.channel,},
                         'charge': response_charge})

    def perform_destroy(self, instance):
        # 订单不在 待付款的 或者不在创建状态
        instance.close_trade()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        charge = xiaolupay.Charge.retrieve(instance.tid)
        if charge and charge.paid:
            notifyTradePayTask.delay(charge)
            return Response({"code": 1, "info": u'订单已支付不支持取消'})
        else:
            self.perform_destroy(instance)
            log_action(request.user.id, instance, CHANGE, u'取消订单')
            return Response({"code": 0, "info": u'订单已取消'})

    @detail_route(methods=['post'])
    def confirm_sign(self, request, *args, **kwargs):
        """ 确认签收 """
        instance = self.get_object()
        wait_sign_orders = instance.sale_orders.filter(status=SaleOrder.WAIT_BUYER_CONFIRM_GOODS)
        if not wait_sign_orders.exists():
            return Response({"code": 1, "info": "没有可签收订单"})

        customer = self.get_customer(request)
        for order in wait_sign_orders:
            order.confirm_sign_order()
            logger.info('user(:%s) confirm sign order(:%s)' % (customer, order.oid))

        return Response({"code": 0, "info": "签收成功"})

    @detail_route(methods=['post'])
    def remind_send(self, request,  *args, **kwargs):
        """ 提醒发货 """
        instance = self.get_object()
        # TODO
        return Response({"code": 0, "info": "已通知尽快发货"})

    @detail_route(methods=['post'])
    def undisplay(self, request, *args, **kwargs):
        """ 不显示订单 """
        instance = self.get_object()
        charge = xiaolupay.Charge.retrieve(instance.tid)
        if charge and charge.paid:
            notifyTradePayTask.delay(charge)
            return Response({"code": 1, "info": u'订单已支付不支持取消'})
        else:
            self.perform_destroy(instance)
        return Response({"code": 0, "info": u"订单已删除"})


from flashsale.restpro.v1.views_refund import refund_Handler

class SaleOrderViewSet(viewsets.ModelViewSet):
    """
    ###特卖订单明细REST API接口：
     - {path}/confirm_sign[.formt]: 确认收货
     - {path}/remind_send[.formt]: 提醒发货
     - {path}/undisplay[.formt]: 删除订单记录
     - {path}/apply_refund[.formt]:申请退款
        > -`id`:sale order id
        > -`reason`:退货原因
        > -`num`:退货数量
        > -`sum_price` 申请金额
        > -`description`: 申请描述
        > -`proof_pic`: 佐证图片（字符串格式网址链接，多个使用＇，＇隔开）
        - - 修改退款单
        > -`id`: sale order id
        > -`modify`:   1
        > -`reason`:   退货原因
        > -`num`:  退货数量
        > -`sum_price`:    申请金额
        > -`description`:  申请描述
    """
    queryset = SaleOrder.objects.all()
    serializer_class = serializers.SaleOrderSerializer  # Create your views here.
    authentication_classes = (authentication.BasicAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_customer(self, request):
        customer = Customer.objects.filter(user=request.user.id).exclude(status=Customer.DELETE).first()
        return customer

    def get_owner_queryset(self, request):
        queryset = self.get_queryset()
        customer = self.get_customer(request)
        return queryset.filter(buyer_id=customer.id)

    def list(self, request, *args, **kwargs):
        """
        获取用户订单列表
        """
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def confirm_sign(self, request, pk=None, *args, **kwargs):
        """ 确认签收 """
        instance = self.get_object()
        instance.confirm_sign_order()
        customer = self.get_customer(request)
        logger.info('user(:%s) confirm sign order(:%s)'%(customer, instance.oid))

        return Response({"code":0,"info": "签收成功"})

    @detail_route(methods=['post'])
    def remind_send(self, request, pk=None, *args, **kwargs):
        """ 提醒发货 """
        instance = self.get_object()
        # TODO
        return Response({"code":0,"info": "已通知尽快发货"})

    @detail_route(methods=['post'])
    def undisplay(self, request, pk=None, *args, **kwargs):
        """ 不显示订单 """
        instance = self.get_object()
        # TODO
        return Response({"code":0,"info": "订单已删除"})

    @detail_route(methods=['post'])
    def apply_refund(self, request, pk=None, *args, **kwargs):
        """ 申请退款 """
        instance = self.get_object()
        # 如果Order已经付款 refund_type = BUYER_NOT_RECEIVED
        # 如果Order 仅仅签收状态才可以退货  refund_type = BUYER_RECEIVED
        second_kill = instance.second_kill_title()
        if second_kill:
            raise exceptions.APIException(u'秒杀商品暂不支持退单，请见谅！')
        elif instance.status not in (SaleOrder.TRADE_BUYER_SIGNED, SaleOrder.WAIT_SELLER_SEND_GOODS):
            raise exceptions.APIException(u'订单状态不予退款或退货')

        res = refund_Handler(request)
        customer = self.get_customer(request)
        logger.warn('user(:%s) apply refund order(:%s)' % (customer, instance.oid))
        return Response({"code":0,"info": "success"})

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def destroy(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')
