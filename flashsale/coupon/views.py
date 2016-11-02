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

import datetime
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

    def post(self, request):
        content = request.REQUEST
        customer = content.get('customer_info', None)
        template_ids = content.get('template_ids', None)

        if template_ids is None:
            return Response({'code': 3, 'message': '请填选用户和优惠券'})  # 参数缺失
        try:
            cus = Customer.objects.get(Q(mobile=customer) | Q(pk=customer), status=Customer.NORMAL)
        except:
            return Response({'code': 2, "message": '客户不存在或重复'})
        cou = UserCoupon()
        message = 'custoemr:%s -' % str(cus.id)
        template_ids = template_ids.split('-')
        for templeate in template_ids:
            res = cou.release_by_template(buyer_id=cus.id, template_id=templeate) or ''
            message += res + '-'
        return Response({'code': 0, "message": message})
