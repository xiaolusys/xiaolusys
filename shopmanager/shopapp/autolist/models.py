from django.db import models
from shopback.base.models import UNEXECUTE



class TimeSlots(models.Model):
    timeslot = models.IntegerField(primary_key=True)

    def hour(self):
        return timeslot / 100

    def minute(self):
        return timeslot % 100


class ItemListTask(models.Model):
    num_iid = models.CharField(primary_key=True,max_length=64)

    list_weekday = models.IntegerField()
    list_time = models.CharField(max_length=8)

    task_type = models.CharField(max_length=10,blank=True)      #listing, delisting
    created_at = models.DateTimeField(null=True,blank=True, auto_now_add=True)

    status = models.CharField(max_length=10,default=UNEXECUTE) #unexecute,execerror,success,delete

    class Meta:
        db_table = 'shop_autolist_itemlisttask'



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
        db_table = 'shop_autolist_logs'
