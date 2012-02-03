from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField

class Item(BaseModel):

    id = BigIntegerAutoField(primary_key=True)

    outer_iid = models.CharField(max_length=20,unique=True)

    num = models.IntegerField()
    numiid_session = models.CharField(max_length=1000) #num_iid:session_key

    class Meta:
        db_table = 'shop_item'