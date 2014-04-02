#-*- coding:utf-8 -*-
import datetime
from django.db import models
from shopback.base.fields import BigIntegerAutoField
from jsonfield import JSONCharField

SAFE_CODE_SECONDS = 60
WX_TEXT  = 'text'
WX_IMAGE = 'image'
WX_VOICE = 'voice'
WX_VIDEO = 'video'
WX_THUMB = 'thumb'
WX_MUSIC = 'music'
WX_NEWS  = 'news'
WX_LOCATION = 'location'
WX_LINK  = 'link'  
WX_DEFAULT = 'DEFAULT'
WX_EVENT   = 'event'

WX_EVENT_SUBSCRIBE   = 'subscribe'
WX_EVENT_UNSUBSCRIBE = 'unsubscribe'
WX_EVENT_SCAN        = 'SCAN'
WX_EVENT_LOCATION    = 'LOCATION'
WX_EVENT_CLICK       = 'CLICK'
WX_EVENT_VIEW        = 'VIEW'

MEN      = 'm'
FERMALE  = 'f'

WX_TYPE  = (
            (WX_TEXT ,u'文本'),
            (WX_IMAGE,u'图片'),
            (WX_VOICE,u'语音'),
            (WX_VIDEO,u'视频'),
            (WX_THUMB,u'缩略图'),
            (WX_MUSIC,u'音乐'),
            (WX_NEWS ,u'图文'),
            )

BABY_SEX_TYPE = (
                 (MEN,u'男'),
                 (FERMALE,u'女')
                 )

class AnonymousWeixinAccount():
    
    def isNone(self):
        return True
    
    def checkSignature(self,signature,timestamp,nonce):
        return False
    
    def isExpired(self):
        return True

class WeiXinAccount(models.Model):
    
    token      = models.CharField(max_length=32,verbose_name=u'TOKEN')    
    
    app_id     = models.CharField(max_length=64,verbose_name=u'应用ID')
    app_secret = models.CharField(max_length=128,verbose_name=u'应用SECRET')
    
    access_token = models.CharField(max_length=256,blank=True,verbose_name=u'ACCESS TOKEN')
    
    expires_in = models.BigIntegerField(default=0,verbose_name="使用期限(s)")
    expired    = models.DateTimeField(default=datetime.datetime.now(),verbose_name="上次过期时间")
    
    jmenu     =  JSONCharField(max_length=1024,blank=True,load_kwargs={},verbose_name=u'菜单代码') 
    
    in_voice   = models.BooleanField(default=False,verbose_name=u'开启语音')
    is_active  = models.BooleanField(default=False,verbose_name=u'激活')
    
    
    class Meta:
        db_table = 'shop_weixin_account'
        verbose_name=u'微信帐号'
        verbose_name_plural = u'微信帐号列表'
        
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
    
    openid     = models.CharField(max_length=64,unique=True,verbose_name=u"用户ID")
    nickname   = models.CharField(max_length=64,blank=True,unique=True,verbose_name=u"昵称")
    
    sex        = models.IntegerField(default=0,verbose_name=u"性别")
    language   = models.CharField(max_length=10,blank=True,verbose_name=u"语言")
    
    headimgurl = models.URLField(verify_exists=False,blank=True,verbose_name=u"头像")
    country    = models.CharField(max_length=24,blank=True,verbose_name=u"国家")
    province   = models.CharField(max_length=24,blank=True,verbose_name=u"省份")
    city       = models.CharField(max_length=24,blank=True,verbose_name=u"城市")
    address    = models.CharField(max_length=256,blank=True,verbose_name=u"地址")
    mobile     = models.CharField(max_length=24,blank=True,verbose_name=u"手机")
    
    baby_nick   = models.CharField(max_length=64,blank=True,verbose_name=u"宝宝昵称")
    baby_birth  = models.DateTimeField(blank=True,null=True,verbose_name=u"宝宝生日")
    baby_sex    = models.CharField(max_length=1,blank=True,choices=BABY_SEX_TYPE,verbose_name=u"宝宝性别")
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
    
    def isNone(self):
        return False
    
    def isValid(self):
        return self.isvalid
    
    def get_wait_time(self):
        
        delta_seconds =int((datetime.datetime.now() - self.code_time).total_seconds())
        
        return delta_seconds < 60 and  (60 - delta_seconds) or 0
    
    def is_code_time_safe(self):
        
        if not self.code_time:
            return True
        
        return (datetime.datetime.now() - self.code_time).total_seconds() > SAFE_CODE_SECONDS

    def doSubscribe(self,sceneid):
        self.sceneid   = sceneid
        self.subscribe = True
        self.subscribe_time = datetime.datetime.now()
        self.save()
        
    def unSubscribe(self):
        self.subscribe = False
        self.save()


class WeiXinAutoResponse(models.Model):
    
    message   = models.CharField(max_length=64,unique=True,verbose_name=u"消息")
    
    rtype     = models.CharField(max_length=8,choices=WX_TYPE,default=WX_TEXT,verbose_name=u"类型")
    
    media_id  = models.CharField(max_length=1024,blank=True,verbose_name=u'媒体ID')
    
    title     = models.CharField(max_length=512,blank=True,verbose_name=u'标题')
    content   = models.CharField(max_length=1024,blank=True,verbose_name=u'回复信息')
    
    music_url = models.CharField(max_length=512,blank=True,verbose_name=u'音乐链接')
    hq_music_url = models.CharField(max_length=512,blank=True,verbose_name=u'高品质音乐链接')
    
    news_json = JSONCharField(max_length=1024,blank=True,load_kwargs={},verbose_name=u'图文信息')
    
    class Meta:
        db_table = 'shop_weixin_response'
        verbose_name=u'微信回复'
        verbose_name_plural = u'微信回复列表'
        
    
    @classmethod
    def respDefault(cls):
        resp,state = cls.objects.get_or_create(message=WX_DEFAULT,rtype=WX_TEXT)
        return resp
    
    def respText(self):
        return {'MsgType':self.rtype,
                'Content':self.content}
    
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
                         'Description':self.content
                         }}
    
    def respMusic(self):
        
        return {'MsgType':self.rtype,
                'Music':{'Title':self.title,
                         'Description':self.content,
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
        
        if   self.rtype == WX_TEXT:
            return self.respText()
        elif self.rtype == WX_IMAGE:
            return self.respImage()
        elif self.rtype == WX_VOICE:
            return self.respVoice()
        elif self.rtype == WX_VIDEO:
            return self.respVideo()
        elif self.rtype == WX_MUSIC:
            return self.respMusic()
        else:
            return self.respNews()
        
            