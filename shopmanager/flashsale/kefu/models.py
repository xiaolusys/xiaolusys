# -*- coding:utf-8 -*-
from django.db import models
from flashsale.signals import signal_kefu_operate_record


class KefuPerformance(models.Model):
    CHECK = u'check'
    REVIEW = u'review'
    DELAY = u'delay'
    OPERATE_TYPE = (
        (CHECK, u'审核订单'),
        (REVIEW, u'重审订单'),
        (DELAY, u'延时'),
    )
    kefu_id = models.BigIntegerField(db_index=True, verbose_name=u'客服ID')
    kefu_name = models.CharField(db_index=True, max_length=32, verbose_name=u'客服名字')
    operation = models.CharField(db_index=True, choices=OPERATE_TYPE, max_length=32, verbose_name=u'操作')
    trade_id = models.BigIntegerField(verbose_name=u'订单ID')
    operate_time = models.DateTimeField(verbose_name=u'操作时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'flashsale_kefu_record'
        app_label = 'kefu'
        verbose_name = u'客服操作记录'
        verbose_name_plural = u'客服操作记录表'

    def __unicode__(self):
        return "{0},{1}".format(self.kefu_name, self.operation)


def performance_record(sender, **kwargs):
    """记录客服操作"""
    from django.contrib.auth.models import User
    from shopback.trades.models import MergeTrade
    import datetime
    if u"trade_id" in kwargs:
        trade_id = kwargs.get("trade_id")
    if u"operation" in kwargs:
        operation = kwargs.get("operation")
    if u"kefu_id" in kwargs:
        kefu_id = kwargs.get("kefu_id")

    try:
        merge_trade = MergeTrade.objects.get(id=trade_id)
        if not merge_trade.can_review:
            log_user = User.objects.get(id=kefu_id)
            new_record = KefuPerformance(kefu_id=kefu_id, kefu_name=log_user.username, operation=operation,
                                         trade_id=trade_id, operate_time=datetime.datetime.now())
            new_record.save()
    except:
        pass


signal_kefu_operate_record.connect(performance_record, sender=KefuPerformance)
