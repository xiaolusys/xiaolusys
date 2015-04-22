#-*- coding:utf8 -*-
from django.db import models
from django.db.models import Q,Sum



class UserAddressManager(models.Manager):
    

    def get_query_set(self):
        
        super_tm = super(UserAddressManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set().filter(status=self.model.NORMAL).order_by('-created')
        
        return super_tm.get_queryset().filter(status=self.model.NORMAL).order_by('-created')
    
    def get_queryset(self):
        
        return self.get_query_set()
    
    

    