# encoding=utf8
import logging
from django.conf import settings
from shopapp.weixin.weixin_apis import WeiXinAPI
from shopapp.weixin.models_base import WeixinFans

from shopapp.weixin.options import get_openid_by_unionid
from shopapp.weixin import utils


logger = logging.getLogger(__name__)


class WeixinPush(object):

    def __init__(self):
        self.mm_api = WeiXinAPI()
        self.mm_api.setAccountId(appKey=settings.WXPAY_APPID)
        self.temai_api = WeiXinAPI()
        self.temai_api.setAccountId(appKey=settings.WEIXIN_APPID)

    def push(self, customer, template_id, template_data, to_url):
        temai_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WEIXIN_APPID)
        mm_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WXPAY_APPID)

        if mm_openid:
            resp = self.mm_api.sendTemplate(mm_openid, template_id, to_url, template_data)
        elif temai_openid:
            resp = self.temai_api.sendTemplate(temai_openid, template_id, to_url, template_data)
        else:
            # TODO:发短信，暂时不处理
            resp = None

        logger.info({
            'action': 'push.weixinpush',
            'customer': customer.id,
            'openid': mm_openid or temai_openid,
            'template_id': template_id,
            'to_url': to_url,
        })
        return resp

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
                'value': u'公主殿下%s，您的订单已支付成功。' % customer.nick,
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
                'value': u'\n打开小鹿美美App，订单详情有现金红包可以领取哦！',
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
                'value': u'公主殿下%s，您的商品已发货！' % customer.nick,
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
                'value': u'\n请到小鹿美美App查看订单物流，还有现金红包可以分享领取哦！',
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
                'value': u'公主殿下%s，您购买的商品「%s」已经退款。' % (customer.nick, salerefund.title),
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
                'value': u'\n小鹿美美App，健康美丽从这里开始！',
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % salerefund.sale_trade.id
        return self.push(customer, template_id, template_data, to_url)

    def push_mama_award(self, awardcarry, courage_remarks, to_url):
        """
        {{first.DATA}}
        任务名称：{{keyword1.DATA}}
        奖励金额：{{keyword2.DATA}}
        时间：{{keyword3.DATA}}
        {{remark.DATA}}
        """

        customer = utils.get_mama_customer(awardcarry.mama_id)
        template_id = 'j4YQuNIWMP-OZV_O5LIl1O8GBmaMuqMQ8aLV1oDfnUw'
        template_data = {
            'first': {
                'value': u'报！公主殿下, 您的小鹿美美App奖金又来啦！',
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'%s' % awardcarry.carry_description,
                'color': '#000000',
            },
            'keyword2': {
                'value': u'¥%.2f' % awardcarry.carry_num_display(),
                'color': '#ff0000',
            },
            'keyword3': {
                'value': u'%s' % awardcarry.created,
                'color': '#000000',
            },
            'remark': {
                'value': courage_remarks,
                'color': '#F87217',
            },
        }

        return self.push(customer, template_id, template_data, to_url)

    def push_mama_ordercarry(self, ordercarry, remarks, to_url):
        """
        {{first.DATA}}
        收益金额：{{keyword1.DATA}}
        收益来源：{{keyword2.DATA}}
        到账时间：{{keyword3.DATA}}
        {{remark.DATA}}
        """

        #CARRY_TYPES = ((1, u'微商城订单'), (2, u'App订单额外+10%'), (3, u'下属订单+20%'),)
        description = ""
        if ordercarry.carry_type == 1:
            description = u'微商城订单'
        if ordercarry.carry_type == 2:
            description = u'App订单（佣金更高哦！）'
        if ordercarry.carry_type == 3:
            description = u'下属订单'
            
        customer = utils.get_mama_customer(ordercarry.mama_id)
        template_id = 'jorNMI-K3ewxBXHTgTKpePCF6yn5O5oLZK6azNNoWK4'
        template_data = {
            'first': {
                'value': u'女王大人, 小鹿美美App报告：您有一笔新订单啦！',
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'¥%.2f' % ordercarry.carry_num_display(),
                'color': '#ff0000',
            },
            'keyword2': {
                'value': description,
                'color': '#000000',
            },
            'keyword3': {
                'value': u'%s (订单时间)' % ordercarry.created,
                'color': '#000000',
            },
            'remark': {
                'value': remarks,
                'color': '#F87217',
            },
        }

        return self.push(customer, template_id, template_data, to_url)

    def push_mama_update_app(self, mama_id, user_version, latest_version, remarks, to_url):
        """
        {{first.DATA}}
        系统名称：{{keyword1.DATA}}
        运维状态：{{keyword2.DATA}}
        {{remark.DATA}}
        """
        
        customer = utils.get_mama_customer(mama_id)
        template_id = 'l9QBpAojbpQmFIRmhSN4M-eQDzkw76yBpfrYcBoakK0'
        template_data = {
            'first': {
                'value': u'小鹿美美App：新版已发布，妈妈们请尽快更新！',
                'color': '#4CC417',
            },
            'keyword1': {
                'value': u'您的当前版本：%s' % user_version,
                'color': '#4CC417',
            },
            'keyword2': {
                'value': u'最新发布版本：%s' % latest_version,
                'color': '#ff0000',
            },
            'remark': {
                'value': remarks,
                'color': '#4CC417',
            },
        }
        
        return self.push(customer, template_id, template_data, to_url)

        
