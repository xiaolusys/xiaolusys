#-*- coding: utf-8 -*-
import datetime
from django.db import models
from .ormcache import managers
from .managers import BaseManager, BaseTagManager
from django.contrib.auth.models import User as DJUser


class BaseModel(models.Model):
    created = models.DateTimeField(default=datetime.datetime.now, db_index=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, db_index=True, verbose_name=u'修改日期')

    objects = BaseManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        return str(self.id)


class AdminModel(BaseModel):
    creator = models.CharField(max_length=30,
                               blank=True,
                               null=True,
                               verbose_name=u'创建者')

    @property
    def creator_user(self):
        return DJUser.objects.get(username=self.creator)

    class Meta:
        abstract = True


class CacheModel(BaseModel):
    """ 需要对queryset结果做缓存的MODEL """

    objects = managers.CacheManager()
    cache_enabled = True

    class Meta:
        abstract = True


from .fields import TagField

class BaseTagModel(BaseModel):

    tags = TagField(null=True, verbose_name=u'标签')

    objects = BaseTagManager()
    class Meta:
        abstract = True

    def __unicode__(self):
        return str(self.id)

