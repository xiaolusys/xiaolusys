from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField

class Item(BaseModel):

    id = BigIntegerAutoField(primary_key=True)

    outer_iid = models.CharField(max_length=20,unique=True)
    num = models.IntegerField()
    numiid_session = models.CharField(max_length=1000) #num_iid:session_key

#    seller_cids = models.CharField(max_length=126)
#    approve_status = models.CharField(max_length=20)
#    type = models.CharField(max_length=12)
#    valid_thru = models.IntegerField()
#
#    cid = models.IntegerField()
#    price = models.CharField(max_length=10)
#    postage_id = models.IntegerField()
#
#    has_showcase = models.BooleanField()
#    modified = models.CharField(max_length=19)
#
#    nick = models.CharField(max_length=64)
#    list_time = models.CharField(max_length=19)
#    delist_time = models.CharField(max_length=19)
#    has_discount = models.BooleanField()
#
#    props = models.CharField(max_length=200)
#    title = models.CharField(max_length=148)
#
#    has_invoice = models.BooleanField()
#    pic_url = models.CharField(max_length=128)

    class Meta:
        db_table = 'shop_item'