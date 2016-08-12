# encoding=utf8
import logging
from django.conf import settings
from shopapp.weixin.weixin_apis import WeiXinAPI
from shopapp.weixin.options import get_openid_by_unionid


logger = logging.getLogger('service')


class WeixinPush(object):

    def __init__(self):
        self.api = WeiXinAPI()
        self.api.setAccountId(appKey=settings.WXPAY_APPID)

    def push(self, customer, template_id, template_data, to_url):
        openid = get_openid_by_unionid(customer.unionid, settings.WXPAY_APPID)
        if not openid:
            return None
        logger.info({
            'action': 'push.weixinpush',
            'customer': customer.id,
            'openid': openid,
            'template_id': template_id,
            'to_url': to_url,
        })
        return self.api.sendTemplate(openid, template_id, to_url, template_data)

    def push_trade_pay_notify(self, saletrade):
        """
        {{first.DATA}}

        支付金额：{{orderMoneySum.DATA}}
        商品信息：{{orderProductName.DATA}}
        {{Remark.DATA}}
        """
        customer = saletrade.order_buyer
        template_id = 'K3R9wpw_yC2aXEW1PP6586l9UhMjXMwn_-Is4xcgjuA'
        template_data = {
            'first': {
                'value': u'亲爱的用户%s，您的订单已支付成功' % customer.nick,
                'color': '#000000',
            },
            'orderMoneySum': {
                'value': u'%s元' % saletrade.total_fee,
                'color': '#c0392b',
            },
            'orderProductName': {
                'value': saletrade.order_title,
                'color': '#c0392b',
            },
            'Remark': {
                'value': u'\n来自小鹿美美',
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % saletrade.id
        return self.push(customer, template_id, template_data, to_url)

    def push_deliver_notify(self, saletrade):
        """
        {{first.DATA}}

        订单金额：{{orderProductPrice.DATA}}
        商品详情：{{orderProductName.DATA}}
        收货信息：{{orderAddress.DATA}}
        订单编号：{{orderName.DATA}}
        {{remark.DATA}}
        """
        customer = saletrade.order_buyer
        order_address = '%s %s%s%s%s %s' % (
            saletrade.receiver_name,
            saletrade.receiver_state,
            saletrade.receiver_city,
            saletrade.receiver_district,
            saletrade.receiver_address,
            saletrade.receiver_mobile,
        )
        template_id = 'ioBWcEsY40yg3NAQPnzE4LxfuHFFS20JnnAlVr96LXs'
        template_data = {
            'first': {
                'value': u'亲爱的用户%s，您的商品已发货' % customer.nick,
                'color': '#000000',
            },
            'orderProductPrice': {
                'value': u'%s元' % saletrade.total_fee,
                'color': '#c0392b',
            },
            'orderProductName': {
                'value': saletrade.order_title,
                'color': '#c0392b',
            },
            'orderAddress': {
                'value': order_address,
                'color': '#c0392b',
            },
            'orderName': {
                'value': saletrade.tid,
                'color': '#c0392b',
            },
            'remark': {
                'value': u'\n来自小鹿美美',
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % saletrade.id
        return self.push(customer, template_id, template_data, to_url)

    def push_refund_notify(self, salerefund):
        """
        {{first.DATA}}

        退款原因：{{reason.DATA}}
        退款金额：{{refund.DATA}}
        {{remark.DATA}}
        """
        customer = salerefund.get_refund_customer()
        template_id = 'S9cIRfdDTM9yKeMTOj-HH5FPw79OofsfK6G4VRbKYQQ'
        template_data = {
            'first': {
                'value': u'亲爱的用户%s，您购买的商品「%s」已经退款' % (customer.nick, salerefund.title),
                'color': '#000000',
            },
            'reason': {
                'value': u'%s' % salerefund.desc,
                'color': '#c0392b',
            },
            'refund': {
                'value': salerefund.refund_fee,
                'color': '#c0392b',
            },
            'remark': {
                'value': u'\n来自小鹿美美',
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % salerefund.sale_trade.id
        return self.push(customer, template_id, template_data, to_url)

    def push_mama_award(self, awardcarry, courage_remarks, to_url):
        """
        {{first.DATA}}
        任务名称：{{reason.DATA}}
        奖励金额：{{award.DATA}}
        时间：{{commit_time.DATA}}
        {{remark.DATA}}
        """

        customer = awardcarry.get_mama_customer()
        template_id = 'j4YQuNIWMP-OZV_O5LIl1O8GBmaMuqMQ8aLV1oDfnUw'
        template_data = {
            'first': {
                'value': u'报！公主殿下, 您的小鹿美美App奖金又来啦！',
                'color': '#F87217',
            },
            'reason': {
                'value': awardcarry.carry_description,
                'color': '#000000',
            },
            'refund': {
                'value': awardcarry.carry_num_display(),
                'color': '#c0392b',
            },
            'commit_time': {
                'value': str(awardcarry.created),
                'color': '#000000',
            },
            'remark': {
                'value': courage_remarks,
                'color': '#F87217',
            },
        }
        
        return self.push(customer, template_id, template_data, to_url)
