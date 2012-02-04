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
    #created_at = models.DateTimeField()
    detail_url = models.URLField(verify_exists=False)
    pic_url = models.URLField(verify_exists=False)

