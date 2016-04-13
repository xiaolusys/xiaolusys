# coding=utf-8
from django.db.models import Sum, Q
from .models_coupon_new import UserCoupon, CouponTemplate
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
        now = datetime.datetime.now()

        templates = CouponTemplate.objects.filter(valid=True,  # 有效，　普通类型和活动类型　排除点击领取　截止时间大于当前的
                                                  type__in=(CouponTemplate.USUAL, CouponTemplate.PROMMOTION_TYPE),
                                                  deadline__gte=now).exclude(way_type=CouponTemplate.CLICK_WAY)
        tem_data = []
        for tem in templates:
            tem_data.append(model_to_dict(tem))

        return Response({'trade': trade, "templates": tem_data})

    def post(self, request):
        content = request.REQUEST
        trade_id = content.get("trade_tid", None)
        template_type = content.get("template", None)
        memo = content.get("memo", None)
        user_id = request.user.id

        trade = self.get_trade(trade_id)
        self.check_trade_status(trade)
        self.check_order_coupon(trade)
        template = self.get_template(template_type)
        self.memo_trade(user_id, trade, memo)

        kwargs = {"buyer_id": trade.buyer_id, "trade_id": trade.id, "template_id": template.id}
        ucr = UserCoupon()
        ucr.release_by_template(**kwargs)
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


def buyer_time_amount(time_from, time_to):
    """ 计算用户的某个时间段的交易金额 """
    orders = SaleOrder.objects.filter(pay_time__gte=time_from, pay_time__lt=time_to,
                                      refund_status=SaleRefund.NO_REFUND,
                                      status__in=(
                                          SaleOrder.WAIT_SELLER_SEND_GOODS,
                                          SaleOrder.WAIT_BUYER_CONFIRM_GOODS,
                                          SaleOrder.TRADE_BUYER_SIGNED,
                                          SaleOrder.TRADE_FINISHED))
    res = orders.values('sale_trade__buyer_id').annotate(s_payment=Sum('payment'))
    return res


def release_coupon_with_limit(time_from, time_to, batch):
    orders = SaleOrder.objects.filter(sale_trade__payment__gte=180.0,
                                      pay_time__gte=time_from, pay_time__lt=time_to,
                                      refund_status=SaleRefund.NO_REFUND,
                                      status__in=(
                                          SaleOrder.WAIT_SELLER_SEND_GOODS,
                                          SaleOrder.WAIT_BUYER_CONFIRM_GOODS,
                                          SaleOrder.TRADE_BUYER_SIGNED,
                                          SaleOrder.TRADE_FINISHED))
    for order in orders:
        template_id = 23
        buyer_id = str(order.sale_trade.buyer_id)
        coups = UserCoupon.objects.filter(customer=buyer_id, cp_id__template__id=template_id)
        if coups.count() >= batch:  # 如果发放过了则跳过
            continue
        coup = UserCoupon()
        coup.release_by_template(buyer_id=buyer_id,
                                 template_id=template_id)
    return


def daily_coupon_judge():
    """
     按照某天的成交金额计算发放优惠券
     3月4号运行
    """
    # 3月2号 10 点　
    date_3_2_from = datetime.datetime(2016, 3, 2, 10, 0, 0)
    date_3_2_to = datetime.datetime(2016, 3, 2, 23, 59, 59)
    batch = 1
    release_coupon_with_limit(date_3_2_from, date_3_2_to, batch)

    # 3月3号
    date_3_3_from = datetime.datetime(2016, 3, 3, 0, 0, 0)
    date_3_3_to = datetime.datetime(2016, 3, 3, 23, 59, 59)
    batch = 2
    release_coupon_with_limit(date_3_3_from, date_3_3_to, batch)

    # 3月4号 10 点
    date_3_4_from = datetime.datetime(2016, 3, 4, 0, 0, 0)
    date_3_4_to = datetime.datetime(2016, 3, 4, 10, 0, 0)
    batch = 3
    release_coupon_with_limit(date_3_4_from, date_3_4_to, batch)
    return


def release_coupon_34(time_from=None, time_to=None):
    """
    ３天以上均成交１８０元以上的订单
    3月４号运行
    """
    date_3_2_from = datetime.datetime(2016, 3, 2, 10, 0, 0)
    date_3_4_to = datetime.datetime(2016, 3, 4, 10, 0, 0)
    if time_from is None:
        time_from = date_3_2_from
    if time_to is None:
        time_to = date_3_4_to

    trades = SaleTrade.objects.filter(
        pay_time__gte=time_from, pay_time__lt=time_to,
        status__in=(SaleTrade.WAIT_SELLER_SEND_GOODS,
                    SaleTrade.WAIT_BUYER_CONFIRM_GOODS,
                    SaleTrade.TRADE_BUYER_SIGNED,
                    SaleTrade.TRADE_FINISHED))
    res = trades.values('buyer_id').annotate(s_payment=Sum('payment'))

    def filter_item(item):
        if item.get('s_payment') >= 540:  # 180*3天
            return item

    result = filter(filter_item, res)
    print "满足条件人数:", len(result)
    count = 0
    for i in result:
        coupon = UserCoupon()
        ss = coupon.release_by_template(buyer_id=i['buyer_id'], template_id=24)
        if ss == 'success':
            count += 1
    print "发放优惠券张数：", count
    return
