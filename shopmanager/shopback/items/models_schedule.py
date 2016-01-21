#encoding:utf-8 
import datetime
import time
from django.db import models
from core.models import AdminModel


class ProductSchedule(AdminModel):
    """ 商品排期管理 """
    ORIGIN_SCHEDULE = 'origin'
    SECKILL_SCHEDULE = 'seckill'
    SCHEDULE_CHOICES = (
        (ORIGIN_SCHEDULE,u'原始排期'),
        (SECKILL_SCHEDULE,u'秒杀排期'),
    )
    
    DEFAULT_TIME = 1000
    SALE_TIME_CHOICES = tuple([(m*100 ,'%02d:00'%m) for m in xrange(8,23)])
    
    sale_date = models.DateField(default=datetime.date.today ,db_index=True, verbose_name=u'排期日期')
    sale_time = models.IntegerField(choices=SALE_TIME_CHOICES, default=DEFAULT_TIME, db_index=True, verbose_name=u'排期时间')
    schedule_type = models.CharField(max_length=64, choices=SCHEDULE_CHOICES,
                                     db_index=True, verbose_name=u'排期类型')
    
    product_id   = models.IntegerField(default=0, db_index=True, verbose_name=u'商品ID')
    product_name = models.CharField(max_length=64,  verbose_name=u'产品名称')
    outer_id     = models.CharField(max_length=32, db_index=True, verbose_name=u'商品编码')
    
    operator_id   = models.BigIntegerField(default=0, db_index=True, verbose_name=u'负责人ID')
    operator_name = models.CharField(max_length=64, verbose_name=u'负责人名字')

    class Meta:
        db_table = 'shop_items_schedule'
        verbose_name = u'商品上下架排期管理'
        verbose_name_plural = u'商品上下架排期管理列表'

    def __unicode__(self):
        return ''