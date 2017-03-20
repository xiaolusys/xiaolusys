# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models

# from django.db import models
from core.models import BaseModel
from core.fields import JSONCharMyField

from global_setup import is_undeploy_enviroment

import logging
logger = logging.getLogger(__name__)

FENGCHAO_SLYC_VENDOR_CODE  = 'slyc'
FENGCHAO_SLYC_CHANNEL_CODE = 'shiliyangchang' # 十里洋场的订单channel

if is_undeploy_enviroment():
    FENGCHAO_DEFAULT_CHANNEL_CODE = '1' # 小鹿特卖的订单channel
else:
    FENGCHAO_DEFAULT_CHANNEL_CODE = 'xiaolumeimei'

def get_channelid_by_vendor_codes(vendor_codes):
    # vendor_codes: 根据vendor_code　返回对应的channel字典
    channel_maps = {}
    for vendor_code in vendor_codes:
        if vendor_code.lower() == FENGCHAO_SLYC_VENDOR_CODE:
            channel_maps[vendor_code] = FENGCHAO_SLYC_CHANNEL_CODE
        else:
            channel_maps[vendor_code] = FENGCHAO_DEFAULT_CHANNEL_CODE
    return channel_maps

class FengchaoOrderChannel(BaseModel):

    CHANNEL_TYPE_CHOICES = (
        ('1', '淘宝'),
        ('2', '天猫'),
        ('7', '京东商城'),
        ('11', '亚马逊'),
        ('12', '一号店'),
        ('13', '国美商城'),
        ('14', '苏宁'),
        ('15', '阿里巴巴'),
        ('16', '当当网'),
        ('17', 'eBay'),
        ('18', '唯品会'),
        ('19', '聚美优品'),
        ('20', '自有商城'),
        ('32', '蜜芽'),
        ('33', 'JD全球售'),
    )

    channel_id   = models.CharField(max_length=16, unique=True, verbose_name=u'销售渠道 ID')
    channel_name = models.CharField(max_length=16, db_index=True, verbose_name=u'销售渠道名字')
    channel_type = models.CharField(max_length=16, db_index=True, choices=CHANNEL_TYPE_CHOICES, verbose_name=u'渠道类型')
    channel_client_id = models.CharField(max_length=16, db_index=True, verbose_name=u'销售渠道商家代码')

    status = models.BooleanField(default=False, verbose_name='更新状态')
    extras = JSONCharMyField(max_length=512, default={}, verbose_name=u'附加信息')

    class Meta:
        db_table = 'fengchao_orderchannnel'
        app_label = 'fengchao'
        verbose_name = u'外仓/蜂巢订单来源渠道'
        verbose_name_plural = u'外仓/蜂巢订单来源渠道'

    @classmethod
    def get_default_channel(cls):
        return cls.objects.first()