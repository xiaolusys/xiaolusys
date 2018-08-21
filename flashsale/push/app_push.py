# encoding=utf8
"""
APP　推送
"""
import json
from django.conf import settings

from flashsale.push.mipush import mipush_of_ios, mipush_of_android
from flashsale.protocol import get_target_url
from flashsale.push.models_message import PushMsgTpl
from flashsale.protocol import constants as protocal_constants
from flashsale.protocol.models import APPFullPushMessge
from shopapp.weixin.utils import get_mama_customer

import logging
logger = logging.getLogger('service')


class AppPush(object):

    def __init__(self):
        pass

    @classmethod
    def push(cls, customer_id, target_url, msg, pass_through=0):
        if not settings.APP_PUSH_SWITCH:
            return
        android_res = mipush_of_android.push_to_account(
            customer_id, {'target_url': target_url}, description=msg, pass_through=pass_through)
        ios_res = mipush_of_ios.push_to_account(
            customer_id, {'target_url': target_url}, description=msg, pass_through=pass_through)

        logger.info({
            'action': 'push.apppush',
            'customer': customer_id,
            'msg': msg,
            'target_url': target_url,
            'android_res': json.dumps(android_res),
            'ios_res': json.dumps(ios_res)
        })
        return {'android': android_res, 'ios': ios_res}

    @classmethod
    def push_to_all(cls, target_url, msg, pass_through=0):
        android_res = mipush_of_android.push_to_all(
            {'target_url': target_url}, description=msg, pass_through=pass_through)
        ios_res = mipush_of_ios.push_to_all(
            {'target_url': target_url}, description=msg, pass_through=pass_through)

        logger.info({
            'action': 'push.apppush.all',
            'msg': msg,
            'target_url': target_url,
            'android_res': json.dumps(android_res),
            'ios_res': json.dumps(ios_res)
        })
        return {'android': android_res, 'ios': ios_res}

    @classmethod
    def push_to_platform(cls, platform, target_url, msg, pass_through=0):
        android_res = {}
        ios_res = {}
        if platform == 'ios':
            android_res = mipush_of_ios.push_to_all(
                {'target_url': target_url}, description=msg, pass_through=pass_through)
        if platform == 'android':
            ios_res = mipush_of_android.push_to_all(
                {'target_url': target_url}, description=msg, pass_through=pass_through)

        logger.info({
            'action': 'push.apppush.platform',
            'platform': platform,
            'msg': msg,
            'target_url': target_url,
            'android_res': json.dumps(android_res),
            'ios_res': json.dumps(ios_res)
        })
        return {'android': android_res, 'ios': ios_res}

    @classmethod
    def push_to_topic(cls, topic, target_url, msg, pass_through=0):
        android_res = mipush_of_android.push_to_topic(
            topic, {'target_url': target_url}, description=msg, pass_through=pass_through)
        ios_res = mipush_of_ios.push_to_topic(
            topic, {'target_url': target_url}, description=msg, pass_through=pass_through)

        logger.info({
            'action': 'push.apppush.topic',
            'topic': topic,
            'msg': msg,
            'target_url': target_url,
            'android_res': json.dumps(android_res),
            'ios_res': json.dumps(ios_res)
        })
        return {'android': android_res, 'ios': ios_res}

    @classmethod
    def push_mama_ordercarry(cls, ordercarry):
        """
        有新的订单收益推送给小鹿妈妈
        """
        customer = get_mama_customer(ordercarry.mama_id)
        target_url = get_target_url(protocal_constants.TARGET_TYPE_VIP_HOME)
        msgtpl = PushMsgTpl.objects.filter(id=5, is_valid=True).first()
        msg    = ''
        if msgtpl:
            money = '%.2f' % ordercarry.carry_num_display()
            nick = ordercarry.contributor_nick
            msg = msgtpl.get_emoji_content().format(money, nick)

        if msg:
            cls.push(customer.id, target_url, msg)

    @classmethod
    def push_mama_ordercarry_to_all(cls, ordercarry):
        """
        有新的订单收益推送给所有小鹿妈妈,使用透传消息
        """
        topic = APPFullPushMessge.TOPIC_XLMM
        msgtpl = PushMsgTpl.objects.filter(id=12, is_valid=True).first()
        customer = get_mama_customer(ordercarry.mama_id)

        if not msgtpl:
            return

        money = '%.2f' % ordercarry.carry_num_display()
        nick = customer.nick
        content = msgtpl.get_emoji_content().format(nick=nick[:10], money=money)

        msg = {
            'content': content,
            'avatar': customer.thumbnail,
            'type': 'mama_ordercarry_broadcast'
        }
        msg = json.dumps(msg)
        target_url = ''
        cls.push_to_topic(topic, target_url, msg, pass_through=1)

    @classmethod
    def push_product_to_customer(cls, customer_id, modelproduct):
        """
        给用户推送商品
        """
        product_url = modelproduct.item_product.get_weburl()
        params = {'product_id': product_url}
        target_url = get_target_url(protocal_constants.TARGET_TYPE_PRODUCT, params=params)
        msg = None

        mstpl = PushMsgTpl.objects.filter(id=11, is_valid=True).first()
        if mstpl:
            msg = mstpl.get_emoji_content().format(modelproduct.name)

        if msg:
            cls.push(customer_id, target_url, msg)

    @classmethod
    def push_pass_through(cls, topic):
        """
        测试用
        """
        import random
        msg = {
            'content': u'有新订单了%s' % str(random.randrange(100)),
            'avatar': 'http://wx.qlogo.cn/mmopen/n24ek7Oc1iaXyxqzHobN7BicG5W1ljszSRWSdzaFeRkGGVwqjmQKTmicTylm8IkclpgDiaamWqZtiaTlcvLJ5z6x35wCKMWVbcYPU/0',
            'type': 'mama_ordercarry_broadcast'
        }
        msg = json.dumps(msg)
        target_url = ''
        cls.push_to_topic(topic, target_url, msg, pass_through=1)
