# coding=utf-8

from django.db import models
from core.models import BaseModel


class FaqMainCategory(BaseModel):
    icon_url = models.CharField(max_length=256, blank=True, verbose_name=u'图标地址')
    category_name = models.CharField(max_length=64, verbose_name=u'分类名称')
    description = models.CharField(max_length=512, verbose_name=u'分类描述')

    class Meta:
        db_table = 'flashsale_sale_faq_main_category'
        app_label = 'pay'
        verbose_name = u'特卖/常见问题主要分类表'
        verbose_name_plural = u'特卖/常见问题分类列表'

    def __unicode__(self):
        return u'%s:%s' % (self.id, self.category_name)

    def getDetailCategory(self):
        details = FaqsDetailCategory.objects.all()
        return details


class FaqsDetailCategory(BaseModel):
    main_category = models.ForeignKey(FaqMainCategory, verbose_name=u'主要分类')
    icon_url = models.CharField(max_length=256, blank=True, verbose_name=u'图标地址')
    category_name = models.CharField(max_length=64, verbose_name=u'分类名称')
    description = models.CharField(max_length=512, verbose_name=u'分类描述')

    class Meta:
        db_table = 'flashsale_sale_faq_detail_category'
        app_label = 'pay'
        verbose_name = u'特卖/常见问题详细分类表'
        verbose_name_plural = u'特卖/常见问题详细分类列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.category_name)


class SaleFaq(BaseModel):
    main_category = models.ForeignKey(FaqMainCategory, db_index=True, verbose_name=u'主要分类')
    detail_category = models.ForeignKey(FaqsDetailCategory, blank=True, verbose_name=u'详细分类')
    question = models.CharField(max_length=256, verbose_name=u'问题')
    answer = models.TextField(max_length=10240, verbose_name=u'回答')

    class Meta:
        db_table = 'flashsale_sale_faq'
        app_label = 'pay'
        verbose_name = u'特卖/常见问题表'
        verbose_name_plural = u'特卖/常见问题表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.detail_category)
