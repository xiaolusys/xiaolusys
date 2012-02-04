from django.db import models
from shopback.base.models import BaseModel
from django.contrib.auth.models import User
from shopback.base.fields import BigIntegerAutoField


class User(models.Model):

    id = BigIntegerAutoField(primary_key=True)
    user = models.ForeignKey(User, null=True)

    top_session = models.CharField(max_length=56,blank=True)
    top_appkey = models.CharField(max_length=24,blank=True)
    top_parameters = models.CharField(max_length=256,blank=True)

    user_id = models.IntegerField(null=True)
    uid = models.CharField(max_length=10,blank=True)
    nick = models.CharField(max_length=32,blank=True)
    sex = models.CharField(max_length=1,blank=True)
    buyer_credit = models.CharField(max_length=80,blank=True)
    seller_credit = models.CharField(max_length=80,blank=True)
    location = models.CharField(max_length=256,blank=True)
    created = models.CharField(max_length=19,blank=True)
    birthday = models.CharField(max_length=19,blank=True)
    type = models.CharField(max_length=2,blank=True)
    item_img_num = models.IntegerField(null=True)
    item_img_size = models.IntegerField(null=True)

    prop_img_num = models.IntegerField(null=True)
    prop_img_size = models.IntegerField(null=True)
    auto_repost = models.CharField(max_length=16,blank=True)
    promoted_type = models.CharField(max_length=32,blank=True)

    alipay_bind = models.CharField(max_length=10,blank=True)

    alipay_account = models.CharField(max_length=48,blank=True)
    alipay_no = models.CharField(max_length=20,blank=True)

    status = models.CharField(max_length=12,blank=True) #normal(正常),inactive(未激活),delete(删除),reeze(冻结),supervise(监管)

    class Meta:
        db_table = 'shop_user'
  