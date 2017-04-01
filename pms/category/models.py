# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import logging


class ProductCategory(models.Model):
    NORMAL = 'normal'
    DELETE = 'delete'

    CAT_STATUS = (
        (NORMAL, u'正常'),
        (DELETE, u'删除'),
    )

    cid = models.AutoField(primary_key=True, verbose_name=u'类目ID')
    parent_cid = models.IntegerField(null=False, verbose_name=u'父类目ID')
    name = models.CharField(max_length=32, blank=True, verbose_name=u'类目名')

    is_parent = models.BooleanField(default=True, verbose_name=u'有子类目')
    status = models.CharField(max_length=7, choices=CAT_STATUS, default=NORMAL, verbose_name=u'状态')
    sort_order = models.IntegerField(default=0, verbose_name=u'优先级')

    class Meta:
        db_table = 'product_category'
        app_label = 'category'
        verbose_name = u'特卖/产品类目'
        verbose_name_plural = u'特卖/产品类目列表'

    def __unicode__(self):

        if not self.parent_cid:
            return self.name
        try:
            p_cat = self.__class__.objects.get(cid=self.parent_cid)
        except:
            p_cat = u'【不存在】'
        return '%s / %s' % (p_cat, self.name)


class FirstCategory(models.Model):
    name = models.CharField(max_length=64, verbose_name=u'品类名称')
    code = models.IntegerField(default=1, verbose_name=u'编码')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')

    class Meta:
        db_table = 'supplychain_product_1st'
        app_label = 'category'
        verbose_name = u'1级品类'
        verbose_name_plural = u'1级品类列表'

    def __unicode__(self):
        return self.name


class SecondCategory(models.Model):
    parent = models.ForeignKey(FirstCategory)
    name = models.CharField(max_length=64, verbose_name=u'品类名称')
    code = models.IntegerField(default=1, verbose_name=u'编码')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')

    @property
    def encoded(self):
        return "%s%02d" % (self.parent.code, self.code)

    class Meta:
        db_table = 'supplychain_product_2nd'
        app_label = 'category'
        verbose_name = u'2级品类'
        verbose_name_plural = u'2级品类列表'

    def __unicode__(self):
        return '/'.join([str(self.parent), self.name])


class ThirdCategory(models.Model):
    parent = models.ForeignKey(SecondCategory)
    name = models.CharField(max_length=64, verbose_name=u'品类名称')
    code = models.IntegerField(default=1, verbose_name=u'编码')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')

    @property
    def encoded(self):
        return "%s%02d" % (self.parent.encoded, self.code)

    class Meta:
        db_table = 'supplychain_product_3rd'
        app_label = 'category'
        verbose_name = u'3级 产品具体名称'
        verbose_name_plural = u'3级 产品具体名称'

    def __unicode__(self):
        return '/'.join([str(self.parent), self.name])


class FourthCategory(models.Model):
    parent = models.ForeignKey(ThirdCategory)
    name = models.CharField(max_length=64, verbose_name=u'品类名称')
    code = models.IntegerField(default=1, verbose_name=u'编码')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')

    @property
    def encoded(self):
        return "%s%02d" % (self.parent.encoded, self.code)

    class Meta:
        db_table = 'supplychain_product_4th'
        app_label = 'category'
        verbose_name = u'4级 品牌名称'
        verbose_name_plural = u'4级 品牌名称'

    def __unicode__(self):
        return '/'.join([str(self.parent), self.name])


class FifthCategory(models.Model):
    parent = models.ForeignKey(FourthCategory)
    name = models.CharField(max_length=64, verbose_name=u'品类名称')
    code = models.IntegerField(default=1, verbose_name=u'编码')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')

    @property
    def encoded(self):
        return "%s%02d" % (self.parent.encoded, self.code)

    class Meta:
        db_table = 'supplychain_product_5th'
        app_label = 'category'
        verbose_name = u'5级 款式描述'
        verbose_name_plural = u'5级 款式描述'

    def __unicode__(self):
        return '/'.join([str(self.parent), self.name])


class SixthCategory(models.Model):
    parent = models.ForeignKey(FifthCategory)
    name = models.CharField(max_length=64, verbose_name=u'品类名称')
    code = models.IntegerField(default=1, verbose_name=u'编码')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')

    class Meta:
        db_table = 'supplychain_product_6th'
        app_label = 'category'
        verbose_name = u'6级 尺寸'
        verbose_name_plural = u'6级 尺寸'

    def __unicode__(self):
        return '/'.join([str(self.parent), self.name])

    