# encoding=utf8
from django.db import models
from .base import BaseModel
from flashsale.pay.models.user import Customer


class Checkin(BaseModel):
    customer = models.ForeignKey(Customer)

    class Meta:
        db_table = 'flashsale_checkin'
        app_label = 'pay'
