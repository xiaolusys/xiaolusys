from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField

class ItemListTask(BaseModel):

    id = BigIntegerAutoField(primary_key=True)

    user_id = models.CharField(max_length=32)
    nick = models.CharField(max_length=32)

    num_iid = models.CharField(max_length=64)
    title = models.CharField(max_length=128)
    num = models.IntegerField()
    update_time = models.DateTimeField()
    task_type = models.IntegerField()       #0 update listing,1 del listing

    created_at = models.DateTimeField(null=True,blank=True, auto_now_add=True)

    is_success = models.BooleanField(default=False)

    class Meta:
        db_table = 'shop_itemlisttask'

class ItemNumTask(models.Model):

    id = BigIntegerAutoField(primary_key=True)

    outer_iid = models.CharField(max_length=64)
    sku_outer_id = models.CharField(max_length=64,blank=True)

    num = models.IntegerField()

    created_at = models.DateTimeField(null=True,blank=True, auto_now_add=True)

    status = models.CharField(max_length=10) #unexcute,excerror,success,delete

    class Meta:
        db_table = 'shop_itemnumtask'



