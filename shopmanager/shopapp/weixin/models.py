#-*- coding:utf-8 -*-
import datetime
from django.db import models
from shopback.base.fields import BigIntegerAutoField
from shopback.base.models import JSONCharMyField
from .managers import WeixinProductManager


SAFE_CODE_SECONDS = 60

class AnonymousWeixinAccount():
    
    def isNone(self):
        return True
    
    def isExpired(self):
        return True


class WeiXinAccount(models.Model):
    
    account_id = models.CharField(max_length=32,unique=True,
                                  verbose_name=u'OPEN ID')
    
    token      = models.CharField(max_length=32,verbose_name=u'TOKEN')    
    
    app_id     = models.CharField(max_length=64,verbose_name=u'应用ID')
    app_secret = models.CharField(max_length=128,verbose_name=u'应用SECRET')
    
    pay_sign_key = models.CharField(max_length=128,verbose_name=u'支付密钥')
    partner_id   = models.CharField(max_length=32,verbose_name=u'商户ID')
    partner_key  = models.CharField(max_length=128,verbose_name=u'商户KEY')
    
    access_token = models.CharField(max_length=256,blank=True,
                                    verbose_name=u'ACCESS TOKEN')
    
    expires_in = models.BigIntegerField(default=0,verbose_name="使用期限(s)")
    expired    = models.DateTimeField(default=datetime.datetime.now(),
                                      verbose_name="上次过期时间")
    
    jmenu     =  JSONCharMyField(max_length=1024,blank=True,
                               load_kwargs={},default='{}',
                               verbose_name=u'菜单代码') 
    
    in_voice   = models.BooleanField(default=False,verbose_name=u'开启语音')
    is_active  = models.BooleanField(default=False,verbose_name=u'激活')
    
    order_updated  = models.DateTimeField(blank=True,null=True,
                                          verbose_name="订单更新时间")
    refund_updated = models.DateTimeField(blank=True,null=True,
                                          verbose_name="维权更新时间")
    
    class Meta:
        db_table = 'shop_weixin_account'
        verbose_name=u'微信服务帐号'
        verbose_name_plural = u'微信服务帐号列表'
        
    
    def __unicode__(self):
        return u'<WeiXinAccount:%s,%s>'%(self.account_id,self.app_id)
        
    
    @classmethod
    def getAccountInstance(cls):
        try:
            return  cls.objects.get()
        except:
            return AnonymousWeixinAccount()
    
    def isNone(self):
        return False
    
    def isExpired(self):
        return datetime.datetime.now() > self.expired \
            + datetime.timedelta(seconds=self.expires_in)
    
    def activeAccount(self):
        self.is_active = True
        self.save()
        
    def changeOrderUpdated(self,updated):
        self.order_updated = updated
        self.save()
        
    def changeRefundUpdated(self,updated):
        self.refund_updated = updated
        self.save()
        
        
class AnonymousWeixinUser():
    
    def isNone(self):
        return True
    
    def isValid(self):
        return False
    
    def get_wait_time(self):
        return SAFE_CODE_SECONDS
    
    def is_code_time_safe(self):
        return False
    
    
class WeiXinUser(models.Model): 
    
    MEN      = 'm'
    FERMALE  = 'f'
    
    BABY_SEX_TYPE = (
        (MEN,u'男'),
        (FERMALE,u'女')
    )
    
    openid     = models.CharField(max_length=64,unique=True,verbose_name=u"用户ID")
    nickname   = models.CharField(max_length=64,blank=True,verbose_name=u"昵称")
    
    sex        = models.IntegerField(default=0,verbose_name=u"性别")
    language   = models.CharField(max_length=10,blank=True,verbose_name=u"语言")
    
    headimgurl = models.URLField(verify_exists=False,blank=True,verbose_name=u"头像")
    country    = models.CharField(max_length=24,blank=True,verbose_name=u"国家")
    province   = models.CharField(max_length=24,blank=True,verbose_name=u"省份")
    city       = models.CharField(max_length=24,blank=True,verbose_name=u"城市")
    address    = models.CharField(max_length=256,blank=True,verbose_name=u"地址")
    mobile     = models.CharField(max_length=24,blank=True,verbose_name=u"手机")
    referal_from_openid = models.CharField(max_length=64,blank=True,verbose_name=u"推荐人ID")
    
    receiver_name   = models.CharField(max_length=64,blank=True,verbose_name=u"收货人")
    birth_year  = models.IntegerField(default=0,verbose_name=u"出生年")
    birth_month  = models.IntegerField(default=0,verbose_name=u"出生月")
    baby_sex    = models.CharField(max_length=1,
                                   blank=True,
                                   choices=BABY_SEX_TYPE,
                                   verbose_name=u"宝宝性别")
    baby_topic  = models.CharField(max_length=256,blank=True,verbose_name=u"宝宝签名")
    
    isvalid    = models.BooleanField(default=False,verbose_name=u"已验证")
    validcode     = models.CharField(max_length=6,blank=True,verbose_name=u"验证码")
    
    valid_count  = models.IntegerField(default=0,verbose_name=u'验证次数')
    code_time    = models.DateTimeField(blank=True,null=True,verbose_name=u'短信发送时间')    
    
    sceneid    = models.CharField(max_length=32,blank=True,verbose_name=u'场景ID')
    
    subscribe   = models.BooleanField(default=False,verbose_name=u"订阅该号")
    subscribe_time = models.DateTimeField(blank=True,null=True,verbose_name=u"订阅时间")
    
    class Meta:
        db_table = 'shop_weixin_user'
        verbose_name=u'微信用户'
        verbose_name_plural = u'微信用户列表'
    
    @classmethod
    def getAnonymousWeixinUser(cls):
        return AnonymousWeixinUser()
    
    def __unicode__(self):
        return u'<WeiXinUser:%s,%s>'%(self.openid,self.nickname)
    
    def isNone(self):
        return False
    
    def isValid(self):
        return self.isvalid
    
    def get_wait_time(self):
        
        delta_seconds =int((datetime.datetime.now() -
                             self.code_time).total_seconds())
        
        return delta_seconds < 60 and  (60 - delta_seconds) or 0
    
    def is_code_time_safe(self):
        
        if not self.code_time:
            return True
        
        return ((datetime.datetime.now() - 
                 self.code_time).total_seconds() 
                > SAFE_CODE_SECONDS)

    def doSubscribe(self,sceneid):
        self.sceneid   = sceneid
        self.subscribe = True
        self.subscribe_time = datetime.datetime.now()
        self.save()
        
    def unSubscribe(self):
        self.subscribe = False
        self.save()


class WeiXinAutoResponse(models.Model):
    
    WX_TEXT  = 'text'
    WX_IMAGE = 'image'
    WX_VOICE = 'voice'
    WX_VIDEO = 'video'
    WX_THUMB = 'thumb'
    WX_MUSIC = 'music'
    WX_NEWS  = 'news'
    WX_LOCATION = 'location'
    WX_LINK     = 'link'  
    WX_DEFAULT  = 'DEFAULT'
    WX_EVENT    = 'event'
    
    WX_EVENT_SUBSCRIBE   = 'subscribe'
    WX_EVENT_UNSUBSCRIBE = 'unsubscribe'
    WX_EVENT_SCAN        = 'SCAN'
    WX_EVENT_LOCATION    = 'LOCATION'
    WX_EVENT_CLICK       = 'CLICK'
    WX_EVENT_VIEW        = 'VIEW'
    WX_EVENT_ORDER       = 'merchant_order'
    
    WX_TYPE  = (
        (WX_TEXT ,u'文本'),
        (WX_IMAGE,u'图片'),
        (WX_VOICE,u'语音'),
        (WX_VIDEO,u'视频'),
        (WX_THUMB,u'缩略图'),
        (WX_MUSIC,u'音乐'),
        (WX_NEWS ,u'新闻'),
    )
    
    message   = models.CharField(max_length=64,unique=True,verbose_name=u"消息")
    
    rtype     = models.CharField(max_length=8,choices=WX_TYPE,default=WX_TEXT,verbose_name=u"类型")
    
    media_id  = models.CharField(max_length=1024,blank=True,verbose_name=u'媒体ID')
    
    title     = models.CharField(max_length=512,blank=True,verbose_name=u'标题')
    content   = models.CharField(max_length=1024,blank=True,verbose_name=u'回复信息')
    
    music_url = models.CharField(max_length=512,blank=True,verbose_name=u'音乐链接')
    hq_music_url = models.CharField(max_length=512,blank=True,verbose_name=u'高品质音乐链接')
    
    news_json = JSONCharMyField(max_length=1024,blank=True,
                              load_kwargs={},default='{}',
                              verbose_name=u'图文信息')
    
    class Meta:
        db_table = 'shop_weixin_response'
        verbose_name=u'微信回复'
        verbose_name_plural = u'微信回复列表'
        
    @classmethod
    def respDefault(cls):
        resp,state = cls.objects.get_or_create(message=cls.WX_DEFAULT,
                                               rtype=cls.WX_TEXT)
        return resp
    
    def __unicode__(self):
        return u'<WeiXinAutoResponse:%d,%s>'%(self.id,
                                              self.get_rtype_display())
    
    def respText(self):
        self.content = self.content.replace('\r','')
        return {'MsgType':self.rtype,
                'Content':self.content.replace('\r','')}
    
    def respImage(self):
        
        return {'MsgType':self.rtype,
                'Image':{'MediaId':self.media_id
                         }}
        
    def respVoice(self):
        
        return {'MsgType':self.rtype,
                'Voice':{'MediaId':self.media_id
                         }}
        
    def respVideo(self):
        
        return {'MsgType':self.rtype,
                'Video':{'MediaId':self.media_id,
                         'Title':self.title,
                         'Description':self.content.replace('\r','')
                         }}
    
    def respMusic(self):
        
        return {'MsgType':self.rtype,
                'Music':{'Title':self.title,
                         'Description':self.content.replace('\r',''),
                         'ThumbMediaId':self.media_id,
                         'MusicURL':self.music_url,
                         'HQMusicUrl':self.hq_music_url
                         }}
        
    def respNews(self):
        news  = self.news_json
        return {'MsgType':self.rtype,
                'ArticleCount':len(news),
                'Articles':{'item':news}}
        
    def autoParams(self):
        
        if   self.rtype == self.WX_TEXT:
            return self.respText()
        elif self.rtype == self.WX_IMAGE:
            return self.respImage()
        elif self.rtype == self.WX_VOICE:
            return self.respVoice()
        elif self.rtype == self.WX_VIDEO:
            return self.respVideo()
        elif self.rtype == self.WX_MUSIC:
            return self.respMusic()
        else:
            return self.respNews()
        

class WXProduct(models.Model):
    
    UP_SHELF   = 1
    DOWN_SHELF = 2
    
    PRODUCT_STATUS = (
        (UP_SHELF,u'下架'),
        (DOWN_SHELF,u'上架')
    )
    
    product_id   = models.CharField(max_length=32,
                                    primary_key=True,
                                    verbose_name=u'商品ID')
    
    product_name = models.CharField(max_length=64,verbose_name=u'商品标题')
    product_img  = models.CharField(max_length=512,verbose_name=u'商品图片')
    
    product_base = JSONCharMyField(max_length=3000,blank=True,
                                 load_kwargs={},default='{}'
                                 ,verbose_name=u'图文信息')
    
    sku_list     = JSONCharMyField(max_length=3000,blank=True,
                                 load_kwargs={},default='{}'
                                 ,verbose_name=u'规格信息') 
    
    attrext      = JSONCharMyField(max_length=1000,blank=True,
                                 load_kwargs={},default='{}'
                                 ,verbose_name=u'附加信息') 
    
    delivery_info   = JSONCharMyField(max_length=200,blank=True,
                                    load_kwargs={},default='{}'
                                    ,verbose_name=u'发货信息') 
    
    status       = models.IntegerField(null=False,default=0,
                                       choices=PRODUCT_STATUS,
                                       verbose_name=u'是否上架')
    
    objects = WeixinProductManager()
    
    class Meta:
        db_table = 'shop_weixin_product'
        verbose_name=u'微信小店商品'
        verbose_name_plural = u'微信小店商品列表'

    def __unicode__(self):
        return u'<WXProduct:%s>'%(self.product_id)
       
class WXOrder(models.Model):
    
    WX_WAIT_SEND = 2
    WX_WAIT_CONFIRM = 3
    WX_FINISHED  = 5
    WX_CLOSE     = 6
    WX_FEEDBACK  = 8
    
    WXORDER_STATUS = (
        (WX_WAIT_SEND,u'待发货'),
        (WX_WAIT_CONFIRM,u'待确认收货'),
        (WX_FINISHED,u'已完成'),
        (WX_CLOSE,u'已关闭'),
        (WX_FEEDBACK,u'维权中')
    )
    
    order_id  = models.CharField(max_length=32,primary_key=True,verbose_name=u'订单ID')
    
    trans_id  = models.CharField(max_length=32,blank=True,verbose_name=u'交易ID')
    seller_id = models.CharField(max_length=32,db_index=True,verbose_name=u'商家ID')
    
    buyer_openid = models.CharField(max_length=64,blank=True,verbose_name=u'买家OPENID')
    buyer_nick   = models.CharField(max_length=32,blank=True,verbose_name=u'买家昵称')
    
    order_total_price   = models.FloatField(default=0,verbose_name=u'订单总价')
    order_express_price = models.FloatField(default=0,verbose_name=u'订单运费')
    order_create_time   = models.DateTimeField(blank=True,null=True,
                                               verbose_name=u'创建时间')
    order_status = models.CharField(max_length=10,blank=True,
                                    choices=WXORDER_STATUS,
                                    verbose_name=u'订单状态')
    
    receiver_name     = models.CharField(max_length=64,blank=True,verbose_name=u'收货人')
    receiver_province = models.CharField(max_length=24,blank=True,verbose_name=u'省')
    receiver_city     = models.CharField(max_length=24,blank=True,verbose_name=u'市')
    receiver_address  = models.CharField(max_length=128,blank=True,verbose_name=u'地址')
    receiver_mobile   = models.CharField(max_length=24,blank=True,verbose_name=u'手机')
    receiver_phone    = models.CharField(max_length=24,blank=True,verbose_name=u'电话')
    
    product_id     = models.CharField(max_length=64,blank=True,verbose_name=u'商品ID')
    product_name   = models.CharField(max_length=64,blank=True,verbose_name=u'商品名')
    product_price  = models.FloatField(default=0,verbose_name=u'商品价格')
    product_sku    = models.CharField(max_length=128,blank=True,verbose_name=u'商品SKU')
    product_count  = models.IntegerField(default=0,verbose_name=u'商品个数')
    product_img    = models.CharField(max_length=512,blank=True,verbose_name=u'商品图片')
    
    delivery_id    = models.CharField(max_length=32,blank=True,verbose_name=u'运单ID')
    delivery_company  = models.CharField(max_length=16,blank=True,verbose_name=u'物流公司编码')
    
    class Meta:
        db_table = 'shop_weixin_order'
        verbose_name=u'微信小店订单'
        verbose_name_plural = u'微信小店订单列表'
    
    def __unicode__(self):
        return u'<WXOrder:%s,%s>'%(self.order_id,self.buyer_nick)
    
    @classmethod
    def mapTradeStatus(cls,wx_order_status):
        
        from shopback import paramconfig as pcfg
        if wx_order_status == cls.WX_WAIT_SEND:
            return pcfg.WAIT_SELLER_SEND_GOODS
        
        elif wx_order_status == cls.WX_WAIT_CONFIRM:
            return pcfg.WAIT_BUYER_CONFIRM_GOODS
        
        elif wx_order_status == cls.WX_FINISHED:
            return pcfg.TRADE_FINISHED
        
        elif wx_order_status == cls.WX_CLOSE:
            return pcfg.TRADE_CLOSED
        
        elif wx_order_status == cls.WX_FEEDBACK:
            return pcfg.WAIT_BUYER_CONFIRM_GOODS

        return pcfg.WAIT_BUYER_PAY
    
    @classmethod
    def mapOrderStatus(cls,wx_order_status):
        
        from shopback import paramconfig as pcfg
        if wx_order_status == cls.WX_WAIT_SEND:
            return pcfg.WAIT_SELLER_SEND_GOODS
        
        elif wx_order_status == cls.WX_WAIT_CONFIRM:
            return pcfg.WAIT_BUYER_CONFIRM_GOODS
        
        elif wx_order_status == cls.WX_FINISHED:
            return pcfg.TRADE_FINISHED
        
        elif wx_order_status == cls.WX_CLOSE:
            return pcfg.TRADE_CLOSED
        
        elif wx_order_status == cls.WX_FEEDBACK:
            return pcfg.TRADE_REFUNDING

        return pcfg.WAIT_BUYER_PAY
    

class WXLogistic(models.Model):
    company_name = models.CharField(max_length=16,blank=True,verbose_name=u'快递名称')
    origin_code  = models.CharField(max_length=16,blank=True,verbose_name=u'原始编码')      
    company_code = models.CharField(max_length=16,blank=True,verbose_name=u'快递编码')    
    
    class Meta:
        db_table = 'shop_weixin_logistic'
        verbose_name=u'微信小店快递'
        verbose_name_plural = u'微信小店快递列表'   
    

class ReferalRelationship(models.Model):
    """ 保存待确定的推荐关系 """
    referal_from_openid = models.CharField(max_length=64,db_index=True,verbose_name=u"推荐人ID")
    referal_to_mobile   = models.CharField(max_length=12,db_index=True,verbose_name=u"被推荐人手机")
    time_created = models.DateTimeField(default=datetime.datetime.now(), verbose_name="time created")

    class Meta:
        db_table = 'shop_weixin_referal_relationship'


class ReferalBonusRecord(models.Model):
    user_openid = models.CharField(max_length=64,db_index=True,verbose_name=u"ID")
    from_referal_user = models.IntegerField() # IntegerField?
    order_id = models.CharField(max_length=32)
    bonus_value = models.IntegerField() # cent
    confirmed_status = models.IntegerField() # 0 unconfirmed, 1 confirmed, 2 cancelled
    
    class Meta:
        db_table = 'shop_wexin_referal_bonus_record'


class BonusCashoutRecord(models.Model):
    user_openid = models.CharField(max_length=64,db_index=True,verbose_name=u"ID")
    cashout_value = models.IntegerField()
    cashout_time = models.DateTimeField(default=datetime.datetime.now(), verbose_name="cashout time")

    class Meta:
        db_table = 'shop_weixin_bonus_cashout_record'


class ReferalSummary(models.Model):
    user_openid = models.CharField(max_length=64,db_index=True,unique=True,verbose_name=u"ID")
    total_confirmed_value = models.IntegerField(default=0)
    cashed_value = models.IntegerField(default=0)
    #uncashed_value = total_confirmed_value - cashed_value
    
    direct_referal_count = models.IntegerField(default=0)
    indirect_referal_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'shop_weixin_referal_summary'



