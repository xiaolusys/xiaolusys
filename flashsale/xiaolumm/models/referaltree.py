# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models
from core.models import BaseModel

class MamaReferalTree(BaseModel):

    referal_to_mama_id = models.IntegerField(default=0, unique=True, verbose_name=u'小鹿妈妈id')
    referal_from_mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'上级妈妈id')

    direct_invite_num = models.IntegerField(default=0, db_index=True, verbose_name=u'直接邀请数')
    indirect_invite_num = models.IntegerField(default=0, db_index=True, verbose_name=u'间接邀请数')

    gradient = models.IntegerField(default=0, db_index=True, verbose_name=u'梯度')
    is_elite = models.BooleanField(default=False, db_index=True, verbose_name=u'精英妈妈')
    is_vip   = models.BooleanField(default=False, db_index=True, verbose_name=u'付费妈妈')

    last_active_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'最近活跃时间')

    class Meta:
        db_table = 'flashsale_xlmm_referaltree'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈树形关系数据'
        verbose_name_plural = u'V2/妈妈树形关系数据列表'

    def __unicode__(self):
        return '%s, %s, %s' % (self.referal_to_mama_id, self.direct_invite_num, self.gradient)