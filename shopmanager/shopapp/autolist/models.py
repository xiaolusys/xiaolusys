from django.db import models
from shopback.base.models import UNEXECUTE



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

    status = models.CharField(max_length=10,default=UNEXECUTE) #unexecute,execerror,success,delete

    class Meta:
        db_table = 'shop_app_itemlisttask'



class Logs(models.Model):
    num_iid = models.CharField(max_length=64)
    cat_id = models.CharField(max_length=64)
    cat_name = models.CharField(max_length=64)
    outer_id = models.CharField(max_length=64)
    title = models.CharField(max_length=128)
    pic_url = models.URLField(verify_exists=False)

    list_weekday = models.IntegerField()
    list_time = models.CharField(max_length=8)
    num = models.IntegerField()

    task_type = models.CharField(max_length=10,blank=True)
    execute_time = models.DateTimeField(null=True,blank=True, auto_now_add=True)

    status = models.CharField(max_length=20) #unexec

    class Meta:
        db_table = 'shop_app_autolist_logs'
