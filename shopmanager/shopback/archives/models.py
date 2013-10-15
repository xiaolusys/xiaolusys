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
    """ 仓库库位 """
    
    district_no  = models.CharField(max_length=32,blank=True,verbose_name='库位号')
    
    parent_no    = models.CharField(max_length=32,blank=True,verbose_name='父库位号')
    
    location     = models.CharField(max_length=64,blank=True,verbose_name='库位名')
    
    in_use       = models.BooleanField(default=True,verbose_name='使用')
    
    extra_info   = models.TextField(blank=True,verbose_name='备注')
    class Meta:
        db_table = 'shop_archives_depositedistrict'
        unique_together = ("parent_no","district_no")
        verbose_name=u'仓库区位'
        verbose_name_plural = u'仓库区位列表'

    def __unicode__(self):
        return '%s-%s'%(self.parent_no,self.district_no)
        
    
class SupplierType(models.Model):
    
    type_name = models.CharField(max_length=32,blank=True,verbose_name='类型名称')
    extra_info = models.TextField(blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_archives_suppliertype'
        verbose_name=u'供应商类型'
        verbose_name_plural = u'供应商类型列表'

    def __unicode__(self):
        return self.type_name
    
    
    
class Supplier(models.Model):
    
    supply_type           = models.ForeignKey(SupplierType,null=True,related_name='suppliers',verbose_name='供应商类型')

    supplier_name  = models.CharField(max_length=32,blank=True,unique=True,verbose_name='供应商名称')
    contact        = models.CharField(max_length=32,blank=True,verbose_name='联系方式')
    phone          = models.CharField(max_length=32,blank=True,verbose_name='电话')
    mobile         = models.CharField(max_length=16,blank=True,verbose_name='手机')
    fax            = models.CharField(max_length=16,blank=True,verbose_name='传真')
    zip_code       = models.CharField(max_length=16,blank=True,verbose_name='邮编')
    email          = models.CharField(max_length=64,blank=True,verbose_name='邮箱')
    
    address        = models.CharField(max_length=64,blank=True,verbose_name='地址')
    account_bank   = models.CharField(max_length=32,blank=True,verbose_name='汇款银行')
    account_no     = models.CharField(max_length=32,blank=True,verbose_name='汇款帐号')
    main_page      = models.CharField(max_length=256,blank=True,verbose_name='供应商主页')
    
    in_use      = models.BooleanField(default=True,verbose_name='使用')
    extra_info     = models.TextField(blank=True,verbose_name='备注')
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
