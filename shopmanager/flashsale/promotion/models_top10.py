# -*- coding:utf-8 -*-
import json
import datetime
from django.db import models
from core.models import BaseModel, CacheModel

class TOP10ActivePic(CacheModel):
    """ top10推广所有图片 """

    BANNER_PIC_TYPE = 0  # Banner picture
    COUPON_PIC_TYPE = 1
    CATEGORY_PIC_TYPE = 2
    GOODS_PIC_TYPE = 3
    FOOTER_PIC_TYPE = 4

    PIC_TYPE_CHOICES = ((BANNER_PIC_TYPE, u'Banner图片'),
                      (COUPON_PIC_TYPE, u'优惠券图片'),
                      (CATEGORY_PIC_TYPE, u'分类说明图片'),
                      (GOODS_PIC_TYPE, u'商品图片'),
                      (FOOTER_PIC_TYPE, u'底部活动说明图片'),)

    activity_id = models.IntegerField(db_index=True, blank=True, verbose_name=u'活动id')

    pic_type = models.IntegerField(default=BANNER_PIC_TYPE, choices=PIC_TYPE_CHOICES, db_index=True, verbose_name=u'图片类型')
    model_id = models.BigIntegerField(db_index=True, default=0, verbose_name=u'商品款式ID')
    product_name = models.CharField(max_length=64, blank=True, verbose_name=u'商品款式名')
    pic_path = models.CharField(max_length=256, blank=True, verbose_name=u'品牌图片')
    location_id = models.IntegerField(default=0, verbose_name=u'位置')

    class Meta:
        db_table = 'flashsale_promotion_top10'
        app_label = 'promotion'
        verbose_name = u'特卖/TOP10推广图片'
        verbose_name_plural = u'特卖/TOP10推广图片'

    def __unicode__(self):
        return u'<%s,%s,%s>' % (self.id, self.activity_id, self.pic_type)

    @classmethod
    def get_top10pic(cls, act_id):
        acts = cls.objects.filter(activity_id=act_id)
        if acts.exists():
            return acts
        return []