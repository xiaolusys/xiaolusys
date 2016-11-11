# coding=utf-8
from django.db.models import Sum, Q
from flashsale.coupon.models import UserCoupon, CouponTemplate
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from django.forms import model_to_dict
from flashsale.pay.models import SaleTrade, SaleOrder, SaleRefund, Customer
from rest_framework.exceptions import APIException
from common.modelutils import update_model_fields
from core.options import log_action, CHANGE


class RefundCouponView(APIView):
    queryset = SaleTrade.objects.all()
    usercoupons = UserCoupon.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "sale/release_post_fee.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get_trade(self, tid):
        try:
            trade = SaleTrade.objects.get(tid=tid)
        except SaleTrade.DoesNotExist:
            raise APIException(u"订单未找到")
        return trade

    def memo_trade(self, user_id, trade, memo):
        """ 备注特卖订单信息　"""
        trade.seller_memo += memo
        update_model_fields(trade, update_fields=['seller_memo'])
        log_action(user_id, trade, CHANGE, u'退货退款问题发放优惠券修改卖家备注')

    def check_trade_status(self, trade):
        if trade.status in (SaleTrade.TRADE_NO_CREATE_PAY, SaleTrade.WAIT_BUYER_PAY):
            raise APIException(u'交易状态异常，不予发放')

    def get(self, request):
        content = request.REQUEST
        trade_tid = content.get("trade_tid", None)
        trade = model_to_dict(self.get_trade(trade_tid)) if trade_tid is not None else None

        templates = CouponTemplate.objects.filter(
            status=CouponTemplate.SENDING,
            coupon_type=CouponTemplate.TYPE_COMPENSATE
        ).order_by("value")

        tem_data = []
        for tem in templates:
            tem_data.append(model_to_dict(tem))

        return Response({'trade': trade, "templates": tem_data})

    def post(self, request):
        content = request.REQUEST
        trade_id = content.get("trade_tid", None)
        template_id = content.get("template_id", None)
        memo = content.get("memo", None)
        user_id = request.user.id

        trade = self.get_trade(trade_id)
        self.check_trade_status(trade)
        self.memo_trade(user_id, trade, memo)
        cou, code, msg = UserCoupon.objects.create_refund_post_coupon(trade.buyer_id,
                                                                      template_id,
                                                                      trade.id,
                                                                      ufrom='web')
        print cou, code, msg
        return Response({'res': "ok"})


class ReleaseOmissive(APIView):
    """
    补发遗漏的优惠券
    参数：优惠券模板
    用户：客户信息(用户手机号，或者用户id)
    """
    usercoupons = UserCoupon.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "sale/release_usercoupon.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        content = request.REQUEST
        buyer_id = content.get("buyer_id")
        model_ids = content.get("model_ids")
        sale_orders = []
        if buyer_id and model_ids:
            model_ids = [int(i.strip()) for i in model_ids.split(',') if i]
            from flashsale.pay.models import SaleOrder
            from shopback.items.models import Product

            item_ids = [i['id'] for i in Product.objects.filter(model_id__in=model_ids).values('id')]
            sale_orders = SaleOrder.objects.filter(item_id__in=item_ids, buyer_id=buyer_id)
        templates = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                                  coupon_type=CouponTemplate.TYPE_TRANSFER).order_by("value")
        usercoupons = []
        if buyer_id:
            usercoupons = UserCoupon.objects.filter(customer_id=buyer_id, coupon_type=CouponTemplate.TYPE_TRANSFER)
        from flashsale.pay.models import ModelProduct

        default_modelids = ModelProduct.objects.filter(product_type=1, status=ModelProduct.NORMAL).values('id')
        default_modelids = ','.join([str(m['id']) for m in default_modelids])
        return Response({'sale_orders': sale_orders,
                         "templates": templates,
                         'usercoupons': usercoupons,
                         'default_modelids': default_modelids})

    def post(self, request):
        content = request.REQUEST
        customer = content.get('buyer_id', None)
        template_id = content.get('template_id', None)
        try:
            cus = Customer.objects.get(Q(mobile=customer) | Q(pk=customer), status=Customer.NORMAL)
        except:
            return Response({'code': 2, "message": '客户不存在或重复'})
        from flashsale.pay.models import ModelProduct
        from shopback.items.models import Product
        from ..apis.v1.transfer import create_present_coupon_transfer_record

        modelids = ModelProduct.objects.filter(product_type=1, status=ModelProduct.NORMAL).values('id')
        modelids = [m['id'] for m in modelids]
        item_ids = [i['id'] for i in Product.objects.filter(model_id__in=modelids).values('id')]  # 找出虚拟产品
        # 交易成功订单
        sale_orders = SaleOrder.objects.filter(item_id__in=item_ids, buyer_id=cus.id, status=SaleOrder.TRADE_FINISHED)
        order_ids = []  # 用户的订单(一个数量为一个id)
        for order in sale_orders:
            for i in range(order.num):
                order_ids.append({'order_id': order.id, 'num': order.num})
        template = CouponTemplate.objects.get(id=template_id)
        yy = len(order_ids)
        message = u''
        for i, v in enumerate(order_ids):
            message = u'发送成功'
            x = i + 1  # 第几个订单 print '%s这是用户的第%s个订单' % (v['order_id'], x)
            y = x % 5
            if y == 0:
                yy += 1
                uni_key = template.gen_usercoupon_unikey(v['order_id'], yy)  # print '满5送1: unikey:%s' % uni_key
                try:
                    cou = UserCoupon.send_coupon(cus, template, uniq_id=uni_key)
                    create_present_coupon_transfer_record(cus, template, cou.id, v['order_id'])
                except Exception as e:
                    message = e.message
                    continue
        return Response({'code': 0, "message": message})