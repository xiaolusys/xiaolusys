# -*- coding:utf-8 -*-
import json
import datetime
from django.db import models

from core.fields import JSONCharMyField
from core.models import BaseModel

import logging
logger = logging.getLogger(__name__)

class ActivityEntry(BaseModel):
    """ 商城活动入口 """

    ACT_COUPON  = 'coupon'
    ACT_WEBVIEW = 'webview'
    ACT_MAMA    = 'mama'
    ACT_BRAND   = 'brand'
    ACT_TOP     = 'atop'
    ACT_TOPIC   = 'topic'

    ACT_CHOICES = (
        (ACT_WEBVIEW, u'商城活动页'),
        (ACT_BRAND, u'商城Top10'),
        (ACT_TOPIC, u'专题活动'),
        (ACT_BRAND, u'品牌活动'),
        (ACT_COUPON, u'优惠券活动'),
        (ACT_MAMA, u'妈妈活动'),
    )

    title = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'活动名称')

    act_desc = models.TextField(max_length=512, blank=True, verbose_name=u'活动描述')
    act_img = models.CharField(max_length=256, blank=True, verbose_name=u'活动入口图片')
    act_link = models.CharField(max_length=256, blank=True, verbose_name=u'活动链接')
    mask_link = models.CharField(max_length=256, blank=True, verbose_name=u'活动弹窗提示图')
    act_applink = models.CharField(max_length=256, blank=True, verbose_name=u'活动APP协议链接')
    share_icon = models.CharField(max_length=128, blank=True, verbose_name=u'活动分享图片')
    share_link = models.CharField(max_length=256, blank=True, verbose_name=u'活动分享链接')
    act_type = models.CharField(max_length=8, choices=ACT_CHOICES,
                                db_index=True, verbose_name=u'活动类型')

    login_required = models.BooleanField(default=False, verbose_name=u'需要登陆')
    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')

    order_val = models.IntegerField(default=0, verbose_name=u'排序值')

    extras = JSONCharMyField(max_length=5120, default={}, blank=True, verbose_name=u'活动数据')
    is_active = models.BooleanField(default=True, verbose_name=u'上线')

    class Meta:
        db_table = 'flashsale_activity_entry'
        app_label = 'pay'
        verbose_name = u'特卖/商城活动入口'
        verbose_name_plural = u'特卖/商城活动入口'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)

    @classmethod
    def get_default_activity(cls):
        acts = cls.objects.filter(is_active=True,
                                  end_time__gte=datetime.datetime.now()) \
            .exclude(act_type=ActivityEntry.ACT_MAMA).order_by('-order_val', '-modified')
        if acts.exists():
            return acts[0]
        return None

    @classmethod
    def get_effect_activitys(cls, active_time):
        """ 根据时间获取活动列表 """
        acts = cls.objects.filter(is_active=True,
                                  end_time__gte=active_time) \
            .order_by('-order_val', '-modified')
        if acts.exists():
            return acts
        return cls.objects.none()

    @classmethod
    def get_landing_effect_activitys(cls, active_time):
        """ 根据时间获取活动列表app首页展示 """
        acts = cls.objects.filter(is_active=True,
                                  end_time__gte=active_time) \
            .exclude(act_type=ActivityEntry.ACT_MAMA).order_by('-order_val', '-modified')
        if acts.exists():
            return acts
        return cls.objects.none()

    def get_shareparams(self, **params):
        return {
            'id': self.id,
            'title': self.title.format(**params),
            'share_type': 'link',
            'share_icon': self.share_icon,
            'share_link': self.share_link.format(**params),
            'active_dec': self.act_desc.format(**params),
        }

    def get_html(self, key):
        htmls = self.extras["html"]
        if key in htmls:
            return htmls[key]
        return None

    def total_member_num(self):
        return 2000

    def friend_member_num(self):
        return 16


class ActivityProduct(BaseModel):
    """ 品牌商品信息 """

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
    activity = models.ForeignKey(ActivityEntry, related_name='brand_products', verbose_name=u'所属专题')

    product_id = models.BigIntegerField(db_index=True, default=0, verbose_name=u'商品ID')
    model_id = models.BigIntegerField(db_index=True, default=0, verbose_name=u'商品款式ID')
    product_name = models.CharField(max_length=64, blank=True, verbose_name=u'商品名称')
    product_img = models.CharField(max_length=256, blank=True, verbose_name=u'商品图片')

    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')

    location_id = models.IntegerField(default=0, verbose_name=u'位置')
    pic_type = models.IntegerField(choices=PIC_TYPE_CHOICES, default=GOODS_VERTICAL_PIC_TYPE,
                                   db_index=True, verbose_name=u'图片类型')

    class Meta:
        db_table = 'flashsale_activity_product'
        app_label = 'pay'
        verbose_name = u'特卖/专题商品'
        verbose_name_plural = u'特卖/专题商品列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.brand_name)

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