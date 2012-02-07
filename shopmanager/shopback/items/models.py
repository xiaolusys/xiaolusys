from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField

class Item(BaseModel):

    num_iid = models.CharField(primary_key=True,max_length=64)

    outer_iid = models.CharField(max_length=64,blank=True)
    num = models.IntegerField()

    seller_cids = models.CharField(max_length=126,blank=True)
    approve_status = models.CharField(max_length=20,blank=True)
    type = models.CharField(max_length=12,blank=True)
    valid_thru = models.IntegerField()

    cid = models.BigIntegerField()
    price = models.CharField(max_length=12,blank=True)
    postage_id = models.BigIntegerField()

    has_showcase = models.BooleanField()
    modified = models.CharField(max_length=19,blank=True)

    user_id = models.CharField(max_length=32,blank=True)
    nick = models.CharField(max_length=64,blank=True)
    list_time = models.CharField(max_length=19,blank=True)
    delist_time = models.CharField(max_length=19,blank=True)
    has_discount = models.BooleanField()

    props = models.CharField(max_length=200,blank=True)
    title = models.CharField(max_length=148,blank=True)

    has_invoice = models.BooleanField()
    pic_url = models.URLField(verify_exists=False)
    detail_url = models.URLField(verify_exists=False)

    desc = models.CharField(max_length=64)

    skus = models.CharField(max_length=1500,blank=True)

    class Meta:
        db_table = 'shop_item'