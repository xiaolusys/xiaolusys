# encoding=utf8
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q

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

    @classmethod
    def get_or_create_by_mama(cls, mama):
        from games.weixingroup.models import XiaoluAdministrator
        item = cls.objects.filter(mama_id=mama.id).first()
        if item and item.administrator.status == 1:
            # administrator is effective
            administrator = item.administrator
        else:
            # administrators = XiaoluAdministrator.objects.filter(Q(id__gte=11) & Q(id__lte=18))
            administrators = XiaoluAdministrator.objects.filter(status=1, is_staff=True)
            num = mama.id % administrators.count()
            administrator = administrators[num]

            if item:
                # old administrator is not effective, change to a new administrator
                item.administrator = administrator
                item.save()
            else:
                ma = MamaAdministrator()
                ma.administrator = administrator
                ma.mama = mama
                ma.save()
        return administrator

    @classmethod
    def get_mama_administrator(cls, mama_id):
        adm = cls.objects.filter(mama_id=mama_id).first()
        if adm:
            return adm.administrator
        return None
