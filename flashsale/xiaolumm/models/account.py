# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models
from core.models import BaseModel

class AccountSubject(BaseModel):

    name = models.CharField(max_length=32, blank=False, verbose_name=u'科目名称')
    summary = models.IntegerField( default=0, verbose_name=u'汇总金额')

    class Meta:
        db_table = 'flashsale_xlmm_account_subject'
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
        db_table = 'flashsale_xlmm_account_summary'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈账单汇总'
        verbose_name_plural = u'V2/妈妈账单汇总列表'

    def __unicode__(self):
        return '<%s>' % (self.id)


class AccountEntry(models.Model):

    IN  = 'in'
    OUT = 'out'


    user_id = models.IntegerField(default=0, verbose_name=u'用户ID')
    subject = models.ForeignKey(AccountSubject, related_name='summarys', verbose_name=u'科目')
    value   = models.IntegerField(default=0, verbose_name=u'金额')
    inorout = models.IntegerField()

    class Meta:
        db_table = 'flashsale_xlmm_account_entry'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈账单复式记录'
        verbose_name_plural = u'V2/妈妈账单复式记录列表'

    def __unicode__(self):
        return '<%s>' % (self.id)

