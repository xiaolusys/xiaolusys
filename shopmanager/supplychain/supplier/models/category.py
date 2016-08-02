# -*- coding:utf-8 -*-

from django.core.cache import cache
from django.db import models

from core.models import BaseModel

def default_salecategory_cid():
    sc = SaleCategory.objects.order_by('-cid').first()
    if sc:
        return sc.cid + 1
    return 1

class SaleCategory(BaseModel):
    NORMAL = 'normal'
    DELETE = 'delete'

    CAT_STATUS = ((NORMAL, u'正常'),
                  (DELETE, u'删除'))

    FIRST_GRADE = 1

    SALEPRODUCT_CATEGORY_CACHE_KEY = 'xlmm_saleproduct_category_cache'

    cid = models.IntegerField(null=False, default=default_salecategory_cid, unique=True, verbose_name=u'类目ID')
    parent_cid = models.IntegerField(null=False, db_index=True, verbose_name=u'父类目ID')
    name = models.CharField(max_length=64, blank=True, verbose_name=u'类目名')

    grade     = models.IntegerField(default=0, db_index=True, verbose_name=u'类目等级')
    is_parent = models.BooleanField(default=True, verbose_name=u'父类目')
    sort_order = models.IntegerField(default=0, verbose_name=u'权值')

    status = models.CharField(max_length=7, choices=CAT_STATUS, default=NORMAL, verbose_name=u'状态')

    class Meta:
        db_table = 'supplychain_sale_category'
        app_label = 'supplier'
        verbose_name = u'特卖/选品类目'
        verbose_name_plural = u'特卖/选品类目列表'

    def __unicode__(self):

        if not self.parent_cid:
            return self.name
        try:
            p_cat = self.__class__.objects.get(id=self.parent_cid)
        except:
            p_cat = u'--'
        return '%s / %s' % (p_cat, self.name)

    def save(self, *args, **kwargs):
        if self.parent_cid > 0 :
            parent_cat = SaleCategory.objects.filter(cid=self.parent_cid).first()
            self.grade = parent_cat.grade + 1
        return super(SaleCategory, self).save(*args, **kwargs)

    @property
    def full_name(self):
        return self.__unicode__()

    @classmethod
    def get_category_names(cls, cid):
        categories = cache.get(cls.SALEPRODUCT_CATEGORY_CACHE_KEY)
        if not categories:
            categories = {}
            for category in cls.objects.filter(
                    status=u'normal').order_by('created'):
                categories[category.id] = {
                    'cid': category.id,
                    'pid': category.parent_cid or 0,
                    'name': category.name
                }
            cache.set(cls.SALEPRODUCT_CATEGORY_CACHE_KEY, categories)
        level_1_category_name, level_2_category_name = ('-',) * 2
        category = categories.get(cid)
        if category:
            pid = category['pid']
            if not pid:
                level_1_category_name = category['name']
            else:
                level_2_category_name = category['name']
                level_1_category_name = (categories.get(pid) or
                                         {}).get('name') or ''
        return level_1_category_name, level_2_category_name

    def get_firstgrade_category(self):
        if self.grade == self.FIRST_GRADE:
            return self

        parant_cat = SaleCategory.objects.filter(cid=self.parent_cid).first()
        cnt = 0
        while parant_cat and cnt < 10:
            tmp_cat = SaleCategory.objects.filter(cid=parant_cat.parent_cid).first()
            if not tmp_cat:
                return parant_cat
            parant_cat = tmp_cat
            cnt += 1
        return None



