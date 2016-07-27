# encoding=utf8
from django.db import models
from .base import BaseModel
from flashsale.pay.models.user import Customer
from flashsale.pay.models.product import ModelProduct


class Favorites(BaseModel):
    customer = models.ForeignKey(Customer)
    model = models.ForeignKey(ModelProduct)

    class Meta:
        db_table = 'flashsale_favorites'
        app_label = 'pay'

