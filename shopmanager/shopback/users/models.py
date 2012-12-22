#-*- coding:utf8 -*-
import time
import json
import datetime
from django.db import models
from shopback.base.models import BaseModel
from django.contrib.auth.models import User as DjangoUser
from shopback.signals import taobao_logged_in
from shopback.base.fields import BigIntegerAutoField
from shopback import paramconfig as pcfg
from auth import apis
import logging

logger = logging.getLogger('user.handler')

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
    
    has_fenxiao = models.BooleanField(default=False)
    
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

    item_notify_updated   = models.DateTimeField(null=True,blank=True)
    refund_notify_updated = models.DateTimeField(null=True,blank=True)
    trade_notify_updated  = models.DateTimeField(null=True,blank=True)

    craw_keywords = models.TextField(blank=True)
    craw_trade_seller_nicks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now=True,null=True) 
    status     = models.CharField(max_length=12,blank=True) #normal,inactive,delete,reeze,supervise

    class Meta:
        db_table = 'shop_users_user'
        verbose_name= u'店铺'

    def __unicode__(self):
        return self.nick


    def populate_user_info(self,top_session,top_parameters):
        """docstring for populate_user_info"""
        response = apis.taobao_user_seller_get(tb_user_id=top_parameters['taobao_user_id'])

        userdict = response['user_seller_get_response']['user']
        userdict['seller_credit'] = json.dumps(userdict['seller_credit'])
        userdict.pop('user_id',None)
        for key, value in userdict.iteritems():
             hasattr(self, key) and  setattr(self, key, value)

        self.top_session = top_session
        top_parameters['ts'] = time.time()
        self.top_parameters = json.dumps(top_parameters)

        self.save()
        
    def verify_fenxiao_user(self):
        from auth.apis.exceptions import UserFenxiaoUnuseException,InsufficientIsvPermissionsException
        try:
            apis.taobao_fenxiao_login_user_get(tb_user_id=self.visitor_id)
        except (UserFenxiaoUnuseException,InsufficientIsvPermissionsException):
            self.has_fenxiao = False
        else:
            self.has_fenxiao = True
        self.save()
        return self.has_fenxiao

    def authorize_increment_notify(self):
        #对用户的主动通知授权
        try:
            response = apis.taobao_increment_customer_permit(type='get,syn,notify',topics='trade;refund;item',
                                                status='all;all;ItemAdd,ItemUpdate',tb_user_id=self.visitor_id)
        except Exception,exc:
            logger.error('主动消息服务授权失败'.decode('utf8'),exc_info=True)
        else:                
            logger.warn('主动消息服务授权成功'.decode('utf8'),exc_info=True)
            created = datetime.datetime.now()-datetime.timedelta(0,15,0)
            self.item_notify_updated=created
            self.trade_notify_updated=created
            self.refund_notify_updated=created
            self.save()
            
def add_taobao_user(sender, user,top_session,top_parameters, *args, **kwargs):
    """docstring for user_logged_in"""
    profile = user.get_profile()
    profile.populate_user_info(top_session,top_parameters)
    
    profile.verify_fenxiao_user()
    #更新用户淘宝商品，以及分销平台商品
    from shopback.items.tasks import updateUserItemSkuFenxiaoProductTask
    
    updateUserItemSkuFenxiaoProductTask.delay(profile.visitor_id)
    
    #对用户的主动通知进行授权
    profile.authorize_increment_notify()
    
    #更新等待发货商城订单
    from shopback.orders.tasks import saveUserDuringOrdersTask

    saveUserDuringOrdersTask.delay(profile.visitor_id,status=pcfg.WAIT_SELLER_SEND_GOODS)
    
    #更新待发货分销订单
    from shopback.fenxiao.tasks import saveUserPurchaseOrderTask
    
    saveUserPurchaseOrderTask.delay(profile.visitor_id,status=pcfg.WAIT_SELLER_SEND_GOODS)
    
taobao_logged_in.connect(add_taobao_user)
  
