import time
import json
from django.db import models
from shopback.base.models import BaseModel
from django.contrib.auth.models import User as DjangoUser
from shopback.users.signals import taobao_logged_in
from shopback.base.fields import BigIntegerAutoField
from auth import apis


class User(models.Model):

    id = BigIntegerAutoField(primary_key=True)
    user = models.ForeignKey(DjangoUser, null=True)

    top_session = models.CharField(max_length=56,blank=True)
    top_appkey = models.CharField(max_length=24,blank=True)
    top_parameters = models.TextField(max_length=1000,blank=True)

    visitor_id = models.CharField(max_length=32,blank=True)
    uid = models.CharField(max_length=32,blank=True)
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
    alipay_no   = models.CharField(max_length=20,blank=True)

    update_items_datetime = models.DateTimeField(null=True,blank=True)

    craw_keywords = models.TextField(blank=True)
    craw_trade_seller_nicks = models.TextField(blank=True)


    created_at = models.DateTimeField(auto_now=True,null=True)
    status     = models.CharField(max_length=12,blank=True) #normal,inactive,delete,reeze,supervise

    class Meta:
        db_table = 'shop_user'


    def __unicode__(self):
        return self.visitor_id+'-'+self.nick


    def populate_user_info(self,top_session,top_parameters):
        """docstring for populate_user_info"""
        response = apis.taobao_user_get(tb_user_id=top_parameters['taobao_user_id'])

        userdict = response['user_get_response']['user']
        userdict['buyer_credit'] = json.dumps(userdict['buyer_credit'])
        userdict['seller_credit'] = json.dumps(userdict['seller_credit'])
        userdict['location'] = json.dumps(userdict['location'])
        userdict.pop('user_id',None)
        for key, value in userdict.iteritems():
             hasattr(self, key) and  setattr(self, key, value)

        self.top_session = top_session
        top_parameters['ts'] = time.time()
        self.top_parameters = json.dumps(top_parameters)

        self.save()



def add_taobao_user(sender, user,top_session,top_parameters, *args, **kwargs):
    """docstring for user_logged_in"""
    profile = user.get_profile()
    profile.populate_user_info(top_session,top_parameters)

taobao_logged_in.connect(add_taobao_user)
  