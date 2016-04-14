__author__ = 'meixqhi'
from django.db import models


class ProductPageRank(models.Model):
    id = models.AutoField(primary_key=True)

    keyword = models.CharField(max_length=20, db_index=True)

    item_id = models.CharField(max_length=32, db_index=True)
    title = models.CharField(max_length=60)
    user_id = models.CharField(max_length=32)
    nick = models.CharField(max_length=20, db_index=True)

    month = models.IntegerField(null=True, db_index=True)
    day = models.IntegerField(null=True, db_index=True)
    time = models.CharField(max_length=5, db_index=True)

    created = models.CharField(max_length=19, blank=True, db_index=True)
    rank = models.IntegerField()

    class Meta:
        db_table = 'shop_collector_pagerank'
        app_label = 'collector'


class ProductTrade(models.Model):
    id = models.AutoField(primary_key=True)

    item_id = models.CharField(max_length=32, db_index=True)
    user_id = models.CharField(max_length=32, db_index=True)

    nick = models.CharField(max_length=20, db_index=True)
    trade_id = models.CharField(max_length=20, db_index=True)
    num = models.IntegerField(null=True)
    price = models.CharField(blank=True, max_length=10)
    trade_at = models.CharField(max_length=19, blank=True, db_index=True)
    state = models.CharField(max_length=12, blank=True)

    year = models.IntegerField(null=True, db_index=True)
    month = models.IntegerField(null=True, db_index=True)
    week = models.IntegerField(null=True, db_index=True)
    day = models.IntegerField(null=True, db_index=True)
    hour = models.IntegerField(null=True, db_index=True)

    class Meta:
        db_table = 'shop_collector_producttrade'
        app_label = 'collector'
