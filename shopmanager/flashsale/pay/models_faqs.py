# coding=utf-8

from django.db import models
from core.models import BaseModel


class SaleFaqs(BaseModel):
    OTHER = 0
    SALE = 1
    TRADE = 2
    AGENCY = 3

    QUESTION_TYPE = ((SALE, u'购物问题'), (TRADE, u'订单问题'), (AGENCY, u'代理问题'), (OTHER, u'其他问题'))

    LOGISTICS = 0
    AFTER_SALE = 1
    SALES_RETURN = 2
    SALES_REFUND = 3

    MAMA_JOIN = 4
    MAMA_OUT = 5
    CARRY_Q = 6
    ACTIVE_Q = 7

    DETAIL_TYPE = ((LOGISTICS, u'物流问题'), (AFTER_SALE, u'售后问题'), (SALES_RETURN, u'退货问题'), (SALES_REFUND, u'退款问题'),

                   (MAMA_JOIN, u'招募问题'), (MAMA_OUT, u'退出问题'), (CARRY_Q, u'佣金问题'), (ACTIVE_Q, u'活动问题'))

    question_type = models.IntegerField(choices=QUESTION_TYPE, default=0, db_index=True, verbose_name=u'主分类')
    detail_type = models.IntegerField(choices=DETAIL_TYPE, default=0, db_index=True, verbose_name=u'详细分类')
    question = models.CharField(max_length=256, verbose_name=u'问题')
    answer = models.TextField(max_length=10240, verbose_name=u'回答')

    class Meta:
        db_table = 'flashsale_sale_faqs'
        verbose_name = u'特卖/常见问题表'
        verbose_name_plural = u'特卖/常见问题表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.question_type)


