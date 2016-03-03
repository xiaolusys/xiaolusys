# coding=utf-8
from django.db import models
from core.models import BaseModel


class MamaFortune(BaseModel):
    mama_id = models.BigIntegerField(default=0, db_index=True, unique=True, verbose_name=u'小鹿妈妈id')
    mama_name = models.CharField(max_length=32, blank=True, verbose_name=u'名称')
    mam_level = models.IntegerField(default=0, verbose_name=u'级别')
    cash_num = models.IntegerField(default=0, verbose_name=u'余额')
    fans_num = models.IntegerField(default=0, verbose_name=u'粉丝数')
    invite_num = models.IntegerField(default=0, verbose_name=u'邀请数')
    order_num = models.IntegerField(default=0, verbose_name=u'订单数')
    carry_num = models.IntegerField(default=0, verbose_name=u'累计收益数')
    active_value_num = models.IntegerField(default=0, verbose_name=u'活跃数')
    today_visitor_num = models.IntegerField(default=0, verbose_name=u'今日访客数')

    class Meta:
        db_table = 'flashsale_xlmm_fortune'
        verbose_name = u'妈妈财富表'
        verbose_name_plural = u'妈妈财富列表'

    def __unicode__(self):
        return '%s,%s' % (self.mama_id, self.mama_name)