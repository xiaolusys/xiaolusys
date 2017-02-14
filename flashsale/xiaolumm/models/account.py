# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models
from core.models import BaseModel


class AccountSubject(BaseModel):

    code = models.CharField(max_length=16, db_index=True, verbose_name=u'科目代码')
    name = models.CharField(max_length=32, verbose_name=u'科目名称')
    parent = models.CharField(max_length=16, verbose_name=u'父级科目代码')

    class Meta:
        db_table = 'flashsale_account_subject'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈账单科目'
        verbose_name_plural = u'V2/妈妈账单科目列表'

    def __unicode__(self):
        return '<%s>' % (self.id)


# class AccountSummary(BaseModel):
#     """ 该存档汇总记录只供参考 """
#     NOW_SUM   = 'now'
#     WEEK_SUM  = 'week'
#     MONTH_SUM = 'month'
#     YEAR_SUM  = 'year'
#
#     SUMMARY_TYPE_CHOICES = (
#         (NOW_SUM, u'实际发生值'),
#         (WEEK_SUM, u'周存档'),
#         (MONTH_SUM, u'月存档'),
#         (YEAR_SUM, u'年存档'),
#     )
#
#     user_id = models.IntegerField(default=0, verbose_name=u'用户ID')
#     subject = models.ForeignKey(AccountSubject, related_name='summarys', verbose_name=u'科目')
#     value   = models.IntegerField(default=0, verbose_name=u'发生金额')
#     sum_type = models.CharField(max_length=8, db_index=True, verbose_name=u'存档类型')
#     sum_key  = models.CharField(max_length=32, db_index=True, verbose_name=u'存档标识', help_text=u'如([年]-[月]), 2016-12')
#
#     class Meta:
#         db_table = 'flashsale_account_summary'
#         app_label = 'xiaolumm'
#         verbose_name = u'V2/妈妈账单汇总'
#         verbose_name_plural = u'V2/妈妈账单汇总列表'
#
#     def __unicode__(self):
#         return '<%s>' % (self.id)


class AccountEntry(BaseModel):

    IN  = 'in'
    OUT = 'out'
    IRO_CHOICES = (
        (IN, '收入'),
        (OUT, '支出')
    )

    customer_id = models.IntegerField(default=0, verbose_name=u'用户ID')
    subject = models.ForeignKey(AccountSubject, verbose_name=u'科目')
    amount = models.IntegerField(default=0, verbose_name=u'金额(分)')
    obj_id = models.CharField(max_length=64, db_index=True, verbose_name=u'生成记录外部ID', help_text=u'两条double entry纪录的值必须相同')
    referal_id = models.CharField(max_length=32, blank=True, verbose_name=u'引用id')

    class Meta:
        db_table = 'flashsale_account_entry'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈账单复式记录'
        verbose_name_plural = u'V2/妈妈账单复式记录列表'

    @classmethod
    def create(cls, customer_id, debit, lender, amount, referal_id=''):
        import os
        obj_id = os.urandom(16).encode('hex')

        try:
            debit = AccountSubject.objects.get(code=debit)
            lender = AccountSubject.objects.get(code=lender)

            AccountEntry.objects.create(customer_id=customer_id, subject=debit, amount=-amount,
                                        obj_id=obj_id, referal_id=referal_id)
            AccountEntry.objects.create(customer_id=customer_id, subject=lender, amount=amount,
                                        obj_id=obj_id, referal_id=referal_id)
        except Exception:
            return

    def __unicode__(self):
        return '<%s>' % (self.id)

