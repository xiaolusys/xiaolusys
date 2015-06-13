#-*- coding:utf-8 -*-
import random
import datetime
from django.db import models
from django.db.models import Q,Sum
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction
from django.forms.models import model_to_dict


class XiaoluMamaManager(models.Manager):   
    
    def get_queryset(self):
        
        super_tm = super(XiaoluMamaManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set()
        return super_tm.get_queryset()
    
    
    def  charge(self,xlmm,user,*args,**kwargs):
        
        if xlmm.charge_status == self.model.CHARGED:
            return False
        
        xlmm.manager = user.id
        xlmm.charge_status = self.model.CHARGED
        xlmm.save()
        
        return True
        
    
    def  uncharge(self,xlmm,*args,**kwargs):
        
        xlmm.charge_status = self.model.UNCHARGE
        xlmm.save()
    
    @property
    def normal_queryset(self):
        
        queryset = self.get_queryset()
        return queryset.filter(status=self.model.EFFECT)
    
    
    