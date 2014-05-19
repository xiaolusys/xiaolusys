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

logger = logging.getLogger('django.request')

USER_STATUS_CHOICES = (
    (pcfg.USER_NORMAL,u'正常'),
    (pcfg.USER_INACTIVE,u'未激活'),
    (pcfg.USER_DELETE,u'删除'),
    (pcfg.USER_FREEZE,u'冻结'),
    (pcfg.USER_SUPERVISE,u'监管'),
)

class EffectUserManager(models.Manager):
    def get_query_set(self):
        return super(EffectUserManager, self).get_query_set().filter(status=pcfg.USER_NORMAL)

class User(models.Model):

    id = BigIntegerAutoField(primary_key=True)
    user = models.ForeignKey(DjangoUser, null=True)
    
    top_session = models.CharField(max_length=128,blank=True)
    top_appkey = models.CharField(max_length=32,blank=True)
    top_parameters = models.TextField(max_length=2000,blank=True)

    visitor_id = models.CharField(max_length=64,blank=True,verbose_name=u'店铺ID')
    uid  = models.CharField(max_length=64,blank=True,verbose_name=u'用户ID')
    nick = models.CharField(max_length=64,blank=True,verbose_name=u'店铺名')
    user_code = models.CharField(max_length=16,blank=True,verbose_name=u'内部编码')
    
    sex = models.CharField(max_length=1,blank=True)
    contacter = models.CharField(max_length=32,blank=True,verbose_name= u'联络人')
    phone     = models.CharField(max_length=20,blank=True,verbose_name= u'电话')
    mobile    = models.CharField(max_length=20,blank=True,verbose_name= u'手机')
    area_code = models.CharField(max_length=10,blank=True,verbose_name= u'区号')
    
    buyer_credit = models.CharField(max_length=80,blank=True)
    seller_credit = models.CharField(max_length=80,blank=True)
    
    has_fenxiao = models.BooleanField(default=False,verbose_name= u'管理分销')
    
    location = models.CharField(max_length=256,blank=True,verbose_name= u'店铺地址')
    created = models.CharField(max_length=19,blank=True)
    birthday = models.CharField(max_length=19,blank=True)

    type = models.CharField(max_length=2,blank=True,verbose_name= u'店铺类型')
    item_img_num = models.IntegerField(default=0)
    item_img_size = models.IntegerField(default=0)

    prop_img_num = models.IntegerField(default=0)
    prop_img_size = models.IntegerField(default=0)
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
    
    sync_stock    = models.BooleanField(default=True,verbose_name= u'同步库存')
    percentage    = models.IntegerField(default=0,verbose_name= u'库存同步比例')
    is_primary    = models.BooleanField(default=False,verbose_name= u'主店铺')
    
    created_at = models.DateTimeField(auto_now=True,null=True) 
    status     = models.CharField(max_length=12,choices=USER_STATUS_CHOICES,blank=True) #normal(正常),inactive(未激活),delete(删除),reeze(冻结),supervise(监管)
    
    objects    = models.Manager()
    effect_users = EffectUserManager()
    
    class Meta:
        db_table = 'shop_users_user'
        verbose_name= u'店铺'
        verbose_name_plural = u'店铺列表'
        permissions = [
                       ("can_download_orderinfo", u"下载待发货订单"),
                       ("can_download_iteminfo", u"下载线上商品信息"),
                       ("can_manage_itemlist", u"管理商品上架时间"),
                       ("can_recover_instock", u"线上库存覆盖系统库存"),
                       ("can_async_threemtrade", u"异步下载近三月订单"),
                       ]
    
    def isValid(self):
        return self.status == pcfg.USER_NORMAL
    
    def __unicode__(self):
        return '%s'%self.nick
    
    @classmethod
    def getSellerByVisitorId(cls,visitor_id):
    
        try:
            return cls.objects.get(visitor_id=visitor_id)
        except cls.DoesNotExist:
            return None

    @property
    def stock_percent(self):
        #获取该店铺商品库存同步比例
        if self.percentage <= 0:
            return -1
        total_percent = User.objects.filter(status=pcfg.USER_NORMAL).aggregate(
                                        total_percent=models.Sum('percentage')).get('total_percent')
        if total_percent >0 and total_percent > self.percentage>0:
            return self.percentage/float(total_percent)
        elif total_percent >0 and 100>=self.percentage>0:
            return self.percetage
        elif self.percentage>=100:
            return 1
        else:
            return -1
            
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
    #对用户的主动通知进行授权
    profile.authorize_increment_notify()
    #初始化系统数据
    from shopback.users.tasks import initSystemDataFromAuthTask
    
    initSystemDataFromAuthTask.delay(profile.visitor_id)
    
    
taobao_logged_in.connect(add_taobao_user)
  
  
class Customer(models.Model):
    """ 会员信息表 """

    nick      = models.CharField(max_length=32,verbose_name='昵称')
    sex       = models.CharField(max_length=1,blank=True,verbose_name='性别')
    avatar    = models.CharField(max_length=32,blank=True,verbose_name='头像')
    
    credit_level     = models.IntegerField(default=0,verbose_name='信用等级')
    credit_score     = models.IntegerField(default=0,verbose_name='信用积分')
    credit_total_num = models.IntegerField(default=0,verbose_name='总评价数')
    credit_good_num  = models.IntegerField(default=0,verbose_name='好评数')
    
    name      = models.CharField(max_length=32,db_index=True,blank=True,verbose_name='收货人')
    zip       = models.CharField(max_length=10,blank=True,verbose_name='邮编')
    address   = models.CharField(max_length=128,blank=True,verbose_name='地址')
    city      = models.CharField(max_length=16,blank=True,verbose_name='城市')
    state     = models.CharField(max_length=16,blank=True,verbose_name='省')
    country   = models.CharField(max_length=16,blank=True,verbose_name='国家')
    district  = models.CharField(max_length=16,blank=True,verbose_name='地区')
    
    phone     = models.CharField(max_length=16,null=True,blank=True,verbose_name='电话')
    mobile    = models.CharField(max_length=12,null=True,blank=True,verbose_name='手机')
    
    created   = models.DateTimeField(db_index=True,null=True,blank=True,auto_now=True,verbose_name='创建日期')
    birthday  = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='生日')
    
    last_buy_time = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='最后购买日期')
    buy_times     = models.IntegerField(default=0,verbose_name='购买次数')
    avg_payment   = models.FloatField(default=0.0,verbose_name='均单金额')
    
    vip_info  = models.CharField(max_length=3,blank=True,verbose_name='VIP等级')
    email     = models.CharField(max_length=32,blank=True,verbose_name='邮箱')
    
    is_valid = models.BooleanField(default=True,verbose_name= u'有效')
    
    class Meta:
        db_table = 'shop_users_customer'
        unique_together = ("nick","mobile","phone")
        verbose_name= u'会员'
        verbose_name_plural = u'会员列表'

    def __unicode__(self):
        return '%s'%self.nick
    
    