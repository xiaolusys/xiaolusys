# -*- coding:utf-8 -*-
import datetime
from django.db import models


class SampleFrozenScore(models.Model):
    FROZEN = 0
    CANCLE = 1
    COMPLETE = 2

    STATUS_CHOICES = ((FROZEN, u'冻结'),
                      (CANCLE, u'取消'),
                      (COMPLETE, u'完成'))

    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u'微信用户ID')
    sample_id = models.IntegerField(unique=True, verbose_name=u'试用订单ID')

    frozen_score = models.IntegerField(default=0, verbose_name=u'冻结积分')
    frozen_time = models.DateTimeField(null=True, blank=True, verbose_name=u'冻结截止')

    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')

    status = models.IntegerField(choices=STATUS_CHOICES, default=FROZEN, verbose_name=u"状态")

    class Meta:
        db_table = 'shop_weixin_score_frozen'
        app_label = 'weixin'
        verbose_name = u'试用冻结积分'
        verbose_name_plural = u'使用冻结积分列表'

    def __unicode__(self):
        return '%d' % self.frozen_score


from shopapp.signals import minus_frozenscore_signal
from shopapp.weixin.models import WeixinScoreItem, WeixinUserScore


def minus_frozenscore(sender, forzen_score_id, *args, **kwargs):
    try:
        record = SampleFrozenScore.objects.get(pk=forzen_score_id)
        user_openid = record.user_openid
        frozen_score = record.frozen_score

        WeixinScoreItem.objects.create(user_openid=user_openid,
                                       score=frozen_score,
                                       score_type=WeixinScoreItem.FROZEN,
                                       expired_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                       memo=u"冻结积分扣除(%d)。" % forzen_score_id)

        record.frozen_score = 0
        record.save()
    except Exception, exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'冻结积分扣除失败:%s' % exc.message, exc_info=True)


minus_frozenscore_signal.connect(minus_frozenscore, sender=SampleFrozenScore)
