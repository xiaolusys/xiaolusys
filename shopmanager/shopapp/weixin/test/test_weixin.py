# encoding=utf8
import os
import sys
sys.path.append('.')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.settings")
# from shopapp.weixin.weixin_apis import WeiXinAPI
from shopapp.weixin.weixin_push import WeixinPush
from flashsale.pay.models.trade import SaleTrade, SaleOrder
from flashsale.pay.models.refund import SaleRefund


if __name__ == '__main__':
    import django
    django.setup()
    # api = WeiXinAPI()
    # openid = 'opNiZv0ZRVFN7zTSpKqqKv7mfUDY'
    # template_id = '0FQKLtn23GBk2MH1lYijRcXIQ3X-akznqr9Ls3M_Ka0'
    # to_url = 'http://baidu.com'
    # data = {
    #     'first': {
    #         'value': u'通知头部',
    #         'color': '#173177',
    #     },
    #     'orderMoneySum': {
    #         'value': u'138.00元',
    #         'color': '#c0392b',
    #     },
    #     'orderProductName': {
    #         'value': u'裙子标题ddd',
    #         'color': '#c0392b',
    #     },
    #     'Remark': {
    #         'value': u'\n来自小鹿妈妈订单',
    #         'color': '#173177',
    #     },
    # }
    # api.sendTemplate(openid, template_id, to_url, data)

    push = WeixinPush()
    saletrade = SaleTrade.objects.get(id=1)
    # push.push_trade_pay_notify(saletrade)
    # push.push_deliver_notify(saletrade)
    salerefund = SaleRefund.objects.get(id=11)
    push.push_refund_notify(salerefund)
