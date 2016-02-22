# -*- coding:utf8 -*-
import string, random
from random import choice
from django.db import models

from flashsale.protocol import get_target_url
from flashsale.protocol.constants import TARGET_TYPE_WEBVIEW
from flashsale.push.mipush import mipush_of_ios, mipush_of_android

CHARANGE_STR = string.ascii_lowercase
NUMBER_STR = '0123456789'


class VipCodeManager(models.Manager):
    def get_queryset(self):
        super_tm = super(VipCodeManager, self)
        if hasattr(super_tm, 'get_query_set'):
            return super_tm.get_query_set()
        return super_tm.get_queryset()

    def genCode(self):
        """ 生成邀请码 """
        xx = random.randint(1000000, 9999999)
        return str(xx)

    def genVIpCode(self, mobile, expiried):
        new_code = self.genCode()
        cnt = 0
        while True:
            cnt += 1
            try:
                xl_invite_code = self.get(vipcode=new_code)
            except self.model.DoesNotExist:
                try:
                    self.create(vipcode=new_code, mobile=mobile, expiried=expiried)
                except:
                    new_code = self.genCode()
                else:
                    return new_code
            else:
                return xl_invite_code.vipcode
            if cnt > 20:
                raise Exception(u'邀请码生成异常')


class ReadPacketManager(models.Manager):
    content = ['美女，您就是真命的白富美，现金红包拿去{0}元。', '亲亲，您魅力引来三位好友，奖励现金红包{0}元。',
               '大王，您又吸引了三位好友，获得现金红包{0}元。']
    descs = ['美女，您就是真命的白富美，现金红包拿去。', '亲亲，您魅力引来三位好友，奖励现金红包。',
             '大王，您又吸引了三位好友，获得现金红包。']
    values = [1.18, 1.28, 1.38, 1.58, 1.68, 1.78, 1.88]

    def get_queryset(self):
        super_pac = super(ReadPacketManager, self)
        if hasattr(super_pac, 'get_query_set'):
            return super_pac.get_query_set()
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
        # else:
        #     packet_count = (downcount - 1) / 3 + 1  # 计算应该要发送红包的数量
        #     li = range(packet_count - r_packerscount)
        #     for i in li:
        #         content = choice(self.content)
        #         self.releasepacket(customer, content)
        #     return
        #
        else:
            if (downcount - 1) % 3 == 0:
                content = choice(self.content)
                self.releasepacket(customer, content)