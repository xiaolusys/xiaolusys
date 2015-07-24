
from django.db import models

class ProductRebeta(models.Model):
    
    NORMAL = 1
    CANCEL = 0
    STATUS_CHOICES = ((CANCEL,u'已取消'),
                   (NORMAL,u'已生效'))
    
    product_id = models.BigIntegerField(db_index=True, verbose_name=u'商品ID')
    
    rebeta_point  = models.IntegerField(null=True, db_index=True, verbose_name=u'返利点')
    
    active_start = models.DateTimeField(null=True, db_index=True,verbose_name=u'开始时间')
    active_end   = models.DateTimeField(null=True, db_index=True,verbose_name=u'结束时间')
    
    created    = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified   = models.DateTimeField(auto_now=True, db_index=True, verbose_name=u'修改时间')
    
    status     = models.IntegerField(choice=STATUS_CHOICES,default=NORMAL,verbose_name=u'状态')
    
    class Meta:
        db_table = 'xiaolumm_productrebeta'
        verbose_name    = u'特卖商品返利'
        verbose_name_plural = u'特卖商品返利列表'

    def __unicode__(self):
        return u'<ProductRebeta:%s,%d>'%(self.product_id,self.rebeta_point)
    
    def rebeta_rate(self):
        rate = self.rebeta_point / 100.0
        if rate > 1:
            return 1
        if rate < 0:
            return 0
        return rate
        
        
        