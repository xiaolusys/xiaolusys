from django.db import models

# Create your models here.
class ProductItem(models.Model):
    num_iid = models.CharField(primary_key=True,max_length=64)
    category_id = models.CharField(max_length=64)
    category_name = models.CharField(max_length=64)
    ref_code  = models.CharField(max_length=64)
    desc = models.CharField(max_length=64)
    title = models.CharField(max_length=60)
    list_time = models.DateTimeField()
    modified = models.DateTimeField()
    detail_url = models.URLField(verify_exists=False)
    pic_url = models.URLField(verify_exists=False)
    num = models.IntegerField()

class Logs(models.Model):
    num_iid = models.CharField(max_length=64)
    cat_id = models.CharField(max_length=64)
    cat_name = models.CharField(max_length=64)
    ref_code = models.CharField(max_length=64)
    title = models.CharField(max_length=128)
    pic_url = models.URLField(verify_exists=False)

    list_weekday = models.IntegerField()
    list_time = models.CharField(max_length=8)
    num = models.IntegerField()

    task_type = models.CharField(max_length=10,blank=True)
    execute_time = models.DateTimeField(null=True,blank=True, auto_now_add=True)

    status = models.CharField(max_length=20) #unexec
