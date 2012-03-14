from django.db import models

class Category(models.Model):

    cid        = models.IntegerField(primary_key=True)
    parent_cid = models.IntegerField(null=True,db_index=True)

    name       = models.CharField(max_length=32)
    is_parent  = models.BooleanField(default=True)
    status     = models.CharField(max_length=7)
    sort_order = models.IntegerField(null=True)

    class Meta:
        db_table = 'product_category'