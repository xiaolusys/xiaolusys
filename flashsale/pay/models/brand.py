# -*- coding:utf-8 -*-
import json
import datetime
from django.db import models

from core.fields import JSONCharMyField
from .base import PayBaseModel, BaseModel

import logging
logger = logging.getLogger(__name__)

class BrandEntry(BaseModel):
    """ 专题活动入口 这个结构不再使用了"""

    PROMOTION_TOP10 = 1
    PROMOTION_TOPIC = 2
    PROMOTION_BRAND = 3

    PROMOTION_CHOICES = (
        (PROMOTION_TOP10, u'Top10'),
        (PROMOTION_TOPIC, u'专题'),
        (PROMOTION_BRAND, u'品牌'),
    )

    id = models.AutoField(primary_key=True)
    brand_name = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'专题名称')

    brand_desc = models.TextField(max_length=512, blank=True, verbose_name=u'专题活动描述')
    brand_pic = models.CharField(max_length=256, blank=True, verbose_name=u'品牌LOGO')
    brand_post = models.CharField(max_length=256, blank=True, verbose_name=u'专题海报')
    brand_applink = models.CharField(max_length=256, blank=True, verbose_name=u'专题APP协议链接')
    mask_link = models.CharField(max_length=256, blank=True, verbose_name=u'专题活动弹窗提示图')
    share_icon = models.CharField(max_length=128, blank=True, verbose_name=u'专题活动分享图片')
    share_link = models.CharField(max_length=256, blank=True, verbose_name=u'专题活动分享链接')
    promotion_type = models.IntegerField(choices=PROMOTION_CHOICES, default=PROMOTION_TOP10,
                                         db_index=True, verbose_name=u'专题活动类型')

    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')

    order_val = models.IntegerField(default=0, verbose_name=u'排序值')
    is_active = models.BooleanField(default=True, verbose_name=u'上线')

    extra_pic = JSONCharMyField(max_length=1024, blank=True, default=[], verbose_name=u'推广展示其它图片')

    class Meta:
        db_table = 'flashsale_brand_entry'
        app_label = 'pay'
        verbose_name = u'特卖/推广专题入口'
        verbose_name_plural = u'特卖/推广专题入口'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.brand_name)

    @classmethod
    def get_brand(cls):
        acts = cls.objects.filter(is_active=True)
        if acts.exists():
            return acts
        return []

    @classmethod
    def get_effect_brands(cls, btime):
        """ 根据时间获取活动列表 """
        brands = cls.objects.filter(is_active=True,
                                    end_time__gte=btime) \
            .order_by('-order_val', '-modified')
        if brands.exists():
            return brands
        return cls.objects.none()


class BrandProduct(BaseModel):
    """ 品牌商品信息 这个结构不再使用了"""

    BANNER_PIC_TYPE = 0  # Banner picture
    COUPON_GETBEFORE_PIC_TYPE = 1
    COUPON_GETAFTER_PIC_TYPE = 2
    TOPIC_PIC_TYPE = 3
    CATEGORY_PIC_TYPE = 4
    GOODS_HORIZEN_PIC_TYPE = 5
    GOODS_VERTICAL_PIC_TYPE = 6
    FOOTER_PIC_TYPE = 7

    PIC_TYPE_CHOICES = ((BANNER_PIC_TYPE, u'Banner图片'),
                        (COUPON_GETBEFORE_PIC_TYPE, u'优惠券领前'),
                        (COUPON_GETAFTER_PIC_TYPE, u'优惠券领后'),
                        (TOPIC_PIC_TYPE, u'主题入口'),
                        (CATEGORY_PIC_TYPE, u'分类说明图片'),
                        (GOODS_HORIZEN_PIC_TYPE, u'商品横放图片'),
                        (GOODS_VERTICAL_PIC_TYPE, u'商品竖放图片'),
                        (FOOTER_PIC_TYPE, u'底部分享图片'),)

    id = models.AutoField(primary_key=True)
    brand = models.ForeignKey(BrandEntry, related_name='brand_products', verbose_name=u'所属专题')
    brand_name = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'专题名称')

    product_id = models.BigIntegerField(db_index=True, default=0, verbose_name=u'商品ID')
    model_id = models.BigIntegerField(db_index=True, default=0, verbose_name=u'商品款式ID')
    product_name = models.CharField(max_length=64, blank=True, verbose_name=u'商品名称')
    product_img = models.CharField(max_length=256, blank=True, verbose_name=u'商品图片')

    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')

    location_id = models.IntegerField(default=0, verbose_name=u'位置')
    pic_type = models.IntegerField(choices=PIC_TYPE_CHOICES, default=GOODS_VERTICAL_PIC_TYPE,
                                   db_index=True, verbose_name=u'图片类型')
    jump_url = models.CharField(max_length=256, blank=True, verbose_name=u'跳转链接')

    class Meta:
        db_table = 'flashsale_brand_product'
        app_label = 'pay'
        verbose_name = u'特卖/专题商品'
        verbose_name_plural = u'特卖/专题商品列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.brand_name)

    def save(self, *args, **kwargs):
        if not self.brand_name:
            self.brand_name = self.brand.brand_name
        # if not self.product_name:
        #     self.product_name = self.prodouct.name
        #     self.product_img = self.prodouct.head_img()
        return super(BrandProduct, self).save(*args, **kwargs)

    # @property
    # def prodouct(self):
    #     if not hasattr(self, '_product_'):
    #         self._product_ = Product.objects.get(id=self.product_id)
    #     return self._product_
    #
    # def product_lowest_price(self):
    #     """ 商品最低价 """
    #     return self.prodouct.product_lowest_price()
    #
    # def product_std_sale_price(self):
    #     """ 商品吊牌价 """
    #     return self.prodouct.std_sale_price

    def update_start_and_end_time(self, start_time, end_time):
        """ 更新开始结束时间 """
        update_fields = []
        if self.start_time != start_time:
            self.start_time = start_time
            update_fields.append('start_time')
        if self.end_time != end_time:
            self.end_time = end_time
            update_fields.append('end_time')
        self.save(update_fields=update_fields)
