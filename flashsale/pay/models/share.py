# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import datetime, urllib
from django.db import models

from common.utils import url_utf8_quote
from .base import PayBaseModel

class CustomShare(PayBaseModel):
    SHOP_SHARE = 'shop'
    MODEL_SHARE = 'model'
    PRODUCT_SHARE = 'product'

    SHARE_TYPE = ((SHOP_SHARE, u'店铺分享'),
                  (MODEL_SHARE, u'款式分享'),
                  (PRODUCT_SHARE, u'商品分享'),)

    title = models.CharField(max_length=64, blank=True, verbose_name=u'分享标题')
    desc = models.CharField(max_length=1024, blank=True, verbose_name=u'分享描述')
    share_url = models.CharField(max_length=256, blank=True, verbose_name=u'分享链接')
    share_img = models.CharField(max_length=256, blank=True, verbose_name=u'分享图片(小于32K)')

    share_type = models.CharField(max_length=8, default=SHOP_SHARE,
                                  choices=SHARE_TYPE, verbose_name=u'分享类型')

    active_at = models.DateField(default=datetime.date.today, verbose_name=u'生效时间')
    status = models.BooleanField(default=False, verbose_name=u'使用')

    class Meta:
        db_table = 'flashsale_customshare'
        app_label = 'pay'
        verbose_name = u'特卖/用户分享设置'
        verbose_name_plural = u'特卖/用户分享设置'

    def __unicode__(self):
        return '<%s,%s>' % (self.id, self.title)

    @classmethod
    def get_instance_by_type(cls, share_type):
        today = datetime.date.today()
        shares = cls.objects.filter(status=True, share_type=share_type,
                                    active_at__lte=today).order_by('-active_at')
        if shares.exists():
            return shares[0]
        return None

    def share_link(self, **params):
        share_link = self.share_url.format(**params)
        if not 'next=' in share_link:
            return share_link

        tokens = share_link.split('next=')
        base_url = tokens[0]
        next_url = urllib.quote(tokens[1])
        return ''.join([base_url, 'next=', next_url])

    def share_title(self, **params):
        if not params:
            return self.title
        return self.title.format(**params)

    def share_desc(self, **params):
        if not params:
            return self.desc
        return self.desc.format(**params)

    def share_image(self, **params):
        share_img = self.share_img.format(**params)
        return url_utf8_quote(share_img.encode('utf-8'))
