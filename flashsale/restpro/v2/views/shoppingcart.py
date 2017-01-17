# coding=utf-8
import re
import time
import datetime

from django.db import models, IntegrityError
from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions

from common.auth import WeAppAuthentication
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES


from flashsale.pay.models import (
    SaleTrade,
    SaleOrder,
    Customer,
    UserBudget,
    ShoppingCart,
    UserAddress,
    gen_uuid_trade_tid,
)
from flashsale.pay.models.product import ModelProduct
from flashsale.pay.apis.v1.order import get_user_skunum_by_last24hours
from flashsale.coupon.models import UserCoupon
from flashsale.restpro import permissions as perms
from .. import serializers
from shopback.items.models import Product, ProductSku
from shopback.base import log_action, ADDITION, CHANGE
from shopback.logistics.models import LogisticsCompany
from flashsale.restpro import constants as CONS

from flashsale.xiaolumm.models import XiaoluMama
from .trade import get_channel_list


import logging
logger = logging.getLogger(__name__)

class ShoppingCartViewSet(viewsets.ModelViewSet):
    """
        ## 特卖购物车REST API接口：
            请求GET类型的api直接返回数据,如果正常http状态码code==200,有异常http状态码code >= 500
            payment (实付金额) = total_fee (商品总金额) + post_fee (邮费) - discount_fee (优惠金额)
        ## [创建购物车: /rest/v2/carts/](/rest/v2/carts/):
            POST:
            {
                _method: "PUT",
                item_id: '64257',
                sku_id: '267842',
                num: '1'
            }
        ## [删除购物车: /rest/v2/carts/{{pk}}/delete_carts](/rest/v2/carts/123/delete_carts):
            POST: _method="DELETE"
        ## [增加一件: /rest/v2/carts/{{pk}}/plus_product_carts](/rest/v2/carts/123/plus_product_carts):
            POST: {}
        ## [减少一件: /rest/v2/carts/{{pk}}/minus_product_carts](/rest/v2/carts/123/minus_product_carts):
            POST: {}
        ## [显示购物车数量: /rest/v2/carts/show_carts_num](/rest/v2/carts/show_carts_num):
        ## [显示购物车历史: /rest/v2/carts/show_carts_history](/rest/v2/carts/show_carts_history):
        ## [获取商品规格数量是否充足: /rest/v2/carts/sku_num_enough](/rest/v2/carts/sku_num_enough):
            POST:
            {
                sku_id:规格ID;
                sku_num:规格数量;
            }
        ## [根据购物车记录获取支付信息: /rest/v2/carts/carts_payinfo](/rest/v2/carts/carts_payinfo):
            GET:
            {
                cart_ids：购物车ID列表,如101,102,103,...
                device :支付类型 (app ,app支付), (wap, wap支付), (web, 网页支付)
            }
        ## [获取立即支付信息: /rest/v2/carts/now_payinfo](/rest/v2/carts/now_payinfo):
            GET:
            {
               sku_id：要立即购买的商品规格ID
               num:购买的商品个数，默认为1
               device :支付类型 (app ,app支付), (wap, wap支付), (web, 网页支付)
            }
    """
    queryset = ShoppingCart.objects.all()
    serializer_class = serializers.ShoppingCartSerializer
    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = self.get_customer(request)
        if not customer:
            return self.queryset.none()
        return self.queryset.filter(buyer_id=customer.id, status=ShoppingCart.NORMAL).order_by('-created')

    def get_customer(self, request):
        if not hasattr(self,'__customer__'):
            self.__customer__ = Customer.objects.filter(user=request.user).exclude(status=Customer.DELETE).first()
        return self.__customer__

    def list(self, request, *args, **kwargs):
        """列出购物车中所有的状态为正常的数据"""
        try:
            type = int(request.GET.get('type', 0))
        except:
            type = 0
        queryset = self.filter_queryset(self.get_owner_queryset(request).filter(type=type))
        serializers = self.get_serializer(queryset, many=True)
        return Response(serializers.data)

    def create(self, request, *args, **kwargs):
        """创建购物车数据"""
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        customer = self.get_customer(request)
        if not customer:
            return Response({"code": 7, "info": u"用户未找到"})  # 登录过期

        data = request.data
        product_id = data.get("item_id", None)
        sku_id = data.get("sku_id", None)
        sku_num = data.get('num', '1')
        if not (product_id and sku_id) or not sku_num.isdigit():
            return Response({"code": 1, "info": u"参数错误"})

        product = Product.objects.filter(id=product_id).first()
        if not product or (product.detail and product.detail.is_seckill):
            return Response({"code": 2, "info": u'秒杀商品不能加购物车'})

        if not product.is_onshelf():
            return Response({"code": 3, "info": u'商品已下架'})

        # 如前端传入的参数 product_id, sku_id不一致，后端先校正再处理
        sku = ProductSku.objects.filter(id=sku_id).first()
        if sku and sku.product != product:
            sku_pname =  sku.properties_name or sku.properties_alias
            sku = product.normal_skus.filter(models.Q(properties_name=sku_pname)|models.Q(properties_alias=sku_pname)).first()

        if not sku:
            logger.error(u'购物车商品id不一致: (%s, %s), agent=%s' % (product_id, sku_id, request.META.get('HTTP_USER_AGENT')))
            return Response({"code": 8, "info": u'商品提交信息不一致'})

        sku_id = sku.id
        cart_id = data.get("cart_id", None)
        if cart_id and cart_id.isdigit():
            s_temp = ShoppingCart.objects.filter(item_id=product_id, sku_id=sku_id,
                                                 status=ShoppingCart.CANCEL, buyer_id=customer.id)
            s_temp.delete()
        type = data.get("type", 0)
        try:
            type = int(type)
        except:
            return Response({"code": 1, "info": u"type 参数错误"})
        if type not in dict(ShoppingCart.TYPE_CHOICES):
            return Response({"code": 1, "info": u"type 参数错误"})
        sku_num = int(sku_num)

        user_skunum = get_user_skunum_by_last24hours(customer, sku)
        lockable = Product.objects.isQuantityLockable(sku, sku_num + user_skunum)
        if not lockable:
            return Response({"code": 4, "info": u'该商品已限购'})
        if (type == 0) or (type == ShoppingCart.VIRTUALBUY):
            shop_cart = ShoppingCart.objects.filter(item_id=product_id, buyer_id=customer.id,
                                                    sku_id=sku_id, status=ShoppingCart.NORMAL, type=type).first()
            if shop_cart:
                # shop_cart_temp = shop_cart
                # shop_cart_temp.num = sku_num
                # shop_cart_temp.total_fee = sku_num * decimal.Decimal(sku.agent_price)
                # shop_cart_temp.save()
                return Response({"code": 6, "info": u"该商品已加入购物车"})  # 购物车已经有了

        #if sku.free_num <= 0 or not Product.objects.lockQuantity(sku, sku_num):
        if sku.free_num < sku_num:
            return Response({"code": 5, "info": u'商品库存不足'})

        new_shop_cart = ShoppingCart()
        new_shop_cart.buyer_id = customer.id
        new_shop_cart.item_id = product_id
        new_shop_cart.sku_id = sku_id
        new_shop_cart.buyer_nick = customer.nick
        new_shop_cart.type = type
        if type == ShoppingCart.TEAMBUY:
            new_shop_cart.price = sku.product.get_product_model().teambuy_price
        else:
            new_shop_cart.price = sku.agent_price
        new_shop_cart.num = sku_num
        new_shop_cart.std_sale_price = sku.std_sale_price
        new_shop_cart.total_fee = sku.agent_price * int(sku_num) if sku.agent_price else 0
        new_shop_cart.sku_name = sku.name
        new_shop_cart.pic_path = product.pic_path
        new_shop_cart.title = product.name

        latest_remain_time = datetime.datetime.now() + datetime.timedelta(minutes=20)
        new_shop_cart.remain_time = latest_remain_time
        new_shop_cart.save()

        queryset.update(remain_time=latest_remain_time)

        return Response({"code": 0, "info": u"添加成功"})  # 购物车没有

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
        try:
            type = int(request.GET.get('type', 0))
        except:
            type = 0
        queryset = self.filter_queryset(self.get_owner_queryset(request).filter(type=type))
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
        queryset = ShoppingCart.objects.filter(
            buyer_id=customer.id,
            status=ShoppingCart.CANCEL,
            modified__gt=before,
            type=0
        ).order_by('-modified')

        items = list(queryset)
        for item in items:
            if item.title.startswith('RMB'):
                items.remove(item)
                continue
            product = Product.objects.filter(id=item.id).first()
            if not product:
                continue
            model_product = product.product_model
            if model_product.product_type == ModelProduct.VIRTUAL_TYPE:
                items.remove(item)

        serializers = self.get_serializer(items, many=True)
        return Response(serializers.data)

    @detail_route(methods=['post', 'delete'])
    def delete_carts(self, request, pk=None, *args, **kwargs):
        """关闭购物车中的某一个数据，调用关闭接口"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"code": 0, "info": u"删除成功"})

    def perform_destroy(self, instance):
        instance.close_cart()

    @detail_route(methods=['post'])
    @transaction.atomic
    def plus_product_carts(self, request, pk=None):
        customer = get_object_or_404(Customer, user=request.user)
        cart_item = get_object_or_404(ShoppingCart, pk=pk, buyer_id=customer.id, status=ShoppingCart.NORMAL)
        sku = get_object_or_404(ProductSku, pk=cart_item.sku_id)
        cart = get_object_or_404(ShoppingCart, pk=pk)
        user_skunum = get_user_skunum_by_last24hours(customer, sku)
        lockable = Product.objects.isQuantityLockable(sku, cart.num + user_skunum + 1)
        if not lockable:
            return Response({"code": 1, "info": u'商品数量限购'})

        lock_success = Product.objects.lockQuantity(sku, 1)
        if sku.free_num <= cart.num or not lock_success:
            return Response({"code": 2, "info": u'商品库存不足'})

        cart.num = models.F('num') + 1
        cart.total_fee = models.F('num') * cart_item.price
        cart.save(update_fields=['num','total_fee'])

        return Response({"code":0, "info": u"修改成功"})

    @detail_route(methods=['post'])
    @transaction.atomic
    def minus_product_carts(self, request, pk=None, *args, **kwargs):
        cart_item = get_object_or_404(ShoppingCart, pk=pk)
        if cart_item.num <= 1:
            return Response({"code": 1, "info": u'至少购买一件'})

        cart = ShoppingCart.objects.filter(id=pk).first()
        cart.num = models.F('num') - 1
        cart.total_fee = models.F('num') * cart_item.price
        cart.save()

        sku = ProductSku.objects.filter(pk=cart_item.sku_id).first()
        Product.objects.releaseLockQuantity(sku, 1)
        return Response({"code": 0 ,"info": u"修改成功"})

    @list_route(methods=['post'])
    def sku_num_enough(self, request, *args, **kwargs):
        """ 规格数量是否充足 """
        content = request.data
        sku_id = content.get('sku_id', '')
        sku_num = content.get('sku_num', '')
        if not sku_id.isdigit() or not sku_num.isdigit():
            return Response({"code": 1 ,"info": u'参数错误'})
        sku_num = int(sku_num)
        # customer = get_object_or_404(Customer, user=request.user)
        sku = get_object_or_404(ProductSku, pk=sku_id)
        # user_skunum = get_user_skunum_by_last24hours(customer, sku)
        lockable = Product.objects.isQuantityLockable(sku, sku_num)
        if not lockable:
            return Response({"code": 2,"info": u'商品数量限购'})
        if sku.free_num < sku_num:
            return Response({"code": 3, "info": u'库存不足'})
        return Response({"code": 0, 'info':u'库存剩下不多了', "sku_id": sku_id, "sku_num": sku_num})

    def get_budget_info(self, customer, payment):
        user_budgets = UserBudget.objects.filter(user=customer)
        if user_budgets.exists():
            user_budget = user_budgets[0]
            return user_budget.budget_cash >= payment, user_budget.budget_cash
        return False, 0

    def has_jingpinquan_product(self, product_ids):
        """
        检测购物车是否含有精品券商品
        """
        for product_id in product_ids:
            product = Product.objects.filter(id=product_id).first()
            if not product:
                continue
            model_product = product.product_model
            if model_product.is_boutique is True:
                return True
        return False

    def get_payextras(self, request, resp, product_ids):

        content = request.GET
        is_in_wap = content.get('device', 'wap') == 'wap'
        extras = []
        # 优惠券
        extras.append(CONS.PAY_EXTRAS.get(CONS.ETS_COUPON))
        # APP减两元
        if not is_in_wap:
            # 精品汇商品没有app减２元优惠, 需要返回pid, value=0防止app出错
            # if self.has_jingpinquan_product(product_ids):
            #     app_cut = CONS.PAY_EXTRAS.get(CONS.ETS_APPCUT)
            #     app_cut.update(value=0)
            #     extras.append(app_cut)
            # else:
            #     app_cut = CONS.PAY_EXTRAS.get(CONS.ETS_APPCUT)
            #     extras.append(app_cut)
            # 2016-12-19 不再有app支付立减2元
            app_cut = CONS.PAY_EXTRAS.get(CONS.ETS_APPCUT)
            app_cut.update(value=0)
            extras.append(app_cut)
        # 余额
        total_payment = resp['total_payment']
        customer = self.get_customer(request)
        budget_payable, budget_cash = self.get_budget_info(customer, total_payment)
        if budget_cash > 0 and resp['total_payment'] > 0:
            budgets = CONS.PAY_EXTRAS.get(CONS.ETS_BUDGET)
            budgets.update(value=budget_cash, use_budget_allowed=budget_payable and 1 or 0)
            extras.append(budgets)
        coins = CONS.PAY_EXTRAS.get(CONS.ETS_XIAOLUCOIN)
        coins.update(value=0, use_budget_allowed=0)
        extras.append(coins)
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
        return ware_by or WARE_NONE

    def get_selectable_logistics(self, ware_by, default_company_code=''):
        logistics = LogisticsCompany.get_logisticscompanys_by_warehouse(ware_by)
        logistics = logistics.values('id','code','name')
        lg_dict_list = [{'id':'', 'code':'', 'name':u'自动分配', 'is_priority':True}]
        has_use_default = False
        for lg in logistics:
            lg['is_priority'] = lg['code'] == default_company_code
            has_use_default |= lg['is_priority']
            lg_dict_list.append(lg)
        if has_use_default:
            lg_dict_list[0]['is_priority'] = False
        return lg_dict_list

    def get_charge_channels(self, request, total_payment):
        return get_channel_list(request, self.get_customer(request))

    def check_coupon(self, request, real_payment, cart_itemid_str):
        customer = self.get_customer(request)
        coupon_id = request.GET.get('coupon_id', '')
        if coupon_id:
            user_coupon = UserCoupon.objects.filter(id=coupon_id, customer_id=customer.id).first()
            if not user_coupon:
                raise exceptions.APIException(u'未找到该优惠券')
            try:  # 优惠券条件检查 绑定产品　和满单金额
                user_coupon.check_user_coupon(product_ids=cart_itemid_str, use_fee=real_payment)
            except Exception, exc:
                raise exceptions.APIException(exc.message)

    @list_route(methods=['get', 'post'])
    def carts_payinfo(self, request, format=None, *args, **kwargs):
        """ 根据购物车ID列表获取支付信息 """
        content = request.GET
        cartid_str = content.get('cart_ids', '')
        if not bool(re.compile('^[\d?,]+$').match(cartid_str)):
            raise exceptions.APIException(u'需要提供正确的购物车ID')
        cart_ids = [int(i) for i in cartid_str.split(',') if i.isdigit()]
        queryset = self.get_owner_queryset(request).filter(id__in=cart_ids)
        if not cart_ids or len(cart_ids) != queryset.count():
            raise exceptions.APIException(u'购物车已失效请重新加入')

        item_ids = []
        total_fee = 0
        discount_fee = 0
        post_fee = 0
        xlmm = None
        customer = self.get_customer(request)
        if customer and customer.unionid.strip():
            xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
            xlmm = xiaolumms.count() > 0 and xiaolumms[0] or None

        for cart in queryset:
            total_fee += cart.price * cart.num
            discount_fee += cart.calc_discount_fee(xlmm=xlmm)
            item_ids.append(str(cart.item_id))

        discount_fee = min(discount_fee, total_fee)
        total_payment = total_fee + post_fee - discount_fee

        real_item_payment = total_fee - discount_fee
        self.check_coupon(request, real_item_payment, ','.join(item_ids))

        ware_by = self.get_logistics_by_shoppingcart(queryset)
        default_address = customer.get_default_address()
        default_company_code = default_address and default_address.logistic_company_code or ''
        selectable_logistics = self.get_selectable_logistics(
            ware_by,
            default_company_code=default_company_code)

        cart_serializers = self.get_serializer(queryset, many=True)
        budget_payable, budget_cash = self.get_budget_info(customer, total_payment)

        response = {
            'uuid': gen_uuid_trade_tid(),
            'total_fee': round(total_fee, 2),
            'post_fee': round(post_fee, 2),
            'discount_fee': round(discount_fee, 2),
            'total_payment': round(total_payment, 2),
            'budget_cash': budget_cash,
            'channels': self.get_charge_channels(request, total_payment),
            'cart_ids': ','.join([str(c) for c in cart_ids]),
            'cart_list': cart_serializers.data,
            'logistics_companys': selectable_logistics
        }
        
        response.update({'pay_extras': self.get_payextras(request, response, item_ids)})
        return Response(response)

    @list_route(methods=['get', 'post'])
    def now_payinfo(self, request, format=None, *args, **kwargs):
        """ 立即购买获取支付信息 """
        content = request.GET
        sku_id = content.get('sku_id', '')
        sku_num = int(content.get('num', '1'))
        product_sku = ProductSku.objects.filter(id=sku_id).first()
        if not product_sku:
            raise exceptions.APIException(u'参数错误')

        discount_fee = 0
        post_fee = 0
        total_fee = product_sku.agent_price * sku_num

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
        default_company_code = default_address and default_address.logistic_company_code or ''
        selectable_logistics = self.get_selectable_logistics(
            ware_by,
            default_company_code=default_company_code)

        product_sku_dict = serializers.ProductSkuSerializer(product_sku).data
        product_sku_dict['product'] = serializers.ProductSerializer(
            product,
            context={'request': request}).data
        budget_payable, budget_cash = self.get_budget_info(customer, total_payment)

        response = {
            'uuid': gen_uuid_trade_tid(),
            'total_fee': round(total_fee, 2),
            'post_fee': round(post_fee, 2),
            'discount_fee': round(discount_fee, 2),
            'total_payment': round(total_payment, 2),
            'budget_cash': budget_cash,
            'channels': self.get_charge_channels(request, total_payment),
            'sku': product_sku_dict,
            'logistics_companys': selectable_logistics
        }
        response.update({'pay_extras': self.get_payextras(request, response, [product.id])})
        return Response(response)
