#-*- coding:utf8 -*-
from django.db import models
from core.models import BaseModel
from django.contrib.auth.models import User
from shopback.base.models import JSONCharMyField

class XLFreeSample(BaseModel):
    """ 试用商品 """
    outer_id = models.CharField(max_length=64,blank=True,verbose_name=u'商品编码')
    name     = models.CharField(max_length=64,blank=True,verbose_name=u'活动名称')
    expiried = models.DateTimeField(null=False,blank=False,verbose_name=u'过期时间')
    
    pic_url  = models.URLField(verify_exists=False,blank=True,verbose_name='商品图片')
    sale_url = models.URLField(verify_exists=False,blank=True,verbose_name='销售链接')

    class Meta:
        db_table = 'flashsale_promotion_freesample'
        verbose_name = u'推广/试用商品'
        verbose_name_plural = u'推广/试用商品列表'

    def __unicode__(self):
        return self.name


class XLSampleSku(BaseModel):
    """ 试用商品规格 """ 
    sample_product = models.ForeignKey(XLFreeSample, verbose_name=u'试用商品', related_name="skus")
    sku_code = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'SKU编码')
    sku_name = models.CharField(max_length=64,blank=True,verbose_name=u'款式尺寸')

    class Meta:
        db_table = 'flashsale_promotion_samplesku'
        verbose_name = u'推广/试用商品SKU'
        verbose_name_plural = u'推广/试用商品SKU列表'

    def __unicode__(self):
        return '-'.join([str(self.sample_product), self.sku_name])


class XLSampleApply(BaseModel):
    """ 试用申请 """
    INACTIVE = 0
    ACTIVED  = 1
    STATUS_CHOICES = (
        (INACTIVE, u'未激活'),
        (ACTIVED, u'已激活'),
    )
    FROM_WXAPP = 'wxapp'
    FROM_PYQ  = 'pyq'
    FROM_QQ   = 'qq'
    FROM_WB   = 'txwb'
    FROM_WEB  = 'web'

    FROM_CHOICES = (
        (FROM_WXAPP,u'微信好友'),
        (FROM_PYQ,u'朋友圈'),
        (FROM_QQ,u'QQ'),
        (FROM_WB,u'腾讯微博'),
        (FROM_WEB,u'外部网页'),
    )
    
    outer_id = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'商品编码')
    sku_code = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'SKU编码')
    
    ufrom    = models.CharField(max_length=8,choices=FROM_CHOICES,blank=True,verbose_name=u'来自平台')
    user_openid  = models.CharField(max_length=28,db_index=True,blank=True,verbose_name=u'用户openid')
    mobile   = models.CharField(max_length=11,null=False,db_index=True,blank=False,verbose_name=u'试用手机')
    vipcode  = models.CharField(max_length=16,null=False,db_index=True,blank=False,verbose_name=u'试用邀请码')
    status   = models.IntegerField(default=INACTIVE,choices=STATUS_CHOICES,db_index=True, verbose_name=u"状态")
    
    class Meta:
        db_table = 'flashsale_promotion_sampleapply'
        verbose_name = u'推广/试用申请'
        verbose_name_plural = u'推广/试用申请列表'


class XLSampleOrder(BaseModel):
    """ 正式试用订单 """
    
    customer_id = models.CharField(max_length=64,db_index=True,verbose_name=u"用户ID")
    outer_id = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'商品编码')
    sku_code = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'SKU编码')
    vipcode  = models.CharField(max_length=16,null=False,db_index=True,blank=False,verbose_name=u'试用邀请码')
    problem_score = models.IntegerField(default=0, verbose_name=u"答题分数")
    status = models.IntegerField(default=0,db_index=True, verbose_name=u"状态")
    
    class Meta:
        db_table = 'flashsale_promotion_sampleorder'
        verbose_name = u'推广/试用订单'
        verbose_name_plural = u'推广/试用订单列表'
        
        
