#-*- coding:utf8 -*-
from django.db import models


class SupplierType(models.Model):
    
    type_name = models.CharField(max_length=32,blank=True)
    extra_info = models.TextField(blank=True)
    
    class Meta:
        db_table = 'shop_purchases_suppliertype'

    def __unicode__(self):
        return self.type_name
    
    
    
class Supplier(models.Model):
    
    type           = models.ForeignKey(SupplierType,null=True,related_name='suppliers')
    
    supplier_name  = models.CharField(max_length=32,blank=True)
    contact        = models.CharField(max_length=32,blank=True)
    phone          = models.CharField(max_length=32,blank=True)
    mobile         = models.CharField(max_length=16,blank=True)
    fax            = models.CharField(max_length=16,blank=True)
    zip_code       = models.CharField(max_length=16,blank=True)
    email          = models.CharField(max_length=64,blank=True)
    
    address        = models.CharField(max_length=64,blank=True)
    account_bank   = models.CharField(max_length=32,blank=True)
    account_no     = models.CharField(max_length=32,blank=True)
    main_page      = models.CharField(max_length=256,blank=True)
    
    extra_info     = models.TextField(blank=True)
    class Meta:
        db_table = 'shop_purchases_supplier'

    def __unicode__(self):
        return self.supplier_name
    
    