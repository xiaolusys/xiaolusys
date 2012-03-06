from shopback.base.fields import BigIntegerAutoField
from django.db import models

class ProductPageRank(models.Model):

    id = BigIntegerAutoField(primary_key=True)
    keyword = models.CharField(max_length=20,db_index=True)

    item_id = models.CharField(max_length=32,db_index=True)
    title = models.CharField(max_length=60)
    user_id = models.CharField(max_length=32)
    nick = models.CharField(max_length=20,db_index=True)

    month = models.IntegerField(null=True,db_index=True)
    day = models.IntegerField(null=True,db_index=True)
    time = models.CharField(max_length=5,db_index=True)

    created = models.CharField(max_length=19,blank=True,db_index=True)
    rank = models.IntegerField()

    class Meta:
        db_table = 'product_pagerank'

