#-*- coding:utf8 -*-
from django.db import models



class Deposite(models.Model):
    """ 仓库 """
    
    deposite_name = models.CharField(max_length=32,blank=True,verbose_name='仓库名')
    location     = models.CharField(max_length=32,blank=True,verbose_name='仓库位置')
    
    in_use       = models.BooleanField(default=True,verbose_name='使用')
    extra_info   = models.TextField(blank=True,verbose_name='备注')
    class Meta:
        db_table = 'shop_archives_deposite'
        verbose_name=u'仓库'
        verbose_name_plural = u'仓库列表'

    def __unicode__(self):
        return self.deposite_name
    
    
class DepositeDistrict(models.Model):
    """ 仓库区位 """
    
    deposite     = models.ForeignKey(Deposite,null=True,blank=True,related_name='deposite_districts',verbose_name='仓库')
    district_no  = models.CharField(max_length=32,blank=True,verbose_name='区位号')
    location     = models.CharField(max_length=32,blank=True,verbose_name='区位置')
    
    in_use       = models.BooleanField(default=True,verbose_name='使用')
    extra_info   = models.TextField(blank=True,verbose_name='备注')
    class Meta:
        db_table = 'shop_archives_depositedistrict'
        verbose_name=u'仓库区位'
        verbose_name_plural = u'仓库区位列表'

    def __unicode__(self):
        return '<%s,%s>'%(self.district_no,self.location)
        
    
class SupplierType(models.Model):
    
    type_name = models.CharField(max_length=32,blank=True)
    extra_info = models.TextField(blank=True)
    
    class Meta:
        db_table = 'shop_archives_suppliertype'
        verbose_name=u'供应商类型'
        verbose_name_plural = u'供应商类型列表'

    def __unicode__(self):
        return self.type_name
    
    
    
class Supplier(models.Model):
    
    supply_type           = models.ForeignKey(SupplierType,null=True,related_name='suppliers')

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
    
    in_use      = models.BooleanField(default=True)
    extra_info     = models.TextField(blank=True)
    class Meta:
        db_table = 'shop_archives_supplier'
        verbose_name=u'供应商'
        verbose_name_plural = u'供应商列表'

    def __unicode__(self):
        return self.supplier_name
    
    
class PurchaseType(models.Model):
    """ 采购类型 """
    
    type_name    = models.CharField(max_length=32,blank=True,verbose_name='采购类型')
    in_use       = models.BooleanField(default=True,verbose_name='使用')
    
    extra_info   = models.TextField(blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_archives_purchasetype'
        verbose_name=u'采购类型'
        verbose_name_plural = u'采购类型列表'

    def __unicode__(self):
        return self.type_name    
