from django.db import models
from shopback.base.fields import BigIntegerAutoField
from shopback.base.models import UNEXECUTE



class ItemNumTask(models.Model):

    id = BigIntegerAutoField(primary_key=True)

    outer_id = models.CharField(max_length=64)
    sku_outer_id = models.CharField(max_length=64,blank=True)

    num = models.IntegerField()

    created_at = models.DateTimeField(null=True,blank=True, auto_now_add=True)

    status = models.CharField(max_length=10,default=UNEXECUTE) #unexecute,execerror,success,delete

    class Meta:
        db_table = 'shop_syncnum_itemnumtask'



