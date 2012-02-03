from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField

class Order(models.Model):

    id = BigIntegerAutoField(primary_key=True)

    oid = models.CharField(max_length=20,unique=True)
    status = models.CharField(max_length=30,null=True)

    title =  models.CharField(max_length=128)
    price = models.CharField(max_length=10)
    num_iid = models.IntegerField(null=True)

    item_meal_id = models.IntegerField(null=True)
    sku_id = models.CharField(max_length=20,null=True)
    num = models.IntegerField(null=True)

    outer_sku_id = models.CharField(max_length=20,null=True)
    total_fee = models.CharField(max_length=10,null=True)

    payment = models.CharField(max_length=10,null=True)
    discount_fee = models.CharField(max_length=10,null=True)
    adjust_fee = models.CharField(max_length=10,null=True)

    modified = models.CharField(max_length=19,null=True)
    sku_properties_name = models.CharField(max_length=88,null=True)
    refund_id = models.IntegerField(null=True)

    is_oversold = models.BooleanField()
    is_service_order = models.BooleanField()

    item_meal_name = models.CharField(max_length=88,null=True)
    pic_path = models.CharField(max_length=128,null=True)

    seller_nick = models.CharField(max_length=32,null=True)
    buyer_nick = models.CharField(max_length=32,null=True)

    refund_status = models.CharField(max_length=40,null=True)

    outer_iid = models.CharField(max_length=48,null=True)
    snapshot_url = models.CharField(max_length=128,null=True)
    snapshot = models.CharField(max_length=356,null=True)

    timeout_action_time = models.CharField(max_length=19,null=True)
    buyer_rate = models.BooleanField(default=False)
    seller_rate = models.BooleanField(default=False)
    seller_type = models.CharField(max_length=2,null=True)

    cid = models.BigIntegerField(null=True)

    class Meta:
        db_table = 'shop_order'
  