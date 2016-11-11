# -*- coding:utf8 -*-
import string
from random import choice
from core.ormcache.managers import CacheManager

from flashsale.protocol import get_target_url
from flashsale.protocol.constants import TARGET_TYPE_WEBVIEW
from flashsale.push.mipush import mipush_of_ios, mipush_of_android

CHARANGE_STR = string.ascii_lowercase
NUMBER_STR = '0123456789'


class ReadPacketManager(CacheManager):
    content = ['美女，您就是真命的白富美，现金红包拿去{0}元。',
               '亲亲，您魅力引来三位好友，奖励现金红包{0}元。',
               '大王，您又吸引了三位好友，获得现金红包{0}元。',
               '女王大人，您又吸引了三位好友，收获现金{0}元。',
               '亲亲，您魅力引来三位好友，奖励现金红包{0}元。',
               '白富美小姐，您好友真给力，送您现金红包{0}元。',
               '陛下，有三位好友前来追随，带来现金红包{0}元。',
               '明星小姐，您多了三位好友捧场，收获红包{0}元。',
               '公主大人，您又有三位好友相助，奖励红包{0}元。',
               '您的引力波击中三位好友前来，奖励现金{0}元。',
               '又有三位好友被您的光彩魅力折服，奖励{0}元。',
               '三位英明俊俏的好友响应了您的号召，奖励{0}元。',
               '您的三位美女火枪手好友已到活动报道，奖励{0}元。',
               '你又增加三位名模好友到活动助阵，奖励现金{0}元。']

    descs = ['美女，您就是真命的白富美，现金红包拿去。',
             '亲亲，您魅力引来三位好友，奖励现金红包。',
             '大王，您又吸引了三位好友，获得现金红包。',
             '女王大人，您又吸引了三位好友，收获现金?元。',
             '亲亲，您魅力引来三位好友，奖励现金红包?元。',
             '白富美小姐，您好友真给力，送您现金红包?元。',
             '陛下，有三位好友前来追随，带来现金红包?元。',
             '明星小姐，您多了三位好友捧场，收获红包?元。',
             '公主大人，您又有三位好友相助，奖励红包?元。',
             '您的引力波击中三位好友前来，奖励现金?元。',
             '又有三位好友被您的光彩魅力折服，奖励?元。',
             '三位英明俊俏的好友响应了您的号召，奖励?元。',
             '您的三位美女火枪手好友已到活动报道，奖励?元。',
             '你又增加三位名模好友到活动助阵，奖励现金?元。']
    values = [1.18, 1.28, 1.38, 1.58, 1.68, 1.78, 1.88]

    def get_queryset(self):
        super_pac = super(ReadPacketManager, self)
        return super_pac.get_queryset()

    def push_message_to_app(self, customer_id):
        """
        给用户客户端推送消息
        """
        site_url = 'http://m.xiaolumeimei.com/sale/promotion/xlsampleorder/'
        desc = choice(self.descs)
        target_url = get_target_url(TARGET_TYPE_WEBVIEW, {'is_native': 1, 'url': site_url})
        mipush_of_android.push_to_account(customer_id,
                                          {'target_url': target_url},
                                          description=desc)
        mipush_of_ios.push_to_account(customer_id,
                                      {'target_url': target_url},
                                      description=desc)

    def releasepacket(self, customer, content):

        value = choice(self.values)
        vcontent = content.format(value)
        self.create(customer=customer, value=value, content=vcontent)
        customer = int(customer)
        self.push_message_to_app(customer)
        return

    def release133_packet(self, customer, downcount):
        """
        激活数量为１的时候发放一个红包，以后每增加３个发放一个红包
        """
        customer = str(customer)
        r_packerscount = self.filter(customer=customer).count()  # 已经发放的红包数量

        if downcount in (1, 2, 3) and r_packerscount == 0:
            content = self.content[0]
            self.releasepacket(customer, content)
            return
        else:
            if (downcount - 1) % 3 == 0:
                content = choice(self.content)
                self.releasepacket(customer, content)
