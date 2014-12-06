#-*- coding:utf8 -*-
from django.db import models


class SaleSupplier(models.Model):

    supplier_code   =   models.CharField(max_length=64,unique=True, blank=True,verbose_name=u'品牌缩写')
    supplier_name =   models.CharField(max_length=64,unique=True,blank=True,verbose_name=u'店铺名称')
    
    brand_url  = models.CharField(max_length=512, blank=True,verbose_name=u'商标图')
    main_page      = models.CharField(max_length=256,blank=True,verbose_name='品牌主页')
    
    contact        = models.CharField(max_length=32,blank=True,verbose_name='联系人')
    phone          = models.CharField(max_length=32,blank=True,verbose_name='电话')
    mobile         = models.CharField(max_length=16,blank=True,verbose_name='手机')
    fax            = models.CharField(max_length=16,blank=True,verbose_name='传真')
    zip_code       = models.CharField(max_length=16,blank=True,verbose_name='邮编')
    email          = models.CharField(max_length=64,blank=True,verbose_name='邮箱')
    
    address        = models.CharField(max_length=64,blank=True,verbose_name='地址')
    account_bank   = models.CharField(max_length=32,blank=True,verbose_name='汇款银行')
    account_no     = models.CharField(max_length=32,blank=True,verbose_name='汇款帐号')
    
    created    = models.DateTimeField(auto_now_add=True,verbose_name=u'创建日期')
    modified   = models.DateTimeField(auto_now=True,verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_grandsale_supplier'
        verbose_name=u'特卖 供应商'
        verbose_name_plural = u'特卖 供应商列表'


class SaleCategory(models.Model):

    name =   models.CharField(max_length=64,unique=True, blank=True,verbose_name=u'类别名')
    
    created    = models.DateTimeField(auto_now_add=True,verbose_name=u'创建日期')
    modified   = models.DateTimeField(auto_now=True,verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_grandsale_category'  
        verbose_name=u'特卖类目'
        verbose_name_plural = u'特卖类目列表'
        
        
class SaleProduct(models.Model):
    
    TIANMAO     = 'tianmao'
    ZHEBABAI     = 'zhe800'
    XIAOHER       = 'xiaoher'
    
    PLATFORM_CHOICE =  ((TIANMAO,u'天猫'),
                                                   (ZHEBABAI,u'折800'),
                                                   (XIAOHER,u'小荷特卖'),)
    
    outer_id  =  models.CharField(max_length=64, blank=True,verbose_name=u'识别码')
    title           =  models.CharField(max_length=64, blank=True,db_index=True,verbose_name=u'标题')
    price         =  models.FloatField(default=0,verbose_name=u'价格')
    pic_url      =  models.CharField(max_length=512,blank=True,verbose_name=u'商品图片')
    product_link      =  models.CharField(max_length=512,blank=True,verbose_name=u'商品外部链接')
    
    sale_supplier     = models.ForeignKey(SaleSupplier,null=True,related_name='suppliers',verbose_name=u'供货商')
    sale_category    = models.ForeignKey(SaleCategory,null=True,related_name='categories',verbose_name=u'类别')
    platform             = models.CharField(max_length=16,blank=True,
                                            choices=PLATFORM_CHOICE,verbose_name='来自平台')
    
    created    = models.DateTimeField(auto_now_add=True,verbose_name=u'创建日期')
    modified   = models.DateTimeField(auto_now=True,verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_grandsale_product'
        unique_together = ( "outer_id","platform")
        verbose_name=u'特卖商品'
        verbose_name_plural = u'特卖商品列表'
        


        
        
