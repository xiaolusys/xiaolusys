# coding=utf-8
from .models_coupon_new import UserCoupon, CouponTemplate
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from django.forms import model_to_dict
from flashsale.pay.models import SaleTrade
from rest_framework.exceptions import APIException
from common.modelutils import update_model_fields
from shopback.base import log_action, CHANGE


class RefundCouponView(APIView):
    queryset = SaleTrade.objects.all()
    usercoupons = UserCoupon.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "salerefund/release_post_fee.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get_trade(self, tid):
        try:
            trade = SaleTrade.objects.get(tid=tid)
        except SaleTrade.DoesNotExist:
            raise APIException(u"订单未找到")
        return trade

    def get_template(self, template_type):
        POST_COUPON = {'POST_FEE_5': 1,
                       'POST_FEE_10': 4,
                       'POST_FEE_15': 5,
                       'POST_FEE_20': 7}
        try:
            template = CouponTemplate.objects.get(type=POST_COUPON[template_type])
        except CouponTemplate.DoesNotExist:
            raise APIException(u"优惠券未找到")
        return template

    def check_order_coupon(self, trade):
        """ 检查用户该交易是否有发放过优惠券　"""
        coupon = self.usercoupons.filter(sale_trade=trade.id, cp_id__template__type__in=(
            CouponTemplate.POST_FEE_5, CouponTemplate.POST_FEE_10, CouponTemplate.POST_FEE_15,
            CouponTemplate.POST_FEE_20))
        if coupon.exists():
            raise APIException(u"已经发放过优惠券")

    def memo_trade(self, user, trade, memo):
        """ 备注特卖订单信息　"""
        trade.seller_memo += memo
        update_model_fields(trade, update_fields=['seller_memo'])
        log_action(user, trade, CHANGE, u'退货退款问题发放优惠券修改卖家备注')

    def check_trade_status(self, trade):
        if trade.status in (SaleTrade.TRADE_NO_CREATE_PAY, SaleTrade.WAIT_BUYER_PAY):
            raise APIException(u'交易状态异常，不予发放')

    def get(self, request):
        content = request.REQUEST
        trade_tid = content.get("trade_tid", None)
        trade = model_to_dict(self.get_trade(trade_tid)) if trade_tid is not None else None
        return Response({'trade': trade})

    def post(self, request):
        content = request.REQUEST
        trade_id = content.get("trade_tid", None)
        template_type = content.get("template", None)
        memo = content.get("memo", None)
        user = request.user.id

        trade = self.get_trade(trade_id)
        self.check_trade_status(trade)
        self.check_order_coupon(trade)
        template = self.get_template(template_type)
        self.memo_trade(user, trade, memo)

        kwargs = {"buyer_id": trade.buyer_id, "trade_id": trade.id, "template_id": template.id}
        ucr = UserCoupon()
        ucr.release_by_template(**kwargs)
        return Response({'res': "ok"})
