# encoding=utf8
from django.db import models
from .base import BaseModel
from flashsale.pay.models.user import Customer
from flashsale.pay.models.product import ModelProduct


class Favorites(BaseModel):
    customer = models.ForeignKey(Customer)
    model = models.ForeignKey(ModelProduct)
    name = models.CharField(max_length=64, db_index=True, verbose_name=u'款式名称')
    head_img = models.TextField(blank=True, verbose_name=u'题头照')
    lowest_agent_price = models.FloatField(default=0, verbose_name=u'出售价')
    lowest_std_sale_price = models.FloatField(default=0, verbose_name=u'吊牌价')

    class Meta:
        db_table = 'flashsale_favorites'
        app_label = 'pay'
