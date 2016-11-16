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

    @classmethod
    def get_or_create_by_mama(cls, mama):
        from games.weixingroup.models import XiaoluAdministrator
        item = cls.objects.filter(mama_id=mama.id).first()
        if item:
            administrator = item.administrator
        else:
            administrators = XiaoluAdministrator.objects.filter(id__gte=11)
            num = mama.id % administrators.count()
            administrator = administrators[num]

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
