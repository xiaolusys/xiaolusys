# coding=utf-8
import time
import datetime
from .models import Refund
from django.http import HttpResponse
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt

from shopback.trades.models import MergeTrade
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.views import APIView
from flashsale.pay.models import SaleRefund
import operator
from shopback.items.models import Product
from supplychain.supplier.models import SaleProduct

import logging
logger = logging.getLogger(__name__)


class RefundReason(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "refunds/refund_analysis.html"
    sale_refs = SaleRefund.objects.all()

    def time_zone(self, request):
        content = request.REQUEST
        date_from = content.get('date_from', None)
        date_to = content.get('date_to', None)
        if date_from is None or date_to is None:
            today_date = datetime.datetime.today()
            fifth_date = today_date - datetime.timedelta(days=15)
            return fifth_date, today_date
        year, month, day = map(int, date_from.split('-'))
        date_from = datetime.datetime(year, month, day, 0, 0, 0)
        year, month, day = map(int, date_to.split('-'))
        date_to = datetime.datetime(year, month, day, 23, 59, 59)
        return date_from, date_to

    def get(self, request):
        date_from, date_to = self.time_zone(request)
        refs = self.sale_refs.filter(created__gte=date_from, created__lte=date_to)
        top_re = refs.values('item_id', 'title').annotate(t_num=Sum('refund_num'))
        top_re = sorted(top_re, key=operator.itemgetter('t_num'))  # 排序
        if len(top_re) > 50:
            top_re = top_re[len(top_re) - 50:]
        # 原因占比
        top_re1 = []
        for one_re in top_re:
            try:
                one_prodcut = Product.objects.get(id=one_re['item_id'])
                one_re['item_id'] = one_prodcut.id
                one_re['pic_path'] = one_prodcut.PIC_PATH
                sale_product = SaleProduct.objects.get(id=one_prodcut.sale_product)
                one_re["contactor"] = sale_product.contactor
                one_re["supplier"] = sale_product.sale_supplier.supplier_name
            except:
                one_re["contactor"] = ""
                one_re["supplier"] = ""
            top_re1.append(one_re)
        return Response({"top_re": top_re1, "fifth_date": date_from.date(), "today": date_to.date()})

    def post(self, request):
        date_from, date_to = self.time_zone(request)
        refs = self.sale_refs.filter(created__gte=date_from, created__lte=date_to)
        # 计算退款关闭占比　
        close_refs = refs.filter(status=SaleRefund.REFUND_CLOSED)
        close_amount = close_refs.aggregate(t_amount=Sum('refund_fee')).get('t_amount') or 0
        ramount = refs.values('reason').annotate(r_amount=Sum('refund_fee'))
        rsum = refs.values('reason').annotate(r_num=Sum('refund_num'))
        mamapup_refs = refs.filter(charge='')  # charge 为空字符串的退款单（默认是小鹿钱包支付的订单）
        mamapup_amount = mamapup_refs.aggregate(mmpub_amount=Sum('refund_fee')).get('mmpub_amount') or 0
        return Response(
            {'rsum': rsum, 'ramount': ramount, 'close_amount': close_amount, "mamapup_amount": mamapup_amount})


@csrf_exempt
def refund_Invalid_Create(request):
    """
    在审核订单的时候作废了，生成对应原因的退货款单
    """
    REASON = (u"其他", u"错拍", u"缺货", u"没有发货", u"未收到货", u"与描述不符", u"七天无理由退换货")
    content = request.REQUEST

    trade_id = content.get("trade_id", None)
    reason = int(content.get("reason", None))
    try:
        trade = MergeTrade.objects.get(id=trade_id)
        # if trade.type != MergeTrade.SALE_TYPE:
        #     return HttpResponse("not sale order")

        ref = Refund()
        ref.id  = time.time() * 10 ** 2
        ref.tid = trade.tid
        ref.user = trade.user  # 店铺
        ref.buyer_nick = trade.buyer_nick  # 买家昵称
        ref.mobile = trade.receiver_mobile  # 手机
        ref.total_fee = trade.total_fee  # 总费用
        ref.payment = trade.payment  # 退款费用
        ref.company_name = trade.logistics_company and trade.logistics_company.name or ''  # 快递公司
        ref.sid = trade.out_sid  # 快递单号
        ref.reason = REASON[reason]  # 原因
        ref.order_status = trade.get_status_display()  # 订单状态
        ref.save()
        return HttpResponse("ok")
    except Exception, exc:
        logger = logging.getLogger('django.request')
        logger.error(exc.message or 'empty', exc_info=True)
        return HttpResponse('error:%s' % exc.message)
