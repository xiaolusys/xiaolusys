# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models
from core.models import BaseModel

class AccountSubject(BaseModel):

    name = models.CharField(max_length=32, blank=False, verbose_name=u'科目名称')
    summary = models.IntegerField( default=0, verbose_name=u'汇总金额')

    class Meta:
        db_table = 'flashsale_account_subject'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈账单科目'
        verbose_name_plural = u'V2/妈妈账单科目列表'

    def __unicode__(self):
        return '<%s>' % (self.id)

class AccountSummary(BaseModel):

    user_id = models.IntegerField(default=0, verbose_name=u'用户ID')
    subject = models.ForeignKey(AccountSubject, related_name='summarys', verbose_name=u'科目')
    value   = models.IntegerField(default=0, verbose_name=u'金额')


    class Meta:
        db_table = 'flashsale_account_summary'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈账单汇总'
        verbose_name_plural = u'V2/妈妈账单汇总列表'

    def __unicode__(self):
        return '<%s>' % (self.id)


class AccountEntry(BaseModel):

    IN  = 'in'
    OUT = 'out'
    IRO_CHOICES = (
        (IN, '收入'),
        (OUT, '支出')
    )

    user_id = models.IntegerField(default=0, verbose_name=u'用户ID')
    subject = models.ForeignKey(AccountSubject, related_name='summarys', verbose_name=u'科目')
    value   = models.IntegerField(default=0, verbose_name=u'金额')
    iro_type = models.CharField(max_length=4, db_index=True, choices=IRO_CHOICES, verbose_name=u'收支类型')
    obj_id = models.CharField(max_length=64, db_index=True, verbose_name=u'生成记录外部ID', help_text=u'double entry纪录的值才可以相同')

    class Meta:
        db_table = 'flashsale_account_entry'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈账单复式记录'
        verbose_name_plural = u'V2/妈妈账单复式记录列表'

    def __unicode__(self):
        return '<%s>' % (self.id)

