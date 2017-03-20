# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType

from core.models import BaseModel
from .. import constants

class BaseWareModel(models.Model):

    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, db_index=True, verbose_name=u'修改日期')

    class Meta:
        abstract = True

    def __unicode__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        #　set modified field update default
        update_fields = kwargs.get('update_fields')
        if update_fields and 'modified' not in update_fields:
            update_fields.append('modified')

        return super(BaseWareModel, self).save( *args, **kwargs)


class OutwareActionRecord(BaseModel):

    STATE_CHOICES = (
        (constants.GOOD, '良好'),
        (constants.ERROR, '出错'),
    )

    record_obj  = models.ForeignKey(ContentType, blank=True, null=True, verbose_name=u'关联对象')
    object_id   = models.IntegerField(db_index=True, verbose_name=u'记录对象id')
    action_code = models.CharField(max_length=8, db_index=True, verbose_name=u'操作编号')
    state_code  = models.IntegerField(db_index=True, choices=STATE_CHOICES, verbose_name='状态编码')
    message     =  models.CharField(max_length=256, verbose_name='操作信息')

    class Meta:
        db_table = 'outware_action_record'
        app_label = 'outware'
        verbose_name = u'外仓/操作记录'
        verbose_name_plural = u'外仓/操作记录'


def log_ware_action(obj, action_code, state_code=constants.GOOD, message=''):
    try:
        OutwareActionRecord.objects.create(
            record_obj=ContentType.objects.get_for_model(obj),
            object_id=obj.id,
            action_code=action_code,
            state_code=state_code,
            message=message,
        )
    except Exception,exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(str(exc), exc_info=True)