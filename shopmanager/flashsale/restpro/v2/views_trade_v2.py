# coding:utf-8
import re
import time
import datetime
import pingpp
import urlparse
import decimal

from django.db import models
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

from flashsale.pay.models import (
    SaleTrade,
    SaleOrder,
    Customer,
    UserBudget,
    BudgetLog,
    ShoppingCart,
    UserAddress,
    gen_uuid_trade_tid,
)
from flashsale.coupon.models import UserCoupon
from flashsale.restpro import permissions as perms
from flashsale.restpro import serializers
from shopback.items.models import Product, ProductSku
from shopback.base import log_action, ADDITION, CHANGE
from shopback.logistics.models import LogisticsCompany
from shopapp.weixin import options
from common.utils import update_model_fields
from flashsale.restpro import constants as CONS

from flashsale.xiaolumm.models import XiaoluMama,CarryLog
from flashsale.pay.tasks import confirmTradeChargeTask

import logging
logger = logging.getLogger(__name__)


UUID_RE = re.compile('^[a-z]{2}[0-9]{6}[a-z0-9-]{10,14}$')

def is_from_weixin(request):
    user_agent = request.META.get('HTTP_USER_AGENT')
    if user_agent and re.search('MicroMessenger', user_agent, re.IGNORECASE):
        return True
    return False

class ShoppingCartViewSet(viewsets.ModelViewSet):
    """
    ###特卖购物车REST API接口：
    - payment (实付金额) = total_fee (商品总金额) + post_fee (邮费) - discount_fee (优惠金额)
    - {prefix}/{{pk}}/delete_carts[.formt]: 删除;
    - {prefix}/{{pk}}/plus_product_carts[.formt]: 增加一件;
    - {prefix}/{{pk}}/minus_product_carts[.formt]: 减少一件;
    - {prefix}/show_carts_num[.formt]: 显示购物车数量;
    - {prefix}/show_carts_history[.formt]: 显示购物车历史;
    - {prefix}/sku_num_enough[.formt]: 获取商品规格数量是否充足;
    > sku_id:规格ID;
    > sku_num:规格数量;
    - {prefix}/carts_payinfo[.formt]: 根据购物车记录获取支付信息;
    > cart_ids：购物车ID列表,如101,102,103,...
    > device :支付类型 (app ,app支付), (wap, wap支付), (web, 网页支付)
    - {prefix}/now_payinfo[.formt]: 根据立即购买获取支付信息;
    > sku_id：要立即购买的商品规格ID
    > device :支付类型 (app ,app支付), (wap, wap支付), (web, 网页支付)
    """
    queryset = ShoppingCart.objects.all()
    serializer_class = serializers.ShoppingCartSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(buyer_id=customer.id, status=ShoppingCart.NORMAL).order_by('-created')

    def get_customer(self, request):
        if not hasattr(self,'__customer__'):
            self.__customer__ = Customer.objects.filter(user=request.user).first()
        return self.__customer__

    def list(self, request, *args, **kwargs):
        """列出购物车中所有的状态为正常的数据"""
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        serializers = self.get_serializer(queryset, many=True)
        return Response(serializers.data)

    def create(self, request, *args, **kwargs):
        """创建购物车数据"""
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        data = request.data
        customer_user = Customer.objects.filter(user=request.user)

        if customer_user.count() == 0:
            return Response({"result": "0"})  # 登录过期
        customer = customer_user[0]
        product_id = data.get("item_id", None)
        buyer_id = customer.id
        sku_id = data.get("sku_id", None)
        if not (product_id and sku_id):
            raise exceptions.APIException(u'参数错误')

        product = get_object_or_404(Product, pk=product_id)
        if product.detail and product.detail.is_seckill:
            raise exceptions.APIException(u'秒杀商品不能加购物车')

        if not product.is_onshelf():
            raise exceptions.APIException(u'商品已下架')

        cart_id = data.get("cart_id", None)
        if cart_id:
            s_temp = ShoppingCart.objects.filter(item_id=product_id, sku_id=sku_id,
                                                 status=ShoppingCart.CANCEL, buyer_id=customer.id)
            s_temp.delete()
        sku_num = 1
        sku = get_object_or_404(ProductSku, pk=sku_id)
        # user_skunum = getUserSkuNumByLast24Hours(customer, sku)
        lockable = Product.objects.isQuantityLockable(sku, sku_num)
        if not lockable:
            raise exceptions.APIException(u'该商品已限购')

        if not Product.objects.lockQuantity(sku, sku_num):
            raise exceptions.APIException(u'商品库存不足')

        if product_id and buyer_id and sku_id:
            shop_cart = ShoppingCart.objects.filter(item_id=product_id, buyer_id=buyer_id, sku_id=sku_id,
                                                    status=ShoppingCart.NORMAL)
            if shop_cart.count() > 0:
                shop_cart_temp = shop_cart[0]
                shop_cart_temp.num += int(sku_num) if sku_num else 0
                shop_cart_temp.total_fee = decimal.Decimal(shop_cart_temp.total_fee) + decimal.Decimal(sku.agent_price)
                shop_cart_temp.save()
                return Response({"result": "1", "code": 1, "info": "购物车已存在"})  # 购物车已经有了

            new_shop_cart = ShoppingCart()
            new_shop_cart.buyer_id = buyer_id
            for k, v in data.iteritems():
                if v:
                    hasattr(new_shop_cart, k) and setattr(new_shop_cart, k, v)
            new_shop_cart.buyer_nick = customer_user[0].nick if customer_user[0].nick else ""
            new_shop_cart.price = sku.agent_price
            new_shop_cart.num = 1
            new_shop_cart.std_sale_price = sku.std_sale_price
            new_shop_cart.total_fee = sku.agent_price * int(sku_num) if sku.agent_price else 0
            new_shop_cart.sku_name = sku.name
            new_shop_cart.pic_path = sku.product.pic_path
            new_shop_cart.title = sku.product.name
            new_shop_cart.remain_time = datetime.datetime.now() + datetime.timedelta(minutes=20)
            new_shop_cart.save()
            for cart in queryset:
                cart.remain_time = datetime.datetime.now() + datetime.timedelta(minutes=20)
                cart.save(update_fields=['remain_time'])
            return Response({"result": "2", "code": 0, "info": "添加成功"})  # 购物车没有
        else:
            return Response({"result": "error", "code": 3, "info": "参数异常"})  # 未知错误

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def show_carts_num(self, request, *args, **kwargs):
        """显示购物车的数量和保留时间"""
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        queryset = queryset.order_by('-created')
        count = 0
        last_created = 0
        if queryset.count() > 0:
            last_created = time.mktime(queryset[0].remain_time.timetuple())
        for item in queryset:
            count += item.num
        return Response({"result": count, "last_created": last_created})

    @list_route(methods=['get'])
    def show_carts_history(self, request, *args, **kwargs):
        """显示该用户28个小时内购物清单历史 """
        before = datetime.datetime.now() - datetime.timedelta(hours=28)
        customer = get_object_or_404(Customer, user=request.user)
        queryset = ShoppingCart.objects.filter(buyer_id=customer.id, status=ShoppingCart.CANCEL,
                                               modified__gt=before).order_by('-modified')
        serializers = self.get_serializer(queryset, many=True)
        return Response(serializers.data)

    @detail_route(methods=['post', 'delete'])
    def delete_carts(self, request, pk=None, *args, **kwargs):
        """关闭购物车中的某一个数据，调用关闭接口"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"code": 0, "info": "OK"}, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.close_cart()

    @detail_route(methods=['post'])
    @transaction.atomic
    def plus_product_carts(self, request, pk=None):
        customer = get_object_or_404(Customer, user=request.user)
        cart_item = get_object_or_404(ShoppingCart, pk=pk, buyer_id=customer.id, status=ShoppingCart.NORMAL)
        sku = get_object_or_404(ProductSku, pk=cart_item.sku_id)
        # user_skunum = getUserSkuNumByLast24Hours(customer, sku)
        lockable = Product.objects.isQuantityLockable(sku, 1)
        if not lockable:
            raise exceptions.APIException(u'商品数量限购')
        lock_success = Product.objects.lockQuantity(sku, 1)
        if not lock_success:
            raise exceptions.APIException(u'商品库存不足')
        cart = ShoppingCart.objects.filter(id=pk).first()
        cart.num = models.F('num') + 1
        cart.total_fee = models.F('num') * cart_item.price
        cart.save(update_fields=['num','total_fee'])

        return Response({"code":0, "status": 1})

    @detail_route(methods=['post'])
    @transaction.atomic
    def minus_product_carts(self, request, pk=None, *args, **kwargs):
        cart_item = get_object_or_404(ShoppingCart, pk=pk)
        if cart_item.num <= 1:
            raise exceptions.APIException(u'至少购买一件')

        cart = ShoppingCart.objects.filter(id=pk).first()
        cart.num = models.F('num') - 1
        cart.total_fee = models.F('num') * cart_item.price
        cart.save()

        sku = ProductSku.objects.filter(pk=cart_item.sku_id).first()
        Product.objects.releaseLockQuantity(sku, 1)
        return Response({"code": 0 ,"status": 1})

    @list_route(methods=['post'])
    def sku_num_enough(self, request, *args, **kwargs):
        """ 规格数量是否充足 """
        sku_id = request.REQUEST.get('sku_id', '')
        sku_num = request.REQUEST.get('sku_num', '')
        if not sku_id.isdigit() or not sku_num.isdigit():
            raise exceptions.APIException(u'规格ID或数量有误')
        sku_num = int(sku_num)
        # customer = get_object_or_404(Customer, user=request.user)
        sku = get_object_or_404(ProductSku, pk=sku_id)
        # user_skunum = getUserSkuNumByLast24Hours(customer, sku)
        lockable = Product.objects.isQuantityLockable(sku, sku_num)
        if not lockable:
            raise exceptions.APIException(u'商品数量限购')
        if sku.free_num < sku_num:
            raise exceptions.APIException(u'库存不足赶快下单')
        return Response({"code": 0, "sku_id": sku_id, "sku_num": sku_num})

    def get_budget_info(self, customer, payment):
        user_budgets = UserBudget.objects.filter(user=customer)
        if user_budgets.exists():
            user_budget = user_budgets[0]
            return user_budget.budget_cash >= payment, user_budget.budget_cash
        return False, 0

    def get_payextras(self, request, resp):
        extras = []
        # 优惠券
        extras.append(CONS.PAY_EXTRAS.get(CONS.ETS_COUPON))
        # APP减两元
        extras.append(CONS.PAY_EXTRAS.get(CONS.ETS_APPCUT))
        # 余额
        budget_cash = resp['channels'][0]['budget_cash']
        if budget_cash > 0 and resp['total_payment'] > 0:
            budgets = CONS.PAY_EXTRAS.get(CONS.ETS_BUDGET)
            budgets.update(value=min(budget_cash, resp['total_payment']))
            extras.append(budgets)
        return extras

    def get_logistics_by_shoppingcart(self, queryset):
        ware_by = None
        for sc in queryset:
            product = Product.objects.filter(id=sc.item_id).first()
            if product and ware_by is None:
                ware_by = product.ware_by
                continue
            if product:
                ware_by &= product.ware_by
        return ware_by or Product.WARE_NONE

    def get_selectable_logistics(self, ware_by, default_company_code=''):
        logistics = LogisticsCompany.get_logisticscompanys_by_warehouse(ware_by)
        logistics = logistics.values('id','code','name')
        lg_dict_list = [{'id':'0', 'code':'', 'name':u'自动分配', 'is_priority':True}]
        has_use_default = False
        for lg in logistics:
            lg['is_priority'] = lg['code'] == default_company_code
            has_use_default |= lg['is_priority']
            lg_dict_list.append(lg)
        if has_use_default:
            lg_dict_list[0]['is_priority'] = False
        return lg_dict_list

    def get_charge_channels(self, request, total_payment):
        content = request.REQUEST
        is_in_weixin = is_from_weixin(request)
        is_in_wap    = content.get('device','wap') == 'wap'

        customer = self.get_customer(request)
        channel_list = []
        budget_payable, budget_cash = self.get_budget_info(customer, total_payment)
        channel_list.append({'id': 'budget', 'name':u'小鹿钱包', 'payable': budget_payable ,'msg':'', 'budget_cash':budget_cash})
        if is_in_wap :
            if is_in_weixin:
                channel_list.append({'id': 'wx_pub', 'name':u'微信支付', 'payable': True ,'msg':''})
            channel_list.append({'id': 'alipay_wap', 'name':u'支付宝', 'payable': True, 'msg': ''})
        else:
            channel_list.append({'id': 'wx', 'name':u'微信支付', 'payable':True, 'msg':''})
            channel_list.append({'id': 'alipay', 'name':u'支付宝', 'payable': True, 'msg': ''})

        return channel_list

    @list_route(methods=['get', 'post'])
    def carts_payinfo(self, request, format=None, *args, **kwargs):
        """ 根据购物车ID列表获取支付信息 """
        content = request.GET
        cartid_str = content.get('cart_ids', '')
        cart_ids = [int(i) for i in cartid_str.split(',') if i.isdigit()]
        queryset = self.get_owner_queryset(request).filter(id__in=cart_ids)
        if not cart_ids or len(cart_ids) != queryset.count():
            raise exceptions.APIException(u'购物车已失效请重新加入')

        total_fee = 0
        discount_fee = 0
        post_fee = 0
        for cart in queryset:
            total_fee += cart.price * cart.num

        xlmm = None
        customer = self.get_customer(request)
        if customer and customer.unionid.strip():
            xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
            xlmm = xiaolumms.count() > 0 and xiaolumms[0] or None

        for cart in queryset:
            discount_fee += cart.calc_discount_fee(xlmm=xlmm)

        discount_fee = min(discount_fee, total_fee)
        total_payment = total_fee + post_fee - discount_fee

        ware_by = self.get_logistics_by_shoppingcart(queryset)
        default_address = customer.get_default_address()
        selectable_logistics = self.get_selectable_logistics(
            ware_by,
            default_company_code=default_address.logistic_company_code)

        cart_serializers = self.get_serializer(queryset, many=True)

        response = {
            'uuid': gen_uuid_trade_tid(),
            'total_fee': round(total_fee, 2),
            'post_fee': round(post_fee, 2),
            'discount_fee': round(discount_fee, 2),
            'total_payment': round(total_payment, 2),
            'channels': self.get_charge_channels(request, total_payment),
            'cart_ids': ','.join([str(c) for c in cart_ids]),
            'cart_list': cart_serializers.data,
            'logistics_companys': selectable_logistics
        }
        response.update({'pay_extras': self.get_payextras(request, response)})
        return Response(response)

    @list_route(methods=['get', 'post'])
    def now_payinfo(self, request, format=None, *args, **kwargs):
        """ 根据购物车ID列表获取支付信息 """
        content = request.GET
        sku_id = content.get('sku_id', '')
        product_sku = ProductSku.objects.filter(id=sku_id).first()
        if not product_sku :
            raise exceptions.APIException(u'参数错误')

        discount_fee = 0
        post_fee = 0
        total_fee = product_sku.agent_price

        xlmm = None
        customer = self.get_customer(request)
        if customer and customer.unionid.strip():
            xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
            xlmm = xiaolumms.count() > 0 and xiaolumms[0] or None

        discount_fee += product_sku.calc_discount_fee(xlmm=xlmm)

        discount_fee = min(discount_fee, total_fee)
        total_payment = total_fee + post_fee - discount_fee

        product = product_sku.product
        ware_by = product.ware_by
        default_address = customer.get_default_address()
        selectable_logistics = self.get_selectable_logistics(
            ware_by,
            default_company_code=default_address.logistic_company_code)

        product_sku_dict = serializers.ProductSkuSerializer(product_sku).data
        product_sku_dict['product'] = serializers.ProductSerializer(
            product,
            context={'request': request}).data

        response = {
            'uuid': gen_uuid_trade_tid(),
            'total_fee': round(total_fee, 2),
            'post_fee': round(post_fee, 2),
            'discount_fee': round(discount_fee, 2),
            'total_payment': round(total_payment, 2),
            'channels': self.get_charge_channels(request, total_payment),
            'sku': product_sku_dict,
            'logistics_companys': selectable_logistics
        }
        response.update({'pay_extras': self.get_payextras(request, response)})
        return Response(response)


class SaleTradeViewSet(viewsets.ModelViewSet):
    """
    ###特卖订单REST API接口：
    - payment (实付金额) = total_fee (商品总金额) + post_fee (邮费) - discount_fee (优惠金额)
    - {path}/waitpay[.formt]:获取待支付订单；
    - {path}/waitsend[.formt]:获取待发货订单；
    - {path}/confirm_sign[.formt]: 确认收货
    - {path}/remind_send[.formt]: 提醒发货
    - {path}/undisplay[.formt]: 删除订单记录
    - {path}/{pk}/charge[.formt]:支付待支付订单;
    - {path}/shoppingcart_create[.formt]:pingpp创建订单接口
    > - cart_ids：购物车明细ID，如 `100,101,...` 
    > - addr_id:客户地址ID
    > - channel:支付方式
    > - payment：付款金额
    > - post_fee：快递费用
    > - discount_fee：优惠折扣
    > - total_fee：总费用
    > - pay_extras：附加支付参数，pid:1:value:2;pid:2:value:3:conponid:2
    > - uuid：系统分配唯一ID
    > - 返回结果：{'code':0,'info':'ok','charge':{...}},请求成功code=0,失败code大于0,错误信息info 
    - {path}/buynow_create[.formt]:立即支付订单接口
    > - item_id：商品ID，如 `100,101,...` 
    > - sku_id:规格ID
    > - num:购买数量
    > - pay_extras：附加支付参数，pid:1:value:2;pid:2:value:3:conponid:2
    > - 其它参数(不包含cart_ids)如上
    """
    queryset = SaleTrade.objects.all()
    serializer_class = serializers.SaleTradeSerializer# Create your views here.
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    filter_fields = ('tid',)
    paginate_by = 15
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    
    def get_owner_queryset(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        return self.queryset.filter(buyer_id=customer.id,
                                    status__lt=SaleTrade.TRADE_CLOSED_BY_SYS).order_by('-created')
    
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
        serializer = serializers.SaleTradeDetailSerializer(instance,context={'request': request})
        return Response(serializer.data)
    
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
        coupon_id = sale_trade.extras_info.get('coupon')
        if coupon_id:
            user_coupon = UserCoupon.objects.get(id=coupon_id, customer_id=sale_trade.buyer_id)
            user_coupon.coupon_basic_check()  # 优惠券基础检查
            user_coupon.use_coupon(sale_trade.tid)  # 使用优惠券

    def wallet_charge(self, sale_trade):
        """ 妈妈钱包支付实现 """
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
            cash__gte=payment).update(cash=models.F('cash')-payment)
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
        return {'channel':channel,'success':True,'id':sale_trade.id,'info':'订单支付成功'}
    
    def budget_charge(self, sale_trade):
        """ 小鹿钱包支付实现 """
        self.check_before_charge(sale_trade)
        
        buyer         = Customer.objects.get(pk=sale_trade.buyer_id)
        payment       = round(sale_trade.payment * 100) 
        strade_id     = sale_trade.id
        channel       = sale_trade.channel
        
        urows = UserBudget.objects.filter(user=buyer, amount__gte=payment)
        logger.info('budget charge:uid=%s, tid=%s, payment=%.2f'%(sale_trade.buyer_id, sale_trade.tid, payment))
        if not urows.exists():
            raise Exception(u'小鹿钱包余额不足')
        
        BudgetLog.objects.create(customer_id=buyer.id,
                                referal_id=strade_id,
                                flow_amount=payment,
                                budget_log_type=BudgetLog.BG_CONSUM,
                                budget_type=BudgetLog.BUDGET_OUT,
                                status=BudgetLog.CONFIRMED)
        #确认付款后保存
        confirmTradeChargeTask.delay(strade_id)
        return {'channel':channel,'success':True,'id':sale_trade.id,'info':'订单支付成功'}
    
    def pingpp_charge(self, sale_trade, **kwargs):
        """ pingpp支付实现 """
        self.check_before_charge(sale_trade)
        
        payment       = round(sale_trade.get_cash_payment() * 100)
        order_no      = sale_trade.tid
        buyer_openid  = sale_trade.openid
        channel       = sale_trade.channel
        payback_url = urlparse.urljoin(settings.M_SITE_URL,kwargs.get('payback_url','/pages/zhifucg.html'))
        cancel_url  = urlparse.urljoin(settings.M_SITE_URL,kwargs.get('cancel_url','/pages/daizhifu-dd.html'))
        if sale_trade.has_budget_paid:
            ubudget = UserBudget.objects.get(user=sale_trade.buyer_id)
            budget_charge_create = ubudget.charge_pending(sale_trade.id, sale_trade.budget_payment)
            if not budget_charge_create:
                raise Exception('用户余额不足')
        
        extra = {}
        if channel == SaleTrade.WX_PUB:
            extra = {'open_id':buyer_openid,'trade_type':'JSAPI'}
        
        elif channel == SaleTrade.ALIPAY_WAP:
            extra = {"success_url":payback_url,
                     "cancel_url":cancel_url}
        
        elif channel == SaleTrade.UPMP_WAP:
            extra = {"result_url":payback_url}
        
        params ={ 'order_no':'%s'%order_no,
                  'app':dict(id=settings.PINGPP_APPID),
                  'channel':channel,
                  'currency':'cny',
                  'amount':'%d'%payment,
                  'client_ip':settings.PINGPP_CLENTIP,
                  'subject':u'小鹿美美平台交易',
                  'body':u'订单ID(%s),订单金额(%.2f)'%(sale_trade.id,sale_trade.payment),
                  'metadata':dict(color='red'),
                  'extra':extra}
        charge = pingpp.Charge.create(api_key=settings.PINGPP_APPKEY,**params)
        sale_trade.charge = charge.id
        update_model_fields(sale_trade,update_fields=['charge'])
        return charge

    def get_mama_referal_params(self, request):
        form = request.REQUEST
        mama_linkid = form.get('mm_linkid', None)
        ufrom = form.get('ufrom', '0')
        if not mama_linkid:
            cookies = request.COOKIES
            mama_linkid = cookies.get('mm_linkid', 0)
            ufrom = cookies.get('ufrom', '')
        return {'mm_linkid': mama_linkid, 'ufrom': ufrom}


    def create_Saletrade(self, request, form, address, customer):
        """ 创建特卖订单方法 """
        tuuid = form.get('uuid')
        assert UUID_RE.match(tuuid), u'订单UUID异常'
        sale_trade,state = SaleTrade.objects.get_or_create(tid=tuuid,
                                                           buyer_id=customer.id)
        assert sale_trade.status in (SaleTrade.WAIT_BUYER_PAY,SaleTrade.TRADE_NO_CREATE_PAY), u'订单不可支付'
        channel = form.get('channel')
        params = {
            'channel':channel,
            'receiver_name':address.receiver_name,
            'receiver_state':address.receiver_state,
            'receiver_city':address.receiver_city,
            'receiver_district':address.receiver_district,
            'receiver_address':address.receiver_address,
            'receiver_zip':address.receiver_zip,
            'receiver_phone':address.receiver_phone,
            'receiver_mobile':address.receiver_mobile,
            }
        if state:
            buyer_openid = options.get_openid_by_unionid(customer.unionid,settings.WXPAY_APPID)
            buyer_openid = buyer_openid or customer.openid
            payment      = float(form.get('payment'))
            pay_extras   = form.get('pay_extras','')
            budget_payment = self.calc_extra_budget(pay_extras)
            coupon_id  = form.get('coupon_id','')
            couponids  = re.compile('.*couponid:(?P<couponid>\d+):').match(pay_extras)
            if couponids:
                coupon_id = couponids.groupdict().get('couponid','')
            params.update({
                'buyer_nick':customer.nick,
                'buyer_message':form.get('buyer_message',''),
                'payment':payment,
                'pay_cash':max(0, round(payment * 100 - budget_payment) / 100.0),
                'has_budget_paid':budget_payment > 0,
                'total_fee':float(form.get('total_fee')),
                'post_fee':float(form.get('post_fee')),
                'discount_fee':float(form.get('discount_fee')),
                'charge':'',
                'status':SaleTrade.WAIT_BUYER_PAY,
                'openid':buyer_openid,
                'extras_info':{'coupon': coupon_id,
                               'pay_extras':pay_extras}
                })
            params['extras_info'].update(self.get_mama_referal_params(request))
        for k,v in params.iteritems():
            hasattr(sale_trade,k) and setattr(sale_trade,k,v)
        sale_trade.save()
        if state:
            from django_statsd.clients import statsd
            statsd.incr('xiaolumm.prepay_count')
            statsd.incr('xiaolumm.prepay_amount',sale_trade.payment)
        return sale_trade,state
    
    def create_Saleorder_By_Shopcart(self,saletrade,cart_qs):
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
        """ pid:1:value:2;pid:2:value:3:conponid:2 """
        if not pay_extras:
            return []
        pay_list = [e for e in re.split(',|;',pay_extras) if e.strip()]
        extra_list = []
        already_exists_pids   = []
        for k in pay_list:
            pdict = {}
            keys = k.split(':')
            for i in range(0,len(keys) / 2):
                pdict.update({keys[2*i]:keys[2*i+1]})
            if pdict.has_key('pid') and pdict['pid'] not in already_exists_pids:
                extra_list.append(pdict)
                already_exists_pids.append(pdict['pid'])
        return extra_list

    def calc_counpon_discount(self, coupon_id, item_ids, buyer_id, payment, **kwargs):
        """ payment（单位分）按原始支付金额计算优惠信息 """
        user_coupon = get_object_or_404(UserCoupon, id=coupon_id, customer_id=buyer_id, status=UserCoupon.UNUSED)
        user_coupon.check_user_coupon(product_ids=item_ids, use_fee=payment / 100.0)
        return round(user_coupon.value * 100)
    
    def calc_extra_discount(self, pay_extras, **kwargs):
        """　优惠信息(分) """
        pay_extra_list = self.parse_entry_params(pay_extras)
        discount_fee = 0
        for param in pay_extra_list:
            pid = param['pid']
            if pid == CONS.ETS_COUPON and CONS.PAY_EXTRAS[pid].get('type') == CONS.DISCOUNT:
                if not param.has_key('couponid') or not param['couponid'].isdigit():
                    raise Exception('请传入合法的couponid')
                coupon_id  = int(param['couponid'])
                discount_fee += self.calc_counpon_discount(coupon_id,**kwargs)
            if pid == CONS.ETS_APPCUT and CONS.PAY_EXTRAS[pid].get('type') == CONS.DISCOUNT:
                discount_fee += CONS.PAY_EXTRAS[pid]['value'] * 100
        return discount_fee
    
    def calc_extra_budget(self, pay_extras, **kwargs):
        """　支付余额(分) """
        pay_extra_list = self.parse_entry_params(pay_extras)
        pay_extra_dict = dict([(p['pid'],p) for p in pay_extra_list if p.has_key('pid')])
        budget_amount = 0
        for param in pay_extra_dict.values():
            pid = param['pid']
            if pid in CONS.PAY_EXTRAS and CONS.PAY_EXTRAS[pid].get('type') == CONS.BUDGET:
                budget_amount += round(float(param['budget']) * 100)
        return budget_amount
            
    @list_route(methods=['post'])
    def shoppingcart_create(self, request, *args, **kwargs):
        """ 购物车订单支付接口 """
        CONTENT  = request.REQUEST
        tuuid    = CONTENT.get('uuid')
        customer = get_object_or_404(Customer,user=request.user)
        try:
            SaleTrade.objects.get(tid=tuuid,buyer_id=customer.id)
        except SaleTrade.DoesNotExist:
            cart_ids = [i for i in CONTENT.get('cart_ids','').split(',')]
            cart_qs = ShoppingCart.objects.filter(
                id__in=[i for i in cart_ids if i.isdigit()], 
                buyer_id=customer.id
            )
            #这里不对购物车状态进行过滤，防止订单创建过程中购物车状态发生变化
            if cart_qs.count() != len(cart_ids):
                logger.warn('debug cart v1:content_type=%s,params=%s,cart_qs=%s' % (request.META.get('CONTENT_TYPE', ''), request.REQUEST, cart_qs.count()))
                return Response({'code':1, 'info':u'购物车已结算'})
            xlmm            = self.get_xlmm(request)
            total_fee       = round(float(CONTENT.get('total_fee','0')) * 100)
            payment         = round(float(CONTENT.get('payment','0')) * 100)
            post_fee        = round(float(CONTENT.get('post_fee','0')) * 100)
            discount_fee    = round(float(CONTENT.get('discount_fee','0')) * 100)
            pay_extras      = CONTENT.get('pay_extras')
            cart_total_fee  = 0
            cart_discount   = 0

            item_ids = []
            for cart in cart_qs:
                if not cart.is_good_enough():
                    return Response({'code':2, 'info':u'商品已被抢光了'})
                cart_total_fee += cart.price * cart.num * 100
                cart_discount  += cart.calc_discount_fee(xlmm=xlmm) * cart.num * 100
                item_ids.append(cart.item_id)
                
            extra_params = {'item_ids': item_ids,
                            'buyer_id':customer.id,
                            'payment':cart_total_fee - cart_discount}
            try:
                cart_discount += self.calc_extra_discount(pay_extras,**extra_params)
            except Exception, exc:
                logger.warn('cart payment:uuid=%s,extra_params=%s'%(tuuid,extra_params),exc_info=True)
                return Response({'code':3,'info':exc.message})
            
            cart_discount = min(cart_discount, cart_total_fee)
            if discount_fee > cart_discount:
                logger.warn('cart discount err:params=%s'%(request.REQUEST))
                return Response({'code':4, 'info':u'优惠金额异常'})
            
            cart_payment = cart_total_fee + post_fee - cart_discount
            if (post_fee < 0 or payment < 0  or abs(payment - cart_payment) > 10 
                or abs(total_fee - cart_total_fee) > 10):
                logger.warn('cart payment err:params=%s'%(request.REQUEST))
                return Response({'code':4, 'info':u'付款金额异常'})
            
        addr_id  = CONTENT.get('addr_id')
        address  = get_object_or_404(UserAddress,id=addr_id,cus_uid=customer.id)
        
        channel  = CONTENT.get('channel')
        if channel not in dict(SaleTrade.CHANNEL_CHOICES):
            return Response({'code':5, 'info':u'付款方式有误'})

        with transaction.atomic():
            sale_trade,state = self.create_Saletrade(request, CONTENT, address, customer)
            if state:
                self.create_Saleorder_By_Shopcart(sale_trade, cart_qs)
        
        try:
            if channel == SaleTrade.WALLET:
                # 妈妈钱包支付 2016-4-23 关闭代理钱包支付功能
                return Response({'code': 7, 'info': u'妈妈钱包支付功能已取消'})
                # response_charge = self.wallet_charge(sale_trade)
            elif channel == SaleTrade.BUDGET:
                #小鹿钱包
                response_charge = self.budget_charge(sale_trade)
            else:
                #pingpp 支付
                response_charge = self.pingpp_charge(sale_trade)
        except Exception,exc:
            logger.warn('cart charge:uuid=%s,channel=%s,err=%s'%(tuuid,channel,exc.message),exc_info=True)
            return Response({'code':6, 'info':exc.message or '未知支付异常'})

        return Response({'code':0, 'info':u'支付成功', 'channel':channel, 'charge':response_charge})
            
        
    @list_route(methods=['post'])
    def buynow_create(self, request, *args, **kwargs):
        """ 立即购买订单支付接口 """
        CONTENT  = request.REQUEST
        item_id  = CONTENT.get('item_id')
        sku_id   = CONTENT.get('sku_id')
        sku_num  = int(CONTENT.get('num','1'))
        pay_extras = CONTENT.get('pay_extras')
        
        customer        = get_object_or_404(Customer,user=request.user)
        product         = get_object_or_404(Product,id=item_id)
        product_sku     = get_object_or_404(ProductSku,id=sku_id)
        total_fee       = round(float(CONTENT.get('total_fee','0')) * 100)
        payment         = round(float(CONTENT.get('payment','0')) * 100)
        post_fee        = round(float(CONTENT.get('post_fee','0')) * 100)
        discount_fee    = round(float(CONTENT.get('discount_fee','0')) * 100)
        bn_totalfee     = round(product_sku.agent_price * sku_num * 100)
        
        xlmm            = self.get_xlmm(request)
        bn_discount     = product_sku.calc_discount_fee(xlmm) * sku_num
        if product_sku.free_num < sku_num or product.shelf_status == Product.DOWN_SHELF:
            raise exceptions.ParseError(u'商品已被抢光啦！')
        
        coupon_id = CONTENT.get('coupon_id', '')
        user_coupon = None
        if coupon_id:
            # 对应用户的未使用的优惠券
            user_coupon = get_object_or_404(UserCoupon, id=coupon_id,
                                            customer_id=customer.id, status=UserCoupon.UNUSED)
            try:  # 优惠券条件检查
                check_use_fee = (bn_totalfee - bn_discount) / 100.0
                user_coupon.check_user_coupon(product_ids=[product.id, ], use_fee=check_use_fee)  # 检查消费金额是否满足
            except Exception, exc:
                raise exceptions.APIException(exc.message)
            bn_discount += round(user_coupon.value * 100)

        bn_discount += self.calc_extra_discount(pay_extras)
        bn_discount = min(bn_discount, bn_totalfee)
        if discount_fee > bn_discount:
            raise exceptions.ParseError(u'优惠金额异常')
        
        bn_payment      = bn_totalfee + post_fee - bn_discount
        if (post_fee < 0 or payment < 0 or abs(payment - bn_payment) > 10 
            or abs(total_fee - bn_totalfee) > 10):
            raise exceptions.ParseError(u'付款金额异常')
        
        addr_id  = CONTENT.get('addr_id')
        address  = get_object_or_404(UserAddress,id=addr_id,cus_uid=customer.id)
        channel  = CONTENT.get('channel')
        if channel not in dict(SaleTrade.CHANNEL_CHOICES):
            raise exceptions.ParseError(u'付款方式有误')
        
        try:
            lock_success =  Product.objects.lockQuantity(product_sku,sku_num)
            if not lock_success:
                raise exceptions.APIException(u'商品库存不足')
            with transaction.atomic():
                sale_trade,state = self.create_Saletrade(request, CONTENT, address, customer)
                if state:
                    self.create_SaleOrder_By_Productsku(sale_trade, product, product_sku, sku_num)
        except exceptions.APIException,exc:
            raise exc
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            Product.objects.releaseLockQuantity(product_sku, sku_num)
            raise exceptions.APIException(u'订单生成异常')

        if coupon_id and user_coupon:  # 使用优惠券，并修改状态
            user_coupon.use_coupon(sale_trade.tid)

        if channel == SaleTrade.WALLET:
            #妈妈钱包支付
            response_charge = self.wallet_charge(sale_trade)
        elif channel == SaleTrade.BUDGET:
            #小鹿钱包
            response_charge = self.budget_charge(sale_trade)
        else:
            #pingpp 支付
            response_charge = self.pingpp_charge(sale_trade)
        return Response(response_charge)

    @detail_route(methods=['post'])
    def charge(self, request, *args, **kwargs):
        """ 待支付订单支付 """
        _errmsg = {SaleTrade.WAIT_SELLER_SEND_GOODS: u'订单无需重复付款',
                   SaleTrade.TRADE_CLOSED_BY_SYS: u'订单已关闭或超时',
                   'default': u'订单不在可支付状态'}

        instance = self.get_object()
        if instance.status != SaleTrade.WAIT_BUYER_PAY:
            return Response({'code': 1, 'info': _errmsg.get(instance.status, _errmsg.get('default'))})

        if not instance.is_payable():
            return Response({'code': 2, 'info': _errmsg.get(SaleTrade.TRADE_CLOSED_BY_SYS)})

        if instance.channel == SaleTrade.WALLET:
            # 小鹿钱包支付
            response_charge = self.wallet_charge(instance)
        elif instance.channel == SaleTrade.BUDGET:
            # 小鹿钱包
            response_charge = self.budget_charge(instance)
        else:
            # pingpp 支付
            response_charge = self.pingpp_charge(instance)
        log_action(request.user.id, instance, CHANGE, u'重新支付')
        return Response({'code': 0, 'info': 'success', 'charge': response_charge})

    def perform_destroy(self, instance):
        # 订单不在 待付款的 或者不在创建状态
        instance.close_trade()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        log_action(request.user.id, instance, CHANGE, u'取消订单')
        return Response(data={"ok": True})

    @detail_route(methods=['post'])
    def confirm_sign(self, request, *args, **kwargs):
        """ 确认签收 """
        instance = self.get_object()
        wait_sign_orders = instance.sale_orders.filtre(status=SaleOrder.WAIT_BUYER_CONFIRM_GOODS)
        if not wait_sign_orders.exists():
            return Response({"code": 1, "info": "没有可签收订单"})

        for order in wait_sign_orders:
            order.confirm_sign_order()
            logger.info('user(:%s) confirm sign order(:s)' % (self.get_customer(request), order.oid))

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
        # TODO
        return Response({"code": 0, "info": "订单已删除"})


from flashsale.restpro.views_refund import refund_Handler

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
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_customer(self, request):
        customer = get_object_or_404(Customer, user=request.user)
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
        logger.info('user(:%s) confirm sign order(:s)'%(self.get_customer(request), instance.oid))

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
        logger.warn('user(:%s) apply refund order(:s)' % (self.get_customer(request), instance.oid))
        return Response({"code":0,"info": "success"})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
