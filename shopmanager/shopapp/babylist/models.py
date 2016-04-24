# -*- coding:utf8 -*-
__author__ = 'meixqhi'
from django.db import models


class BabyPhone(models.Model):
    fa_mobile = models.BigIntegerField(null=True, db_index=True, verbose_name='父亲号码')

    ma_mobile = models.BigIntegerField(null=True, db_index=True, verbose_name='母亲号码')

    name = models.CharField(max_length=64, blank=True, verbose_name='宝宝名')

    father = models.CharField(max_length=64, blank=True, db_index=True, verbose_name='父亲名')

    mather = models.CharField(max_length=64, blank=True, db_index=True, verbose_name='母亲名')

    state = models.CharField(max_length=32, blank=True, verbose_name='省')

    address = models.CharField(max_length=256, blank=True, verbose_name='地址')
    sex = models.CharField(max_length=3, blank=True, verbose_name='性别')

    born = models.DateField(null=True, blank=True, verbose_name='出生日期')
    code = models.CharField(max_length=64, blank=True, verbose_name='邮编')

    hospital = models.CharField(max_length=64, blank=True, verbose_name='医院')

    class Meta:
        db_table = 'shop_babylist_babyphone'
        app_label = 'babylist'
        verbose_name = u'新生儿童信息'
        verbose_name_plural = u'新生儿童信息列表'

    def __unicode__(self):
        return '<(%s,%s),(%s,%s)>' % (self.fa_mobile and str(self.fa_mobile) or '',
                                      self.father, self.ma_mobile and str(self.ma_mobile) or '', self.mather)
