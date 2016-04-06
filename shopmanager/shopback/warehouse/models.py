#-*- coding:utf8 -*-
from django.utils.encoding import smart_unicode
from django.db import models


class WareHouse(models.Model):
    """ 仓库 """
    
    ware_name = models.CharField(max_length=32,blank=True,verbose_name='仓库名')
    city      = models.CharField(max_length=32,blank=True,verbose_name='所在城市')
    address   = models.TextField(max_length=256,blank=True,verbose_name='详细地址')
    
    in_active    = models.BooleanField(default=True,verbose_name='有效')
    extra_info   = models.TextField(blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_ware_house'
        app_label = 'warehouse'
        verbose_name=u'仓库'
        verbose_name_plural = u'仓库列表'

    def __unicode__(self):
        return smart_unicode(self.ware_name)
    
