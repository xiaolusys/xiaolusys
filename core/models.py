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


def multi_update(model_class, key_attr, value_attr, res, where=''):
    """
        批量更新数据
        至多一次更新2000W,更多要更新数据库架构啦
    :param model_class: 对应model
    :param key_attr: 识别记录的字段（需要唯一）
    :param value_attr: 要改值的字段
    :param res: 设置的值字典
    :param where: 额外限定条件
    :return:
    """
    from django.db import connection, transaction
    if not res:
        raise Exception('set values res empty')
    sql_begin = 'UPDATE %s SET %s = CASE %s ' % (model_class._meta.db_table, value_attr, key_attr)
    sql_when_str = lambda key: 'WHEN %s THEN %s' % (key, res[key])
    sql_whens_list = []
    SLICE_LEN = 20000
    res_keys = res.keys()
    for i in range(0, 1000):
        slice = res_keys[i * SLICE_LEN: i * SLICE_LEN + SLICE_LEN]
        sql_whens_list.append(slice)
    for item in sql_whens_list:
        if item:
            sql_end = ' END where %s in (%s)' % (key_attr, ','.join([str(i) for i in item]))
            if where:
                sql_end = sql_end + ' AND ' + where
            sql = sql_begin + ' '.join([sql_when_str(key) for key in item]) + sql_end
            cursor = connection.cursor()
            cursor.execute(sql)
            cursor.close()