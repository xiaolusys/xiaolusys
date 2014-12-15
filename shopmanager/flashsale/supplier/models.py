#-*- coding:utf8 -*-
from django.db import models


class SaleSupplier(models.Model):
    
    supplier_name =   models.CharField(max_length=64,unique=True,blank=True,verbose_name=u'店铺名称')
    supplier_code   =   models.CharField(max_length=64, blank=True,verbose_name=u'品牌缩写')
    
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
        db_table = 'shop_flashsale_supplier'
        verbose_name=u'特卖 供应商'
        verbose_name_plural = u'特卖 供应商列表'
        
    def __unicode__(self):
        return self.supplier_name


class SaleCategory(models.Model):

    name =   models.CharField(max_length=64,unique=True, blank=True,verbose_name=u'类别名')
    
    created    = models.DateTimeField(auto_now_add=True,verbose_name=u'创建日期')
    modified   = models.DateTimeField(auto_now=True,verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_flashsale_category'  
        verbose_name=u'特卖类目'
        verbose_name_plural = u'特卖类目列表'
        
    def __unicode__(self):
        return self.name
        
        
class SaleProduct(models.Model):
    
    TAOBAO        = 'taobao'
    TMALL           = 'tianmao'
    ZHEBABAI     = 'zhe800'
    XIAOHER       = 'xiaoher'
    
    PLATFORM_CHOICE =  ((TAOBAO,u'淘宝'),
                        (TMALL,u'天猫'),
                        (ZHEBABAI,u'折800'),
                        (XIAOHER,u'小荷特卖'),)
    WAIT = 'wait'
    SELECTED = 'selected'
    PURCHASE = 'passed'
    IGNORED  = 'ignored'
    REJECTED = 'rejected'
    STATUS_CHOICES = ((WAIT,u'待选'),
                      (SELECTED,u'初选'),
                      (PURCHASE,u'通过'),
                      (REJECTED,u'淘汰'),
                      (IGNORED,u'忽略'),)

    outer_id  =  models.CharField(max_length=64, blank=True,verbose_name=u'外部ID')
    title     =  models.CharField(max_length=64, blank=True,db_index=True,verbose_name=u'标题')
    price     =  models.FloatField(default=0,verbose_name=u'价格')
    pic_url   =  models.CharField(max_length=512,blank=True,verbose_name=u'商品图片')
    product_link =  models.CharField(max_length=512,blank=True,verbose_name=u'商品外部链接')
    
    sale_supplier = models.ForeignKey(SaleSupplier,null=True,related_name='suppliers',verbose_name=u'供货商')
    sale_category = models.ForeignKey(SaleCategory,null=True,related_name='categories',verbose_name=u'类别')
    platform      = models.CharField(max_length=16,blank=True,
                                     choices=PLATFORM_CHOICE,verbose_name=u'来自平台')
    
    hot_value   = models.IntegerField(default=0,verbose_name=u'热度值')
    sale_price   = models.FloatField(default=0,verbose_name=u'采购价')
    memo         = models.CharField(max_length=1024,blank=True,verbose_name=u'备注')
    
    status          = models.CharField(max_length=16,blank=True,
                                            choices=STATUS_CHOICES,default=WAIT,verbose_name=u'状态')
    
    created  = models.DateTimeField(auto_now_add=True,verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True,verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_flashsale_product'
        unique_together = ( "outer_id","platform")
        verbose_name=u'特卖商品'
        verbose_name_plural = u'特卖商品列表'
        
    def __unicode__(self):
        return self.title
        


        
        
