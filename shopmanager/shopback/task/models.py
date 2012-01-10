from django.db import models
import datetime
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField

class ItemTask(BaseModel):

    id = BigIntegerAutoField(primary_key=True)

    visitor_id = models.CharField(max_length=20)
    visitor_nick = models.CharField(max_length=32)
    session_key = models.CharField(max_length=32)

    num_iid = models.CharField(max_length=20)
    title = models.CharField(max_length=128)
    num = models.IntegerField()
    update_time = models.DateTimeField()
    created_at = models.DateTimeField(default=datetime.datetime.now)

    is_active = models.BooleanField(default=False)
    is_success = models.BooleanField(default=False)

    class Meta:
        db_table = 'shop_itemtask'



