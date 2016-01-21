# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

class BaseModel(models.Model):
    
    created  = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return str(self.id)
    
class AdminModel(BaseModel):
    
    creator  = models.CharField(max_length=2,blank=True,null=True,verbose_name=u'创建者')
    
    class Meta:
        abstract = True
        