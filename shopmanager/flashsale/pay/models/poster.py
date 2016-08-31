# -*- coding:utf-8 -*-
import json
import datetime
from django.db import models
from django.db.models import F

from tagging.fields import TagField
from core.utils.modelutils import update_model_fields
from core.fields import JSONCharMyField
from core.models import BaseTagModel
from .base import PayBaseModel, BaseModel

from flashsale.promotion.models import ActivityEntry

import logging
logger = logging.getLogger(__name__)

DEFAULT_WEN_POSTER = [
    {
        "subject": ['2折起', '小鹿美美  女装专场'],
        "item_link": "/mall/product/list/lady",
        "app_link": "com.jimei.xlmm://app/v1/products/ladylist",
        "pic_link": ""
    }
]

DEFAULT_CHD_POSTER = [
    {
        "subject": ['2折起', '小鹿美美  童装专场'],
        "item_link": "/mall/product/list/child",
        "app_link": "com.jimei.xlmm://app/v1/products/childlist",
        "pic_link": ""
    }
]

def default_wen_poster():
    return json.dumps(DEFAULT_WEN_POSTER, indent=2)

def default_chd_poster():
    return json.dumps(DEFAULT_WEN_POSTER, indent=2)

class GoodShelf(PayBaseModel):
    DEFAULT_WEN_POSTER = DEFAULT_WEN_POSTER
    DEFAULT_CHD_POSTER = DEFAULT_CHD_POSTER

    title = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'海报名称')

    wem_posters = JSONCharMyField(max_length=10240, blank=True,
                                  default=default_wen_poster,
                                  verbose_name=u'女装海报')
    chd_posters = JSONCharMyField(max_length=10240, blank=True,
                                  default=default_chd_poster,
                                  verbose_name=u'童装海报')

    is_active = models.BooleanField(default=True, verbose_name=u'上线')
    active_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'上线日期')

    class Meta:
        db_table = 'flashsale_goodshelf'
        app_label = 'pay'
        verbose_name = u'特卖商品/海报'
        verbose_name_plural = u'特卖商品/海报列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)

    def get_cat_imgs(self):
        from supplychain.supplier.models.category import SaleCategory
        lv1_category = SaleCategory.objects.filter(grade=1)
        child_category = lv1_category.filter(cid__exact='1').first()
        women_category = lv1_category.filter(cid__exact='2').first()
        food_category = lv1_category.filter(cid__exact='3').first()
        other_category = lv1_category.filter(cid__exact='6').first()
        if (not child_category) or (not women_category) or (not food_category) or (not other_category):
            return []

        return [
            {'id': 1, 'name': u'童装专区',
             'cat_img': child_category.cat_pic,
             'cat_link': 'com.jimei.xlmm://app/v1/products/category?cid=1'},
            {'id': 2, 'name': u'女装专区',
             'cat_img': women_category.cat_pic,
             'cat_link': 'com.jimei.xlmm://app/v1/products/category?cid=2'},
            {'id': 3, 'name': u'美食专区',
             'cat_img': food_category.cat_pic,
             'cat_link': 'com.jimei.xlmm://app/v1/products/category?cid=3'},
            {'id': 4, 'name': u'美妆家居',
             'cat_img': other_category.cat_pic,
             'cat_link': 'com.jimei.xlmm://app/v1/products/category?cid=4,5,6,7,8'},
        ]

    def get_posters(self):
        return self.wem_posters + self.chd_posters

    def get_activity(self):
        return ActivityEntry.get_default_activity()

    def get_current_activitys(self):
        now = datetime.datetime.now()
        return ActivityEntry.get_landing_effect_activitys(now)


