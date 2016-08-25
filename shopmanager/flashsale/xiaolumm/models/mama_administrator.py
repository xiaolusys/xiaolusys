# encoding=utf8
from django.db import models
from core.models import BaseModel
from flashsale.xiaolumm.models.models import XiaoluMama


class MamaAdministrator(BaseModel):

    mama = models.ForeignKey(XiaoluMama)
    administrator = models.ForeignKey('weixingroup.XiaoluAdministrator')

    class Meta:
        db_table = 'xiaolumm_mamaadministrator'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈管理员'
        verbose_name_plural = u'小鹿妈妈管理员列表'
