from shopback.base.fields import BigIntegerAutoField
from django.db import models



class MonthTradeReportStatus(models.Model):

    seller_id   = models.CharField(max_length=64,blank=True)

    year  = models.IntegerField(null=True)
    month = models.IntegerField(null=True)

    update_order    = models.BooleanField(default=False)
    update_purchase = models.BooleanField(default=False)
    update_amount   = models.BooleanField(default=False)
    update_logistics  = models.BooleanField(default=False)
    update_refund   = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shop_app_monthreportstatus'
        unique_together = ("seller_id","year","month")