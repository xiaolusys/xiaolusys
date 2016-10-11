# encoding=utf8
import json
import random
import logging
import datetime
from django.conf import settings
from flashsale.xiaolumm.models import XiaoluMama, WeixinPushEvent
from shopapp.weixin.weixin_apis import WeiXinAPI
from shopapp.weixin.models_base import (
    WeixinFans,
    WeixinTplMsg,
)
from shopapp.weixin import utils
from shopapp.smsmgr.sms_push import SMSPush


logger = logging.getLogger(__name__)


class WeixinPush(object):

    def __init__(self):
        self.mm_api = WeiXinAPI()
        if settings.WEIXIN_PUSH_SWITCH:
            self.mm_api.setAccountId(appKey=settings.WXPAY_APPID)
            self.temai_api = WeiXinAPI()
            self.temai_api.setAccountId(appKey=settings.WEIXIN_APPID)

    def need_sms_push(self, customer):
        """
        如果两个公众账号（小鹿美美，小鹿美美特卖）都没关注，需要发短信
        """
        if not (customer and customer.mobile):
            return False

        temai_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WEIXIN_APPID)
        mm_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WXPAY_APPID)

        if not temai_openid and not mm_openid:
            return True
        else:
            return False

    def push(self, customer, template_ids, template_data, to_url):

        if not settings.WEIXIN_PUSH_SWITCH:
            return

        temai_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WEIXIN_APPID)
        mm_openid = WeixinFans.get_openid_by_unionid(customer.unionid, settings.WXPAY_APPID)

        resp = None
        if mm_openid:
            template_id = template_ids.get('meimei')
            if template_id:
                resp = self.mm_api.sendTemplate(mm_openid, template_id, to_url, template_data)

        if temai_openid and not resp:
            template_id = template_ids.get('temai')
            if template_id:
                resp = self.temai_api.sendTemplate(temai_openid, template_id, to_url, template_data)

        if resp:
            logger.info({
                'action': 'push.weixinpush',
                'customer': customer.id,
                'openid': mm_openid or temai_openid,
                'template_id': json.dumps(template_ids),
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

        template_ids = {
            'meimei': 'K3R9wpw_yC2aXEW1PP6586l9UhMjXMwn_-Is4xcgjuA',
            'temai': 'zFO-Dw936B9TwsJM4BD2Ih3zu3ygtQ_D_QXuNja6J6w'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.format(customer.nick).decode('string_escape'),
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
                'value': template.footer.decode('string_escape'),
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % saletrade.id
        return self.push(customer, template_ids, template_data, to_url)

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
        template_ids = {
            'meimei': 'ioBWcEsY40yg3NAQPnzE4LxfuHFFS20JnnAlVr96LXs',
            'temai': 'vVEY-AOiyiTEVF5AzUupI-H9WeG0tXA3YMYTn8l35VI'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.format(customer.nick).decode('string_escape'),
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
                'value': template.footer.decode('string_escape'),
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % saletrade.id
        return self.push(customer, template_ids, template_data, to_url)

    def push_refund_notify(self, salerefund):
        """
        {{first.DATA}}

        退款原因：{{reason.DATA}}
        退款金额：{{refund.DATA}}
        {{remark.DATA}}
        """
        customer = salerefund.get_refund_customer()
        template_ids = {
            'meimei': 'S9cIRfdDTM9yKeMTOj-HH5FPw79OofsfK6G4VRbKYQQ',
            'temai': '4TlQaNHO8MtVef33iCcPvxhRYS8Q1Nr3j_A9S-BtbLo'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.format(customer.nick, salerefund.title).decode('string_escape'),
                'color': '#000000',
            },
            'reason': {
                'value': u'%s' % salerefund.desc,
                'color': '#c0392b',
            },
            'refund': {
                'value': u'¥%.2f' % salerefund.refund_fee,
                'color': '#c0392b',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#000000',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/mall/od.html?id=%s' % salerefund.sale_trade.id
        return self.push(customer, template_ids, template_data, to_url)

    def push_mama_award(self, awardcarry, courage_remarks, to_url):
        """
        {{first.DATA}}
        任务名称：{{keyword1.DATA}}
        奖励金额：{{keyword2.DATA}}
        时间：{{keyword3.DATA}}
        {{remark.DATA}}
        """

        customer = utils.get_mama_customer(awardcarry.mama_id)

        if self.need_sms_push(customer):
            sms = SMSPush()
            money = u'¥%.2f' % awardcarry.carry_num_display()
            sms.push_mama_ordercarry(customer, money=money)
            return

        template_ids = {
            'meimei': 'K2RVQnhIh6psYkGrkjLclLWmNXQ-hqoc-yumdsLuqC4',
            'temai': 'ATPs2YP1ynKfgtXRl1fhhZ2Kne3AmDmU8Rghax31edg'
        }
        template_data = {
            'first': {
                'value': u'报！公主殿下, 您的小鹿美美App奖金又来啦！',
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'%s' % awardcarry.carry_type_name(),
                'color': '#000000',
            },
            'keyword2': {
                'value': u'¥%.2f' % awardcarry.carry_num_display(),
                'color': '#ff0000',
            },
            'keyword3': {
                'value': u'%s' % awardcarry.created.strftime('%Y-%m-%d %H:%M:%S'),
                'color': '#000000',
            },
            'remark': {
                'value': courage_remarks,
                'color': '#F87217',
            },
        }

        return self.push(customer, template_ids, template_data, to_url)

    def push_mama_ordercarry(self, ordercarry, to_url):
        """
        {{first.DATA}}

        提交时间：{{tradeDateTime.DATA}}
        订单类型：{{orderType.DATA}}
        客户信息：{{customerInfo.DATA}}
        {{orderItemName.DATA}}：{{orderItemData.DATA}}
        {{remark.DATA}}
        """
        # CARRY_TYPES = ((1, u'微商城订单'), (2, u'App订单额外+10%'), (3, u'下属订单+20%'),)
        order_type = ""
        if ordercarry.carry_type == 1:
            order_type = u'微商城订单'
        if ordercarry.carry_type == 2:
            order_type = u'App订单（佣金更高哦！）'
        if ordercarry.carry_type == 3:
            order_type = u'下属订单'

        customer = utils.get_mama_customer(ordercarry.mama_id)

        if self.need_sms_push(customer):
            sms = SMSPush()
            money = u'¥%.2f' % ordercarry.carry_num_display()
            sms.push_mama_ordercarry(customer, money=money)
            return

        template_ids = {
            'meimei': 'eBAuTQQxeGw9NFmheYd8Fc5X7CQbMKpfUSmqxnJOyEc',
            'temai': 'IDXvfqC9j_Y1NhVmtRdBcc6W7MNTNCiLdGTrikgdHoJ3E'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.decode('string_escape'),
                'color': '#F87217',
            },
            'tradeDateTime': {
                'value': ordercarry.created.strftime('%Y-%m-%d %H:%M:%S'),
                'color': '#000000',
            },
            'orderType': {
                'value': order_type,
                'color': '#000000',
            },
            'customerInfo': {
                'value': ordercarry.contributor_nick,
                'color': '#000000',
            },
            'orderItemName':{
                'value': u'订单佣金',
                'color': '#ff0000',
            },
            'orderItemData':{
                'value': '¥%.2f' % ordercarry.carry_num_display(),
                'color': '#ff0000',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#F87217',
            },
        }

        return self.push(customer, template_ids, template_data, to_url)

    def push_mama_clickcarry(self, clickcarry):
        """
        推送点击收益

        ---
        收益通知

        {{first.DATA}}
        收益类型：{{keyword1.DATA}}
        收益金额：{{keyword2.DATA}}
        收益时间：{{keyword3.DATA}}
        剩余金额：{{keyword4.DATA}}
        {{remark.DATA}}


        """
        mama_id = clickcarry.mama_id
        customer = utils.get_mama_customer(mama_id)
        mama = XiaoluMama.objects.get(id=mama_id)
        event_type = WeixinPushEvent.CLICK_CARRY

        template_id = 'n9kUgavs_10Dz8RbIgY2F9r6rNdlNw3I6D1KLft0_2I'
        template = WeixinTplMsg.objects.filter(wx_template_id=template_id, status=True).first()

        if not template:
            return

        today = datetime.datetime.now().date().strftime('%Y%m%d')
        q_str = '{mama_id}-{date}-clickcarry'.format(**{'mama_id': mama_id, 'date': today})
        last_event = WeixinPushEvent.objects.filter(uni_key__contains=q_str).order_by('-created').first()

        if last_event:
            _, _, _, last_click_num, last_total_value = last_event.uni_key.split('-')
            carry_count = clickcarry.click_num - int(last_click_num)
            carry_money = clickcarry.total_value - int(last_total_value)

            # 60秒内不许重复推送
            delta = datetime.datetime.now() - last_event.created
            if delta.seconds < 60 and clickcarry.click_num < clickcarry.init_click_limit:
                return
        else:
            carry_count = clickcarry.click_num
            carry_money = clickcarry.total_value

        uni_key = '{mama_id}-{date}-clickcarry-{click_num}-{total_value}'.format(**{
            'mama_id': mama_id,
            'date': today,
            'click_num': clickcarry.click_num,
            'total_value': clickcarry.total_value
        })

        template_data = {
            'first': {
                'value': template.header.format(carry_count).decode('string_escape'),
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'点击收益',
                'color': '#000000',
            },
            'keyword2': {
                'value': u'%.2f元' % (carry_money * 0.01),
                'color': '#ff0000',
            },
            'keyword3': {
                'value': u'%s' % clickcarry.modified.strftime('%Y-%m-%d %H:%M:%S'),
                'color': '#000000',
            },
            'keyword4': {
                'value': u'%.2f元（可提现）' % (mama.get_carry()[0] * 0.01),
                'color': '#000000',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#F87217',
            },
        }
        to_url = 'http://m.xiaolumeimei.com/rest/v2/mama/redirect_stats_link?link_id=4'

        event = WeixinPushEvent(customer_id=customer.id, mama_id=mama_id, uni_key=uni_key, tid=template.id,
                                event_type=event_type, params=template_data, to_url=to_url)
        event.save()

    def push_mama_update_app(self, mama_id, user_version, latest_version, to_url, device=''):
        """
        {{first.DATA}}
        系统名称：{{keyword1.DATA}}
        运维状态：{{keyword2.DATA}}
        {{remark.DATA}}
        """

        customer = utils.get_mama_customer(mama_id)

        if self.need_sms_push(customer):
            sms = SMSPush()
            sms.push_mama_update_app(customer)
            return

        template_ids = {
            'meimei': 'l9QBpAojbpQmFIRmhSN4M-eQDzkw76yBpfrYcBoakK0',
            'temai': 'x_nPMjWKodG0V4w334I_u5LAFpoTH1fSqjAv5jPmA7Y'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.decode('string_escape'),
                'color': '#4CC417',
            },
            'keyword1': {
                'value': u'您的当前%s版本：%s' % (device, user_version),
                'color': '#4CC417',
            },
            'keyword2': {
                'value': u'最新发布%s版本：%s' % (device, latest_version),
                'color': '#ff0000',
            },
            'remark': {
                'value': template.footer.decode('string_escape'),
                'color': '#4CC417',
            },
        }

        return self.push(customer, template_ids, template_data, to_url)

    def push_mama_invite_trial(self, referal_mama_id, potential_mama_id, diff_num, award_num,
                               invite_num, award_sum, trial_num, carry_num):
        """
        {{first.DATA}}
        姓名：{{keyword1.DATA}}
        手机：{{keyword2.DATA}}
        会员等级：{{keyword3.DATA}}
        {{remark.DATA}}
        """

        referal_customer = utils.get_mama_customer(referal_mama_id)

        if not referal_customer:
            return

        potential_customer = utils.get_mama_customer(potential_mama_id)
        mobile_string = ''
        if potential_customer.mobile:
            mobile = potential_customer.mobile
            mobile_string = '%s****%s' % (mobile[0:3], mobile[7:])

        template_ids = {
            'meimei': 'tvns3YwYkRkkd2mycvxKsbRtuQl1spBHxtm9PLFIlFI',
            'temai': 'O6SYsBHUpYpk9UTUzmUrhybU7arHuFsz2shox0JOg1s'
        }
        template = WeixinTplMsg.objects.filter(wx_template_id__in=template_ids.values(), status=True).first()

        if not template:
            return

        template_data = {
            'first': {
                'value': template.header.format(diff_num=diff_num, award_num=award_num).decode('string_escape'),
                'color': '#F87217',
            },
            'keyword1': {
                'value': u'%s (ID:%s)' % (potential_customer.nick, potential_mama_id),
                'color': '#4CC417',
            },
            'keyword2': {
                'value': mobile_string,
                'color': '#4CC417',
            },
            'keyword3': {
                'value': u'15天体验试用',
                'color': '#4CC417',
            },
            'remark': {
                'value': template.footer.format(
                    invite_num=invite_num, award_sum=award_sum,
                    trial_num=trial_num, award_total=trial_num*carry_num).decode('string_escape'),
                'color': '#F87217',
            },
        }
        to_url = 'http://m.xiaolumeimei.com'
        return self.push(referal_customer, template_ids, template_data, to_url)

    def push_new_mama_task(self, mama_id, header='', footer='', to_url='', params=None):
        """
        任务完成通知

        {{first.DATA}}
        任务名称：{{keyword1.DATA}}
        任务类型：{{keyword2.DATA}}
        完成时间：{{keyword3.DATA}}
        {{remark.DATA}}
        """
        customer = utils.get_mama_customer(mama_id)
        if not params:
            params = {}

        template_ids = {
            'meimei': 'Lvw0t5ttadeEzRV2tczPclzpPnLXGEQZZJVdWxHyS4g',
            'temai': 'frGeesnAWDCmn5CinuzVGb1VbS5610J8xjM-tgPV7XQ'
        }
        template_data = {
            'first': {
                'value': header,
                'color': '#4CC417',
            },
            'keyword1': {
                'value': params.get('task_name', ''),
                'color': '#4CC417',
            },
            'keyword2': {
                'value': params.get('task_type', u'新手任务'),
                'color': '#4CC417',
            },
            'keyword3': {
                'value': (params.get('finish_time') or datetime.datetime.now()).strftime('%Y-%m-%d'),
                'color': '#4CC417',
            },
            'remark': {
                'value': footer,
                'color': '#4CC417',
            },
        }
        return self.push(customer, template_ids, template_data, to_url)

    push_mission_finish_task = push_new_mama_task

    def push_mission_state_task(self, mama_id, header='', footer='', to_url='', params=None):
        """
        新任务提醒

        {{first.DATA}}
        任务名称：{{keyword1.DATA}}
        奖励金额：{{keyword2.DATA}}
        截止时间：{{keyword3.DATA}}
        需求数量：{{keyword4.DATA}}
        任务简介：{{keyword5.DATA}}
        {{remark.DATA}}
        """
        customer = utils.get_mama_customer(mama_id)
        if not params:
            params = {}

        template_ids = {
            'meimei': '5dmrReey6YXG-eRuNWsfpK0xFL35xzk0UoJ43DJHwJ4',
            'temai': '98pFo0KBn5WFLecvFnC2Ve_atd9wNYXdBc5zO4jJO9g'
        }
        template_data = {
            'first': {
                'value': header,
                'color': '#4CC417',
            },
            'keyword1': {
                'value': params.get('task_name', ''),
                'color': '#4CC417',
            },
            'keyword2': {
                'value': params.get('award_amount', u'不限额'),
                'color': '#4CC417',
            },
            'keyword3': {
                'value': params.get('deadline', ''),
                'color': '#4CC417',
            },
            'keyword4': {
                'value': params.get('target_state', ''),
                'color': '#4CC417',
            },
            'keyword5': {
                'value': params.get('description', ''),
                'color': '#4CC417',
            },
            'remark': {
                'value': footer,
                'color': '#4CC417',
            },
        }
        return self.push(customer, template_ids, template_data, to_url)

    def push_event(self, event_instance):
        customer = event_instance.get_effect_customer()
        if not customer:
            return

        tid = event_instance.tid
        template = WeixinTplMsg.objects.filter(id=tid, status=True).first()
        if not template:
            return

        template_ids = template.template_ids
        template_data = event_instance.params

        header = template_data.get('first')
        if not header:
            template_data.update({'first': {'value': template.header.decode('string_escape'), 'color':'#F87217'}})
        footer = template_data.get('remark')
        if not footer:
            template_data.update({'remark': {'value': template.footer.decode('string_escape'), 'color':'#F87217'}})
        to_url = event_instance.to_url
        if not to_url:
            from flashsale.promotion.models import ActivityEntry
            active_time = datetime.datetime.now() - datetime.timedelta(hours=6)
            activity_entries = ActivityEntry.get_effect_activitys(active_time)
            entry = random.choice(activity_entries)
            login_url = 'http://m.xiaolumeimei.com/rest/v1/users/weixin_login/?next='
            redirect_url = '/rest/v2/mama/redirect_activity_entry?activity_id=%s' % entry.id
            to_url = login_url + redirect_url
            remark = template_data.get('remark')
            desc = ''
            if remark:
                desc = remark.get('value')

            desc += u'\n\n今日热门:\n［%s］%s' % (entry.title, entry.act_desc)
            template_data.update({'remark': {'value': desc, 'color':'#ff6633'}})

        return self.push(customer, template_ids, template_data, to_url)
