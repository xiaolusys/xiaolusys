from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField


class Order(models.Model):

    oid = models.CharField(primary_key=True,max_length=20)

    title =  models.CharField(max_length=128)
    price = models.CharField(max_length=12,blank=True)
    num_iid = models.BigIntegerField(null=True)

    item_meal_id = models.IntegerField(null=True)
    sku_id = models.CharField(max_length=20,blank=True)
    num = models.IntegerField(null=True)

    outer_sku_id = models.CharField(max_length=20,blank=True)
    total_fee = models.CharField(max_length=12,blank=True)

    payment = models.CharField(max_length=12,blank=True)
    discount_fee = models.CharField(max_length=12,blank=True)
    adjust_fee = models.CharField(max_length=12,blank=True)

    modified = models.CharField(max_length=19,blank=True)
    sku_properties_name = models.CharField(max_length=88,blank=True)
    refund_id = models.BigIntegerField(null=True)

    is_oversold = models.BooleanField()
    is_service_order = models.BooleanField()

    item_meal_name = models.CharField(max_length=88,blank=True)
    pic_path = models.CharField(max_length=128,blank=True)

    seller_nick = models.CharField(max_length=32,blank=True)
    buyer_nick = models.CharField(max_length=32,blank=True)

    refund_status = models.CharField(max_length=40,blank=True)

    outer_iid = models.CharField(max_length=64,blank=True)
    snapshot_url = models.CharField(max_length=128,blank=True)
    snapshot = models.CharField(max_length=356,blank=True)

    timeout_action_time = models.CharField(max_length=19,blank=True)
    buyer_rate = models.BooleanField(default=False)
    seller_rate = models.BooleanField(default=False)
    seller_type = models.CharField(max_length=2,blank=True)

    cid = models.BigIntegerField(null=True)

    status = models.CharField(max_length=30,blank=True)
    class Meta:
        db_table = 'shop_order'
  