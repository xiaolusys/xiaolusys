from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField

class Item(BaseModel):

    num_iid = models.CharField(primary_key=True,max_length=64)

    outer_iid = models.CharField(max_length=64,blank=True)
    num = models.IntegerField(null=True)

    seller_cids = models.CharField(max_length=126,blank=True)
    approve_status = models.CharField(max_length=20,blank=True)
    type = models.CharField(max_length=12,blank=True)
    valid_thru = models.IntegerField(null=True)

    cid = models.BigIntegerField(null=True)
    price = models.CharField(max_length=12,blank=True)
    postage_id = models.BigIntegerField(null=True)

    has_showcase = models.BooleanField(default=False)
    modified = models.CharField(max_length=19,blank=True)

    user_id = models.CharField(max_length=32,blank=True)
    nick = models.CharField(max_length=64,blank=True)
    list_time = models.CharField(max_length=19,blank=True)
    delist_time = models.CharField(max_length=19,blank=True)
    has_discount = models.BooleanField(default=False)

    props = models.CharField(max_length=200,blank=True)
    title = models.CharField(max_length=148,blank=True)

    has_invoice = models.BooleanField(default=False)
    pic_url = models.URLField(verify_exists=False)
    detail_url = models.URLField(verify_exists=False)

    desc = models.CharField(max_length=64)

    skus = models.CharField(max_length=1500,blank=True)

    class Meta:
        db_table = 'shop_item'


    def __unicode__(self):
        return self.num_iid+'---'+self.outer_iid+'---'+self.title