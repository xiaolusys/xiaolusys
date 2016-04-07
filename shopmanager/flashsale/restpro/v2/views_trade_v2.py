# coding:utf-8
import re
import json
import pingpp
import urlparse

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
    UserCoupon,
)

from flashsale.restpro import permissions as perms
from flashsale.restpro import serializers 
from flashsale.restpro.exceptions import rest_exception
from shopback.items.models import Product, ProductSku
from shopback.base import log_action, ADDITION, CHANGE
from shopapp.weixin import options
from common.utils import update_model_fields
from flashsale.restpro import constants as CONS

from flashsale.xiaolumm.models import XiaoluMama,CarryLog
from flashsale.pay.tasks import confirmTradeChargeTask

import logging
logger = logging.getLogger(__name__)


UUID_RE = re.compile('^[a-z]{2}[0-9]{6}[a-z0-9-]{10,14}$')

class SaleTradeViewSet(viewsets.ModelViewSet):
    """
    ###特卖订单REST API接口：
    - payment (实付金额) = total_fee (商品总金额) + post_fee (邮费) - discount_fee (优惠金额)
    - {path}/waitpay[.formt]:获取待支付订单；
    - {path}/waitsend[.formt]:获取待发货订单；
    - {path}/{pk}/charge[.formt]:支付待支付订单;
    - {path}/{pk}/details[.formt]:获取订单及明细；
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
        return self.queryset.filter(buyer_id=customer.id).order_by('-created')
    
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
    
    @detail_route(methods=['get'])
    def details(self, request, pk, *args, **kwargs):
        """ 获取用户订单及订单明细列表 """
        strade   = self.get_object()
        strade_dict = serializers.SaleTradeSerializer(strade,context={'request': request}).data
#         orders_serializer = serializers.SaleOrderSerializer(strade.sale_orders.all(), many=True)
#         strade_dict['orders'] = orders_serializer.data
        return Response(strade_dict)
    
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
            coupon  = UserCoupon.objects.get(id=coupon_id, customer=str(sale_trade.buyer_id))
            if coupon.status != UserCoupon.UNUSED:
                raise Exception('选择的优惠券不可用')

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
        
        urows = UserBudget.objects.filter(
                user=buyer,
                amount__gte=payment
            ).update(amount=models.F('amount') - payment)
        logger.info('budget charge:saletrade=%s, updaterows=%d'%(sale_trade, urows))
        if urows == 0 :
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
    
    @transaction.atomic
    def create_Saletrade(self,form,address,customer):
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
                'extras_info':{'mm_linkid':form.get('mm_linkid','0'),
                               'ufrom':form.get('ufrom',''),
                               'coupon': coupon_id,
                               'pay_extras':pay_extras}
                })
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
    
    def calc_counpon_discount(self, coupon_id, item_ids, buyer_id, payment,**kwargs):
        """ payment（单位分）按原始支付金额计算优惠信息 """
        coupon       = get_object_or_404(UserCoupon, 
                                         id=coupon_id, 
                                         customer=str(buyer_id),
                                         status=UserCoupon.UNUSED)
        
        coupon.check_usercoupon(product_ids=item_ids, use_fee=payment / 100.0)
        coupon_pool = coupon.cp_id
        
        return round(coupon_pool.template.value * 100)
    
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
            logger.warn('debug cart:params=%s,cart_qs=%s' % (request.REQUEST,cart_qs.count()))
            if cart_qs.count() != len(cart_ids):
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
                
            extra_params = {'item_ids':','.join(item_ids),
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
        
        sale_trade,state = self.create_Saletrade(CONTENT, address, customer)
        if state:
            self.create_Saleorder_By_Shopcart(sale_trade, cart_qs)
        
        try:
            if channel == SaleTrade.WALLET:
                #妈妈钱包支付
                response_charge = self.wallet_charge(sale_trade)
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
        
        coupon_id = CONTENT.get('coupon_id','')
        if coupon_id:
            # 对应用户的未使用的优惠券
            coupon       = get_object_or_404(UserCoupon, id=coupon_id, 
                                             customer=str(customer.id),
                                             status=UserCoupon.UNUSED)
            try:  # 优惠券条件检查
                check_use_fee = (bn_totalfee - bn_discount) / 100.0
                coupon.check_usercoupon(product_ids=[product.id, ], use_fee=check_use_fee)
                # coupon.cp_id.template.usefee_check((bn_totalfee - bn_discount) / 100.0)  # 检查消费金额是否满足
                coupon_pool = coupon.cp_id
            except Exception, exc:
                raise exceptions.APIException(exc.message)
            bn_discount += round(coupon_pool.template.value * 100)
        
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
            sale_trade,state = self.create_Saletrade(CONTENT, address, customer)
            if state:
                self.create_SaleOrder_By_Productsku(sale_trade, product, product_sku, sku_num)
        except exceptions.APIException,exc:
            raise exc
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            Product.objects.releaseLockQuantity(product_sku, sku_num)
            raise exceptions.APIException(u'订单生成异常')
        #使用优惠券，并修改状态
        if coupon_id and coupon:
            coupon.status = UserCoupon.USED
            coupon.sale_trade = sale_trade.id
            coupon.save()
        
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
        _errmsg = {SaleTrade.WAIT_SELLER_SEND_GOODS:u'订单无需重复付款',
                   SaleTrade.TRADE_CLOSED_BY_SYS:u'订单已关闭或超时',
                   'default':u'订单不在可支付状态'}
        
        instance = self.get_object()
        if instance.status != SaleTrade.WAIT_BUYER_PAY:
            return Response({'code':1,'info':_errmsg.get(instance.status,_errmsg.get('default'))})
        
        if not instance.is_payable():
            return Response({'code':2,'info':_errmsg.get(SaleTrade.TRADE_CLOSED_BY_SYS)})
        
        if instance.channel == SaleTrade.WALLET:
            #小鹿钱包支付
            response_charge = self.wallet_charge(instance)
        elif instance.channel == SaleTrade.BUDGET:
            #小鹿钱包
            response_charge = self.budget_charge(instance)
        else:
            #pingpp 支付
            response_charge = self.pingpp_charge(instance)
        log_action(request.user.id, instance, CHANGE, u'重新支付')
        return Response({'code':0,'info':'success','charge':response_charge})
    
    def perform_destroy(self, instance):
        # 订单不在 待付款的 或者不在创建状态
        instance.close_trade()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        log_action(request.user.id, instance, CHANGE, u'通过接口程序－取消订单')
        return Response(data={"ok": True})
    
    