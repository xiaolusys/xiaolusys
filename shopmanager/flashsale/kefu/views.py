# coding:utf-8
from rest_framework import generics
from shopback.categorys.models import ProductCategory
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from flashsale.signals import signal_kefu_operate_record
from .tasks import task_record_kefu_performance
from flashsale.kefu.models import KefuPerformance
import datetime
from shopback.base import log_action, CHANGE

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
        start_task = task_record_kefu_performance.s(start_date, end_date, record_type)()
        return Response(
            {"task_id": start_task, "record_type": record_type, "start_date": start_date, "end_date": end_date,
             "all_type": all_type})


from shopback.trades.models import MergeTrade, MergeOrder
from shopback.items.models import Product
from .tasks import task_send_message
SEND_TEMPLATE = "您好，我是小鹿美美的客服Amy。您买的{0}{1}码 因销售火爆断货了。由于我们是按照下单的先后顺序发货的，到您这里很不巧缺货了。要麻烦亲申请一下退款我们会及时处理。给您带来不便非常抱歉！么么哒～"
class SendMessageView(generics.ListCreateAPIView):
    """
        客服发送短信
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "data2send.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, trade_id, order_id, *args, **kwargs):

        try:
            m_trade = MergeTrade.objects.get(id=trade_id)
            m_order = MergeOrder.objects.get(id=order_id)
            product = Product.objects.get(outer_id=m_order.outer_id)
            product_name = product.name
            content = SEND_TEMPLATE.format(product_name[0], m_order.sku_properties_name)
            mobile = m_trade.receiver_mobile
            return Response({"content": content, "mobile": mobile, "trade_id": trade_id, "order_id": order_id})
        except:
            pass
            return Response({"trade_id": trade_id, "order_id": order_id})

    def post(self, request, trade_id, order_id, *args, **kwargs):
        post = request.POST
        try:
            content = post.get("content")
            mobile = post.get("mobile")
            m_trade = MergeTrade.objects.get(id=trade_id)
            m_order = MergeOrder.objects.get(id=order_id)
            if not content and not mobile or len(mobile) != 11:
                return Response({"send_result": "error"})
            log_action(request.user.id, m_trade, CHANGE, u'{0}缺货短信{1}'.format(m_order.id, mobile))
            task_send_message.s(content, mobile)()
        except:
            return Response({"send_result": "error"})
        return Response({"send_result": "OK"})
