from django.db import models
from shopback.base.fields import BigIntegerAutoField

class ItemListTask(models.Model):
    num_iid = models.CharField(primary_key=True,max_length=64)

    user_id = models.CharField(max_length=32)
    nick = models.CharField(max_length=32)

    title = models.CharField(max_length=128)
    num = models.IntegerField()

    list_weekday = models.IntegerField()
    list_time = models.CharField(max_length=8)

    task_type = models.CharField(max_length=10,blank=True)      #listing, delisting

    created_at = models.DateTimeField(null=True,blank=True, auto_now_add=True)

    status = models.CharField(max_length=10,default='unexecute') #unexecute,execerror,success,delete

    class Meta:
        db_table = 'shop_itemlisttask'





class ItemNumTask(models.Model):

    id = BigIntegerAutoField(primary_key=True)

    outer_iid = models.CharField(max_length=64)
    sku_outer_id = models.CharField(max_length=64,blank=True)

    num = models.IntegerField()

    created_at = models.DateTimeField(null=True,blank=True, auto_now_add=True)

    status = models.CharField(max_length=10,default='unexecute') #unexecute,execerror,success,delete

    class Meta:
        db_table = 'shop_itemnumtask'



