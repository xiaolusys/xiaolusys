# coding:utf-8
from .models import Customer,SaleTrade,genTradeUniqueid
from shopback.items.models import ProductSku
from flashsale.xiaolumm.models import XiaoluMama

class PayInfoMethodMixin(object):
    """ 支付信息方法Mixin类 """
    
    def get_trade_uuid(self):
        return genTradeUniqueid()
    
    def is_from_weixin(self, request):
        if hasattr(self, '_isfromweixin'):
            return self._isfromweixin
        agent = request.META.get('HTTP_USER_AGENT', None)
        self._isfromweixin = "MicroMessenger" in agent
        return self._isfromweixin
    
    def get_user_profile(self,request):
        if hasattr(self,'_customer'):
            return self._customer
        customers = Customer.objects.filter(user=request.user)
        if customers.exists() :
            self._customer = customers[0] 
        else: 
            self._customer = None
        return self._customer
        
        
    def get_xiaolumm(self, request):
        if hasattr(self,'_xiaolumm'):
            return self._xiaolumm
        customer = self.get_user_profile(request)
        xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
        if xiaolumms.exists() :
            self._xiaolumm = xiaolumms[0] 
        else: 
            self._xiaolumm = None
        return self._xiaolumm
        
    def calc_mama_discount_fee(self, product_sku, xlmm):
        return product_sku.calc_discount_fee(xlmm=xlmm)
    
    def calc_product_sku_amount_params(self, request, product_sku, **kwargs):
        """ 计算商品规格支付信息 """
        def get_payable_channel_params(customer, xlmm, is_deposite_order, total_payment):
            wallet_payable = False
            wallet_cash    = 0 
            xlmm = self.get_xiaolumm(request)
            if xlmm:
                wallet_payable = (xlmm.cash > 0 and 
                                  total_payment >= 0 and
                                  xlmm.cash >= int(total_payment * 100) and
                                  not is_deposite_order)
                wallet_cash    = xlmm.cash_money
            weixin_payable = False
            if customer.unionid:
                weixin_payable = self.is_from_weixin(request) 
            return {'wallet_cash':wallet_cash,
                    'weixin_payable':weixin_payable,
                    'alipay_payable':True,
                    'wallet_payable':wallet_payable,
                    }
        
        product     = product_sku.product
        total_fee    = float(product_sku.agent_price) * 1
        post_fee = 0
        discount_fee = 0
        
        customer = self.get_user_profile(request)
        xlmm = self.get_xiaolumm(request)
        if xlmm:
            discount_fee = self.calc_mama_discount_fee(product_sku, xlmm)
        
        total_payment = total_fee + post_fee - discount_fee
        order_type    = SaleTrade.SALE_ORDER
        is_deposite_order  = False
        if product.is_deposite() :
            order_type = SaleTrade.DEPOSITE_ORDER  
            is_deposite_order = True
        
        payable_params = get_payable_channel_params(customer, xlmm, is_deposite_order, total_payment)
        
        return payable_params.update({
                'order_type':order_type,
                'total_fee':round(total_fee,2),
                'post_fee':round(post_fee,2),
                'discount_fee':round(discount_fee,2),
                'total_payment':round(total_payment,2),
                })
        

 
        
        