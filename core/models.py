#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
from django.db import models
from .ormcache import managers
from .managers import BaseManager #, BaseTagManager
# from django.contrib.auth.models import User as DJUser


class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, db_index=True, verbose_name=u'修改日期')

    objects = BaseManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        return str(self.id)

    def save(self, update_fields=[], *args, **kwargs):
        #　set modified field update default
        if update_fields and 'modified' not in update_fields:
            update_fields.append('modified')
        return super(BaseModel, self).save(*args, **kwargs)

    @classmethod
    def get_by_pk(cls, pk):
        return cls.objects.filter(pk=pk).first()

    @classmethod
    def get_apimodel_by_pk(cls, pk):
        model = cls.get_by_pk(pk)
        return cls.apimodelclass.init_by_model(model)


class AdminModel(BaseModel):
    creator = models.CharField(max_length=30,
                               blank=True,
                               null=True,
                               verbose_name=u'创建者')

    @property
    def creator_user(self):
        from django.contrib.auth.models import User as DJUser
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

    # objects = BaseTagManager()
    class Meta:
        abstract = True

    def __unicode__(self):
        return str(self.id)

