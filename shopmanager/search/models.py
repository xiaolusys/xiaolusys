from shopback.base.fields import BigIntegerAutoField
from django.db import models

class ProductPageRank(models.Model):

    id = BigIntegerAutoField(primary_key=True)
    keyword = models.CharField(max_length=20)

    item_id = models.CharField(max_length=32)
    title = models.CharField(max_length=60)
    user_id = models.CharField(max_length=32)
    nick = models.CharField(max_length=20)

    search_datetime = models.DateTimeField()
    rank = models.IntegerField()

    class Meta:
        db_table = 'product_pagerank'