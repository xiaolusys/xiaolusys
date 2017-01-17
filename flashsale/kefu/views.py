# coding=utf-8
from __future__ import unicode_literals

from rest_framework import generics
from shopback.categorys.models import ProductCategory
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from flashsale.signals import signal_kefu_operate_record
from .tasks import task_record_kefu_performance
from flashsale.kefu.models import KefuPerformance
import datetime
from core.options import log_action, CHANGE


class KefuRecordView(generics.ListCreateAPIView):
    """
        客服绩效查看
    """
    queryset = ProductCategory.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "data2operate.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        record_type = content.get("record_type", "0")
        start_date = content.get("df", datetime.date.today().strftime("%Y-%m-%d"))
        end_date = content.get("dt", datetime.date.today().strftime("%Y-%m-%d"))
        all_type = KefuPerformance.OPERATE_TYPE
        start_task = task_record_kefu_performance.delay(start_date, end_date, record_type)
        return Response(
            {"task_id": start_task, "record_type": record_type, "start_date": start_date, "end_date": end_date,
             "all_type": all_type})


from flashsale.pay.models import SaleOrder,SaleTrade

from shopback.items.models import Product
from shopapp.smsmgr.apis import send_sms_message, SMS_TYPE
from shopapp.smsmgr.models import SMSActivity, SMS_NOTIFY_GOODS_LACK

# SEND_TEMPLATE = "您好，我是小鹿美美的客服Amy。您订购{0}{1}码 因销量火爆，厂家缺货。我们已经帮您自动退款并且补偿10元优惠券。给您带来不便非常抱歉！么么哒～"
SEND_TEMPLATE = "尊贵的{0}小主！我是小鹿客服小凳子~在这里很抱歉的告诉小主，" \
                "由于小主的眼光过于犀利，购买的{1}{2}这款宝贝严重缺货了呢。小凳子我在这里八百里加急为小主办理退款了~请小主息怒~小凳子对小主一片忠心望小主今后多多提携~【小鹿美美】"


class SendMessageView(generics.ListCreateAPIView):
    """
        客服发送短信
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "data2send.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, trade_id, order_id, *args, **kwargs):

        try:
            s_trade = SaleTrade.objects.get(id=trade_id)
            s_order = SaleOrder.objects.get(id=order_id)
            product = Product.objects.get(outer_id=s_order.outer_id)
            product_name = product.name
            receiver_name = s_trade.receiver_name
            content = SEND_TEMPLATE.format(receiver_name, product_name, s_order.sku_name)
            # 根据后台短信模板设置
            sms_tpls = SMSActivity.objects.filter(sms_type=SMS_NOTIFY_GOODS_LACK, status=True)
            if sms_tpls.exists():  # 如果有短信模板
                sms_tpl = sms_tpls[0]
                # tpl = sms_tpl.text_tmpl or SEND_TEMPLATE
                tpl = SEND_TEMPLATE
                content = tpl.format(receiver_name, product_name, s_order.sku_name)

            mobile = s_trade.receiver_mobile
            return Response({"content": content, "mobile": mobile, "trade_id": trade_id, "order_id": order_id})
        except:
            pass
            return Response({"trade_id": trade_id, "order_id": order_id})

    def post(self, request, trade_id, order_id, *args, **kwargs):
        post = request.POST
        try:
            content = post.get("content")
            mobile = post.get("mobile")
            s_trade = SaleTrade.objects.get(id=trade_id)
            s_order = SaleOrder.objects.get(id=order_id)
            if not content and not mobile or len(mobile) != 11:
                return Response({"send_result": "error"})
            log_action(request.user.id, s_trade, CHANGE, u'{0}缺货短信{1}'.format(s_order.id, mobile))

            # 此处需要创建缺货短信模板 @meron
            # send_sms_message(mobile)
        except:
            return Response({"send_result": "error"})
        return Response({"send_result": "OK"})
