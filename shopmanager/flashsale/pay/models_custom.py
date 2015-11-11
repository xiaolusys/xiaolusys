#-*- coding:utf-8 -*-
from django.db import models
from shopback.items.models import Product,ProductSku

class Productdetail(models.Model):
    WASH_INSTRUCTION = '''洗涤时请深色、浅色衣物分开洗涤。最高洗涤温度不要超过40度，不可漂白。有涂层、印花表面不能进行熨烫，会导致表面剥落。不可干洗，悬挂晾干。'''
    OUT_PERCENT  = 0 #未设置代理返利比例
    ZERO_PERCENT = -1
    TEN_PERCENT  = 10
    TWENTY_PERCENT = 20
    THIRTY_PERCENT = 30

    REBETA_CHOICES = ((OUT_PERCENT,u'未设置返利'),
                     (ZERO_PERCENT,u'该商品不返利'),
                     (TEN_PERCENT,u'返利百分之10'),
                     (TWENTY_PERCENT,u'返利百分之20'),
                     (THIRTY_PERCENT,u'返利百分之30'),)
    
    product  = models.OneToOneField(Product, primary_key=True,
                                    related_name='details',verbose_name=u'库存商品')
    
    head_imgs  = models.TextField(blank=True,verbose_name=u'题头照(多张请换行)')
    content_imgs = models.TextField(blank=True,verbose_name=u'内容照(多张请换行)')
    
    mama_discount  = models.IntegerField(default=100,verbose_name=u'妈妈折扣')
    is_recommend = models.BooleanField(db_index=True,verbose_name=u'专区推荐')
    is_seckill   = models.BooleanField(db_index=True,default=False, verbose_name=u'是否秒杀')
    buy_limit    = models.BooleanField(db_index=True,default=False,verbose_name=u'是否限购')
    per_limit    = models.IntegerField(default=5,verbose_name=u'限购数量')

    material = models.CharField(max_length=64, blank=True, verbose_name=u'商品材质')
    color    = models.CharField(max_length=64, blank=True, verbose_name=u'可选颜色')
    wash_instructions = models.TextField(default=WASH_INSTRUCTION, blank=True, verbose_name=u'洗涤说明')
    note = models.CharField(max_length=256, blank=True, verbose_name=u'备注')
    mama_rebeta = models.IntegerField(default=OUT_PERCENT, choices=REBETA_CHOICES,
                                      db_index=True, verbose_name=u'代理返利')

    class Meta:
        db_table = 'flashsale_productdetail'
        verbose_name=u'特卖商品/详情'
        verbose_name_plural = u'特卖商品/详情列表'
    
    def __unicode__(self):
        return '<%s,%s>'%(self.product.outer_id,self.product.name)
    
    def mama_rebeta_rate(self):
        if self.mama_rebeta == self.ZERO_PERCENT:
            return 0.0
        if self.mama_rebeta == self.OUT_PERCENT:
            return None
        rate = self.mama_rebeta / 100.0
        assert rate >= 0 and rate <=1
        return rate 
    
    
class ModelProduct(models.Model):
    
    NORMAL = '0'
    DELETE = '1'
    
    STATUS_CHOICES = ((NORMAL,u'正常'),
                      (DELETE,u'作废'))
    
    name       = models.CharField(max_length=64,db_index=True,verbose_name=u'款式名称')
    
    head_imgs  = models.TextField(blank=True,verbose_name=u'题头照(多张请换行)')
    
    content_imgs = models.TextField(blank=True,verbose_name=u'内容照(多张请换行)')
    
    buy_limit    = models.BooleanField(default=False,verbose_name=u'是否限购')
    per_limit    = models.IntegerField(default=5,verbose_name=u'限购数量')
    
    sale_time    = models.DateField(null=True,blank=True,db_index=True,verbose_name=u'上架日期')
    
    created      = models.DateTimeField(auto_now_add=True,verbose_name=u'创建时间')
    modified     = models.DateTimeField(auto_now=True,verbose_name=u'修改时间')
    
    status       = models.CharField(max_length=16,db_index=True,
                                    choices=STATUS_CHOICES,
                                    default=NORMAL,verbose_name=u'状态')
    
    class Meta:
        db_table = 'flashsale_modelproduct'
        unique_together = ("id", "name")
        verbose_name=u'特卖商品/款式'
        verbose_name_plural = u'特卖商品/款式列表'
     
    def __unicode__(self):
        return '<%s,%s>'%(self.id,self.name)
    
    def is_single_spec(self):
        if self.id <= 0:
            return True
        products = Product.objects.filter(model_id=self.id,status=Product.NORMAL)
        if products.count() > 1:
            return False
        return True
    
from shopback.base.models import JSONCharMyField

POSTER_DEFAULT =(
'''
[
  {
    "subject":["2折起","Joan&David  女装专场"],
    "item_link":"商品链接",
    "pic_link":"海报图片"
  }
]
''')

class GoodShelf(models.Model):
    
    title = models.CharField(max_length=32,db_index=True,blank=True, verbose_name=u'海报说明')
    
    wem_posters   = JSONCharMyField(max_length=10240, blank=True, 
                                    default=POSTER_DEFAULT, 
                                    verbose_name=u'女装海报')
    chd_posters   = JSONCharMyField(max_length=10240, blank=True, 
                                    default=POSTER_DEFAULT,
                                    verbose_name=u'童装海报')
    
    is_active    = models.BooleanField(default=True,verbose_name=u'上线')
    active_time  = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'上线日期')
    
    created      = models.DateTimeField(null=True,auto_now_add=True,db_index=True,blank=True,verbose_name=u'生成日期')
    modified     = models.DateTimeField(null=True,auto_now=True,blank=True,verbose_name=u'修改日期')
    
    class Meta:
        db_table = 'flashsale_goodshelf'
        verbose_name=u'特卖商品/海报'
        verbose_name_plural = u'特卖商品/海报列表'
    
    def __unicode__(self):
        return u'<海报：%s>'%(self.title)
    

