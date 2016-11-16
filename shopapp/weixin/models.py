# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_save

from core import managers
from core.models import CacheModel
from core.fields import JSONCharMyField
from .managers import VipCodeManager, WeixinUserManager

from shopback.trades.models import MergeTrade
from .models_base import WeixinUnionID,WeixinUserInfo
from shopback.trades.models import PackageOrder
from .models_base import WeixinUnionID, WeixinFans
from .models_sale import WXProduct,WXSkuProperty,WXProductSku,WXOrder,WXLogistic

MIAOSHA_SELLER_ID = 'wxmiaosha'
SAFE_CODE_SECONDS = 180
TOKEN_EXPIRED_IN = 15 * 60


def get_Unionid(openid, appid):
    try:
        wxunion = WeixinUnionID.objects.get(openid=openid, app_key=appid)
        return wxunion.unionid
    except WeixinUnionID.DoesNotExist:
        return None


class AnonymousWeixinAccount():
    def isNone(self):
        return True

    def isExpired(self):
        return True


class WeiXinAccount(models.Model):
    account_id = models.CharField(max_length=32, unique=True,
                                  verbose_name=u'OPEN ID')

    token = models.CharField(max_length=32, verbose_name=u'TOKEN')

    app_id = models.CharField(max_length=64, verbose_name=u'应用ID')
    app_secret = models.CharField(max_length=128, verbose_name=u'应用SECRET')

    pay_sign_key = models.CharField(max_length=128, verbose_name=u'支付密钥')
    partner_id = models.CharField(max_length=32, verbose_name=u'商户ID')
    partner_key = models.CharField(max_length=128, verbose_name=u'商户KEY')

    access_token = models.CharField(max_length=256, blank=True,
                                    verbose_name=u'ACCESS TOKEN')

    js_ticket = models.CharField(max_length=256, blank=True, verbose_name=u'JSAPI_TICKET')

    expires_in = models.BigIntegerField(default=0, verbose_name=u"使用期限(s)")
    expired = models.DateTimeField(default=timezone.now,
                                   verbose_name=u"上次过期时间")

    js_expired = models.DateTimeField(default=timezone.now,
                                      verbose_name=u"TICKET上次过期时间")

    jmenu = JSONCharMyField(max_length=4096, blank=True, default={}, verbose_name=u'菜单代码')

    in_voice = models.BooleanField(default=False, verbose_name=u'开启语音')
    is_active = models.BooleanField(default=False, verbose_name=u'激活')

    order_updated = models.DateTimeField(blank=True, null=True,
                                         verbose_name=u"订单更新时间")
    refund_updated = models.DateTimeField(blank=True, null=True,
                                          verbose_name=u"维权更新时间")

    class Meta:
        db_table = 'shop_weixin_account'
        app_label = 'weixin'
        verbose_name = u'微信服务帐号'
        verbose_name_plural = u'微信服务帐号列表'

    def __unicode__(self):
        return u'<WeiXinAccount:%s,%s>' % (self.account_id, self.app_id)

    @classmethod
    def getAccountInstance(cls):
        try:
            return cls.objects.get()
        except:
            return AnonymousWeixinAccount()

    @classmethod
    def gen_account_list_cache_key(cls):
        return '%s.%s.list_cache_key'%(__file__, cls.__name__)

    @classmethod
    def getWeixinAccountValueList(cls):
        list_cache_key = cls.gen_account_list_cache_key()
        cache_value = cache.get(list_cache_key)
        if not cache_value:
            cache_value = WeiXinAccount.objects.all().values(
                'account_id', 'token', 'app_id', 'app_secret', 'access_token', 'js_ticket')
            cache.set(list_cache_key, cache_value, 24 * 3600)

        return cache_value

    @classmethod
    def getAnonymousAccount(self):
        return AnonymousWeixinAccount()

    def isNone(self):
        return False

    def isExpired(self):

        if not self.expired:
            return True
        return datetime.datetime.now() > self.expired + datetime.timedelta(seconds=TOKEN_EXPIRED_IN)

    def isJSTicketExpired(self):

        if not self.js_expired:
            return True
        return datetime.datetime.now() > self.js_expired + datetime.timedelta(seconds=TOKEN_EXPIRED_IN)

    def activeAccount(self):
        self.is_active = True
        self.save()

    def changeOrderUpdated(self, updated):
        self.order_updated = updated
        self.save(update_fields=['order_updated'])

    def changeRefundUpdated(self, updated):
        self.refund_updated = updated
        self.save(update_fields=['refund_updated'])

    def isResponseToDRF(self):
        return self.app_id in (settings.WXPAY_APPID,)


def invalid_wxaccount_cache_value(sender, instance, created, **kwargs):
    """ invalid wxaccount cache value  """
    cache_key = WeiXinAccount.gen_account_list_cache_key()
    cache.delete(cache_key)

post_save.connect(invalid_wxaccount_cache_value, sender=WeiXinAccount,
                   dispatch_uid='post_save_invalid_wxaccount_cache_value')



class UserGroup(models.Model):
    code = models.CharField(max_length=32, blank=True, verbose_name=u"组代码")
    name = models.CharField(max_length=32, blank=True, verbose_name=u"组名")

    class Meta:
        db_table = 'shop_weixin_group'
        app_label = 'weixin'
        verbose_name = u'用户分组'
        verbose_name_plural = u'用户分组列表'

    def __unicode__(self):
        return self.name


class AnonymousWeixinUser():
    def isNone(self):
        return True

    def isValid(self):
        return False

    def get_wait_time(self):
        return SAFE_CODE_SECONDS

    def is_code_time_safe(self):
        return False


class WeiXinUser(CacheModel):
    MAX_MOBILE_VALID_COUNT = 3

    MEN = 'm'
    FERMALE = 'f'

    SEX_TYPE = (
        (1, u'男'),
        (2, u'女')
    )

    BABY_SEX_TYPE = (
        (MEN, u'男'),
        (FERMALE, u'女')
    )

    CHARGED = 'charged'
    UNCHARGE = 'uncharge'
    FROZEN = 'frozen'
    STATUS_CHOICES = (
        (UNCHARGE, u'待接管'),
        (CHARGED, u'已接管'),
        (FROZEN, u'已冻结'),
    )

    openid = models.CharField(max_length=64, unique=True, verbose_name=u"用户ID")
    nickname = models.CharField(max_length=64, blank=True, verbose_name=u"昵称")
    unionid = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u"UnionID")
    sex = models.IntegerField(default=0, choices=SEX_TYPE, verbose_name=u"性别")
    language = models.CharField(max_length=10, blank=True, verbose_name=u"语言")

    headimgurl = models.URLField(blank=True, verbose_name=u"头像")
    country = models.CharField(max_length=24, blank=True, verbose_name=u"国家")
    province = models.CharField(max_length=24, blank=True, verbose_name=u"省份")
    city = models.CharField(max_length=24, blank=True, verbose_name=u"城市")
    address = models.CharField(max_length=256, blank=True, verbose_name=u"地址")
    mobile = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u"手机")
    referal_from_openid = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u"推荐人ID")

    receiver_name = models.CharField(max_length=64, blank=True, verbose_name=u"收货人")
    birth_year = models.IntegerField(default=0, verbose_name=u"出生年")
    birth_month = models.IntegerField(default=0, verbose_name=u"出生月")
    baby_sex = models.CharField(max_length=1, blank=True,
                                choices=BABY_SEX_TYPE,
                                verbose_name=u"宝宝性别")
    baby_topic = models.CharField(max_length=256, blank=True, verbose_name=u"宝宝签名")

    vmobile = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u"待验证手机")
    isvalid = models.BooleanField(default=False, verbose_name=u"已验证")
    validcode = models.CharField(max_length=6, blank=True, verbose_name=u"验证码")

    valid_count = models.IntegerField(default=0, verbose_name=u'验证次数')
    code_time = models.DateTimeField(blank=True, null=True, verbose_name=u'短信发送时间')

    sceneid = models.CharField(max_length=32, blank=True, verbose_name=u'场景ID')

    user_group = models.ForeignKey(UserGroup, null=True, blank=True, verbose_name=u"分组")

    subscribe = models.BooleanField(default=False, verbose_name=u"订阅该号")
    subscribe_time = models.DateTimeField(blank=True, null=True, verbose_name=u"订阅时间")

    referal_count = models.IntegerField(default=0, verbose_name=u'F码次数')
    charge_status = models.CharField(max_length=16, blank=True, db_index=True,
                                     choices=STATUS_CHOICES,
                                     default=UNCHARGE, verbose_name=u'接管状态')

    objects = WeixinUserManager()

    class Meta:
        db_table = 'shop_weixin_user'
        app_label = 'weixin'
        verbose_name = u'微信用户'
        verbose_name_plural = u'微信用户列表'

    @classmethod
    def getAnonymousWeixinUser(cls):
        return AnonymousWeixinUser()

    def __unicode__(self):
        return u'<WeiXinUser:%s,%s>' % (self.openid, self.nickname)

    def isNone(self):
        return False

    def isValid(self):
        if not self.mobile and self.isvalid:
            self.isvalid = False
            self.save()
            return False

        return self.isvalid

    def get_wait_time(self):

        delta_seconds = int((datetime.datetime.now() -
                             self.code_time).total_seconds())

        return delta_seconds < SAFE_CODE_SECONDS and (SAFE_CODE_SECONDS - delta_seconds) or 0

    def is_valid_count_safe(self):
        return self.valid_count <= self.MAX_MOBILE_VALID_COUNT

    def is_code_time_safe(self):

        if not self.code_time:
            return True

        return ((datetime.datetime.now() -
                 self.code_time).total_seconds()
                > SAFE_CODE_SECONDS)

    def doSubscribe(self, sceneid):
        self.sceneid = sceneid
        self.subscribe = True
        self.subscribe_time = self.subscribe_time or datetime.datetime.now()
        self.save()

    def unSubscribe(self):
        self.subscribe = False
        self.save()


class WXUserCharge(models.Model):
    EFFECT = 'effect'
    INVALID = 'invalid'
    STATUS_CHOICES = (
        (EFFECT, u'有效'),
        (INVALID, u'失效'),
    )

    wxuser_id = models.IntegerField(default=0, verbose_name=u'微信用户ID')
    employee = models.ForeignKey(User, related_name='employee_wxusers', verbose_name=u'接管人')

    status = models.CharField(max_length=16, blank=True, choices=STATUS_CHOICES,
                              default=EFFECT, verbose_name=u'状态')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'shop_weixin_user_charge'
        unique_together = ("wxuser_id", "employee")
        app_label = 'weixin'
        verbose_name = u'微信用户接管'
        verbose_name_plural = u'微信用户接管列表'

    def __unicode__(self):
        return '<{0},{1},{2}>'.format(self.wxuser_id, self.employee, self.get_status_display())


class ResponseManager(managers.CacheManager):
    def get_queryset(self):
        return (super(ResponseManager, self).get_queryset().extra(
            select={'length': 'Length(message)'}).order_by('-length'))

    @property
    def FuzzyMatch(self):
        return self.get_queryset().filter(fuzzy_match=True)

    @property
    def FullMatch(self):
        return self.get_queryset().filter(fuzzy_match=False)


class WeiXinAutoResponse(models.Model):
    WX_TEXT = 'text'
    WX_IMAGE = 'image'
    WX_VOICE = 'voice'
    WX_VIDEO = 'video'
    WX_THUMB = 'thumb'
    WX_MUSIC = 'music'
    WX_NEWS = 'news'
    WX_LOCATION = 'location'
    WX_LINK = 'link'
    WX_DEFAULT = 'DEFAULT'
    WX_EVENT = 'event'

    WX_EVENT_SUBSCRIBE = 'subscribe'
    WX_EVENT_UNSUBSCRIBE = 'unsubscribe'
    WX_EVENT_SCAN = 'SCAN'
    WX_EVENT_LOCATION = 'LOCATION'
    WX_EVENT_CLICK = 'CLICK'
    WX_EVENT_VIEW = 'VIEW'
    WX_EVENT_ORDER = 'merchant_order'
    WX_EVENT_SCAN_WAITMSG = 'scancode_waitmsg'
    WX_EVENT_PIC_SYSPHOTO = 'pic_sysphoto'
    WX_EVENT_PIC_ALBUM = 'pic_photo_or_album'
    WX_EVENT_PIC_WEIXIN = 'pic_weixin'
    WX_EVENT_KF_CLOSE_SESSION = 'kf_close_session'
    WX_EVENT_KF_CREATE_SESSION = 'kf_create_session'
    WX_EVENT_LOCATION_SELECT = 'location_select'
    WX_EVENT_FAQS = 'faqs'
    WX_EVENT_TSJF = 'TEMPLATESENDJOBFINISH'

    WX_TYPE = (
        (WX_TEXT, u'文本'),
        (WX_IMAGE, u'图片'),
        (WX_VOICE, u'语音'),
        (WX_VIDEO, u'视频'),
        (WX_THUMB, u'缩略图'),
        (WX_MUSIC, u'音乐'),
        (WX_NEWS, u'新闻'),
    )

    message = models.CharField(max_length=64, unique=True, verbose_name=u"消息")

    rtype = models.CharField(max_length=8, choices=WX_TYPE, default=WX_TEXT, verbose_name=u"类型")

    media_id = models.CharField(max_length=1024, blank=True, verbose_name=u'媒体ID')

    title = models.CharField(max_length=512, blank=True, verbose_name=u'标题')
    content = models.CharField(max_length=4096, blank=True, verbose_name=u'回复信息')

    music_url = models.CharField(max_length=512, blank=True, verbose_name=u'音乐链接')
    hq_music_url = models.CharField(max_length=512, blank=True, verbose_name=u'高品质音乐链接')

    news_json = JSONCharMyField(max_length=8192, blank=True, default={}, verbose_name=u'图文信息')

    fuzzy_match = models.BooleanField(default=True, verbose_name=u'模糊匹配')

    class Meta:
        db_table = 'shop_weixin_response'
        app_label = 'weixin'
        verbose_name = u'微信回复'
        verbose_name_plural = u'微信回复列表'

    def __unicode__(self):
        return u'<WeiXinAutoResponse:%d,%s>' % (self.id,
                                                self.get_rtype_display())

    @classmethod
    def respDefault(cls):
        resp, state = cls.objects.get_or_create(message=cls.WX_DEFAULT,
                                                rtype=cls.WX_TEXT)
        return resp.autoParams()

    @classmethod
    def respEmptyString(cls):
        return {'MsgType': cls.WX_TEXT,
                'Content': ''}

    @classmethod
    def respDKF(cls):
        return {'MsgType': 'transfer_customer_service'}

    def respText(self):
        self.content = self.content.replace('\r', '')
        return {'MsgType': self.rtype,
                'Content': self.content.replace('\r', '')}

    def respImage(self):

        return {'MsgType': self.rtype,
                'Image': {'MediaId': self.media_id
                          }}

    def respVoice(self):

        return {'MsgType': self.rtype,
                'Voice': {'MediaId': self.media_id
                          }}

    def respVideo(self):

        return {'MsgType': self.rtype,
                'Video': {'MediaId': self.media_id,
                          'Title': self.title,
                          'Description': self.content.replace('\r', '')
                          }}

    def respMusic(self):

        return {'MsgType': self.rtype,
                'Music': {'Title': self.title,
                          'Description': self.content.replace('\r', ''),
                          'ThumbMediaId': self.media_id,
                          'MusicURL': self.music_url,
                          'HQMusicUrl': self.hq_music_url
                          }}

    def respNews(self):
        news = self.news_json
        return {'MsgType': self.rtype,
                'ArticleCount': len(news),
                'Articles': {'item': news}}

    def autoParams(self):

        if self.rtype == self.WX_TEXT:
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


class ReferalRelationship(models.Model):
    """ 保存待确定的推荐关系 """
    referal_from_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"推荐人ID")
    referal_to_mobile = models.CharField(max_length=12, db_index=True, verbose_name=u"被推荐人手机")
    time_created = models.DateTimeField(default=timezone.now, verbose_name="time created")

    class Meta:
        db_table = 'shop_weixin_referal_relationship'
        app_label = 'weixin'


class ReferalBonusRecord(models.Model):
    REFERAL_BONUS_STATUS = ((0, u'未知'), (1, u'确定'), (2, u'取消'))
    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"微信ID")
    referal_user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"被推荐人微信ID")
    trade_id = models.IntegerField(default=0, db_index=True, unique=True, verbose_name=u"订单号")
    bonus_value = models.IntegerField(default=0, verbose_name=u"金额（分）")  # cent
    confirmed_status = models.IntegerField(default=0, choices=REFERAL_BONUS_STATUS,
                                           verbose_name=u'状态')  # 0 unconfirmed, 1 confirmed, 2 cancelled
    created = models.DateTimeField(default=timezone.now, verbose_name=u"创建时间")

    class Meta:
        db_table = 'shop_weixin_referal_bonus_record'
        app_label = 'weixin'
        verbose_name = u'大使返利'
        verbose_name_plural = u'大使返利列表'


class BonusCashoutRecord(models.Model):
    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"ID")
    cashout_value = models.IntegerField()
    cashout_time = models.DateTimeField(default=timezone.now, verbose_name="cashout time")

    class Meta:
        db_table = 'shop_weixin_bonus_cashout_record'
        app_label = 'weixin'


class ReferalSummary(models.Model):
    user_openid = models.CharField(max_length=64, db_index=True, unique=True, verbose_name=u"ID")
    total_confirmed_value = models.IntegerField(default=0)
    cashed_value = models.IntegerField(default=0)
    # uncashed_value = total_confirmed_value - cashed_value

    direct_referal_count = models.IntegerField(default=0)
    indirect_referal_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'shop_weixin_referal_summary'
        app_label = 'weixin'


class Refund(models.Model):
    REFUND_TYPES = ((0, u'晒单返现'),
                    (1, u'VIP邀请'),
                    (2, u'10积分换购'),
                    (3, u'满100元返10元'),
                    (4, u'100元免单'),
                    (5, u'10积分返邮费'))

    REFUND_STATUSES = ((0, u'等待审核'),
                       (1, u'审核通过'),
                       (2, u'审核不通过'),
                       (3, u'完成'))

    PAY_TYPES = ((0, u'申请退款'),
                 (1, u'退邮费'),
                 (2, u'支付宝转账'),
                 (3, u'银行转账'))

    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"微信ID")

    mobile = models.CharField(max_length=24, blank=True, verbose_name=u"手机")

    ### note: trade_id in mergetrade is biginteger.
    trade_id = models.IntegerField(default=0, unique=True, verbose_name=u'订单ID')

    ### 晒单返现 VIP邀请
    refund_type = models.IntegerField(default=0, choices=REFUND_TYPES, verbose_name=u'返利类型')

    ### 支付宝转账 退邮费 申请退款
    pay_type = models.IntegerField(default=0, choices=PAY_TYPES, verbose_name=u'支付方式')

    vip_code = models.CharField(max_length=10, blank=True, verbose_name=u'VIP邀请码')

    ### 以分为单位
    pay_amount = models.IntegerField(default=0, verbose_name=u'金额')

    ### 0 等待审核, 1 审核通过, 2 审核不通过, 3 完成
    refund_status = models.IntegerField(default=0, choices=REFUND_STATUSES, verbose_name=u'状态')

    ### 备注支付宝帐号，财付通帐号等
    review_note = models.CharField(max_length=256, blank=True, verbose_name=u'审核备注')

    pay_note = models.CharField(max_length=256, blank=True, verbose_name=u'返现备注')

    created = models.DateTimeField(null=True, db_index=True, auto_now_add=True, verbose_name=u'申请日期')
    pay_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'付款日期')

    class Meta:
        db_table = 'shop_weixin_refund'
        app_label = 'weixin'
        verbose_name = u'返现订单'
        verbose_name_plural = u'返现订单列表'
        permissions = [
            ("can_refund_agree", u"返现订单审核权限"),
            ("can_refund_confirm", u"返现订单支付确认权限"),
        ]


class FreeSample(models.Model):
    outer_id = models.CharField(max_length=32, unique=True, null=False, blank=True, verbose_name=u'外部编码')
    name = models.CharField(max_length=64, blank=True, verbose_name=u'商品名称')
    expiry = models.DateTimeField(null=False, blank=False, verbose_name=u'过期时间')
    stock = models.IntegerField(default=0, verbose_name=u'库存')

    pic_url = models.URLField(blank=True, verbose_name='商品图片')
    sale_url = models.URLField(blank=True, verbose_name='销售链接')

    class Meta:
        db_table = 'shop_weixin_free_sample'
        app_label = 'weixin'
        verbose_name = u'试用商品'
        verbose_name_plural = u'试用商品列表'

    def __unicode__(self):
        return self.name


class SampleSku(models.Model):
    sample_product = models.ForeignKey(FreeSample, verbose_name=u'试用商品', related_name="skus")
    sku_code = models.CharField(max_length=32, null=False, blank=True, verbose_name=u'SKU编码')
    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'款式尺寸')

    class Meta:
        db_table = 'shop_weixin_sample_sku'
        app_label = 'weixin'
        verbose_name = u'试用商品SKU'
        verbose_name_plural = u'试用商品SKU列表'

    def __unicode__(self):
        return '-'.join([str(self.sample_product), self.sku_name])


class SampleOrder(models.Model):
    sample_product = models.ForeignKey(FreeSample, related_name="sample_orders", verbose_name=u'试用商品')
    sku_code = models.CharField(max_length=32, null=False, blank=True, verbose_name=u'SKU编码')
    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"微信ID")
    created = models.DateTimeField(auto_now_add=True, db_index=True, null=True, verbose_name=u'创建时间')
    vipcode = models.CharField(max_length=16, null=False, db_index=True, blank=False, verbose_name=u'VIP邀请码')
    problem_score = models.IntegerField(default=0, verbose_name=u"答题分数")
    status = models.IntegerField(default=0, db_index=True, verbose_name=u"状态")

    class Meta:
        db_table = 'shop_weixin_sample_order'
        app_label = 'weixin'
        verbose_name = u'试用申请'
        verbose_name_plural = u'试用申请列表'


class VipCode(models.Model):
    CODE_TYPES = ((0, u'试用'), (1, u'购买'))

    owner_openid = models.OneToOneField(WeiXinUser, related_name="vipcodes", verbose_name=u"微信ID")
    code = models.CharField(max_length=16, unique=True, null=False, blank=False, verbose_name=u'F码')
    expiry = models.DateTimeField(null=False, blank=False, verbose_name=u'过期时间')

    ### 1. for getting samples; 2. for purchase discount
    code_type = models.IntegerField(default=0, choices=CODE_TYPES, verbose_name=u'支付方式')

    ### get $10 for $50 purchase; get $25 for $100 purchase;
    code_rule = models.CharField(max_length=256, null=False, blank=True, verbose_name=u'使用规则')

    ### once or multiple times
    max_usage = models.IntegerField(default=0, verbose_name=u'可用次数')

    ### total number of usage
    usage_count = models.IntegerField(default=0, db_index=True, verbose_name=u'已使用')

    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    objects = VipCodeManager()

    class Meta:
        db_table = 'shop_weixin_vipcode'
        app_label = 'weixin'
        verbose_name = u'VIP邀请码'
        verbose_name_plural = u'VIP邀请码列表'


class Coupon(models.Model):
    description = models.CharField(max_length=256, null=False, blank=True, verbose_name=u'描述')
    coupon_url = models.URLField(blank=True, verbose_name='领取链接')
    face_value = models.IntegerField(default=0, verbose_name=u'面值')
    expiry = models.DateTimeField(null=False, blank=False, verbose_name=u'过期时间')
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'shop_weixin_coupon'
        app_label = 'weixin'
        verbose_name = u'优惠券'
        verbose_name_plural = u'优惠券列表'


class CouponClick(models.Model):
    coupon = models.ForeignKey(Coupon, related_name='clicks', verbose_name=u'优惠券')
    wx_user = models.ForeignKey(WeiXinUser, related_name="couponclicks", verbose_name=u"微信ID")
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')
    vipcode = models.CharField(max_length=16, null=False, blank=False, verbose_name=u'VIP邀请码')

    class Meta:
        db_table = 'shop_weixin_coupon_click'
        app_label = 'weixin'
        verbose_name = u'优惠券点击'
        verbose_name_plural = u'优惠券点击列表'


# class AmbassCoupon(models.Model):
#    openid = models.CharField(max_length=64,db_index=True,verbose_name=u"微信ID")
#    coupon_id = models.IntegerField(default=0,db_index=True,verbose_name=u"优惠券ID")
#    created = models.DateTimeField(auto_now_add=True,null=True,verbose_name=u'创建时间')
#
#    class Meta:
#        db_table = 'shop_ambass_coupon'
#        verbose_name = u'优尼大使优惠券'
#        verbose_name_plural = u'优尼大使优惠券列表'


class Survey(models.Model):
    selection = models.IntegerField(default=0, verbose_name=u'选择')
    wx_user = models.ForeignKey(WeiXinUser, related_name="surveys", verbose_name=u"微信ID")
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'shop_weixin_survey'
        app_label = 'weixin'
        verbose_name = u'用户调研'
        verbose_name_plural = u'用户调研列表'


class SampleChoose(models.Model):
    A = 1
    B = 2
    choices = ((A, u'斗篷'),
               (B, u'睡袋'))

    user_openid = models.CharField(max_length=64, unique=True, verbose_name=u"微信ID")
    vipcode = models.CharField(max_length=16, null=False, blank=False, verbose_name=u'VIP邀请码')
    mobile = models.CharField(max_length=24, blank=True, verbose_name=u"手机")
    selection = models.IntegerField(default=0, choices=choices, verbose_name=u'选择')
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'shop_weixin_sample_choose'
        app_label = 'weixin'
        verbose_name = u'试用商品选择'
        verbose_name_plural = u'试用商品选择列表'


class TradeScoreRelevance(models.Model):
    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"微信ID")
    trade_id = models.CharField(max_length=64, unique=True, verbose_name=u'交易ID')

    mobile = models.CharField(max_length=36, db_index=True, blank=True, verbose_name=u'手机')
    # 订单成交金额 以分未单位
    payment = models.IntegerField(default=0, verbose_name=u'付款金额')

    is_used = models.BooleanField(default=False, verbose_name=u'使用')
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'shop_weixin_trade_score_relate'
        app_label = 'weixin'
        verbose_name = u'交易积分关联'
        verbose_name_plural = u'交易积分关联列表'


class WeixinUserScore(models.Model):
    user_openid = models.CharField(max_length=64, unique=True, verbose_name=u"微信ID")

    user_score = models.PositiveIntegerField(default=0, verbose_name=u'剩余积分')

    expiring_score = models.PositiveIntegerField(default=0, verbose_name=u'即将过期积分')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'shop_weixin_user_score'
        app_label = 'weixin'
        verbose_name = u'用户积分'
        verbose_name_plural = u'用户积分列表'


class WeixinScoreItem(models.Model):
    FROZEN = -3
    AWARD = -2
    CONSUME = -1
    OTHER = 0
    INVITE = 1
    SHOPPING = 2
    ACTIVE = 3
    READCLICK = 4

    choices = ((FROZEN, u'冻结积分'),
               (CONSUME, u'返现消费'),
               (SHOPPING, u'购物积分'),
               (INVITE, u'邀请积分'),
               (ACTIVE, u'活动积分'),
               (AWARD, u'中奖扣除'),
               (READCLICK, u'阅读点击'),
               (OTHER, u'其它'),)

    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"微信ID")

    score = models.IntegerField(default=0, verbose_name=u'积分变化')
    score_type = models.IntegerField(default=0, db_index=True, choices=choices, verbose_name=u'积分类型')

    expired_at = models.DateTimeField(blank=True, null=True, verbose_name=u'过期时间')
    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    memo = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'变更备注')

    class Meta:
        db_table = 'shop_weixin_score_item'
        app_label = 'weixin'
        verbose_name = u'用户积分明细'
        verbose_name_plural = u'用户积分明细列表'


class WeixinScoreBuy(models.Model):
    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"微信ID")

    buy_score = models.PositiveIntegerField(default=0, verbose_name=u'换购积分')

    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    batch = models.IntegerField(default=0, verbose_name=u"批次")

    class Meta:
        db_table = 'shop_weixin_scorebuy'
        app_label = 'weixin'
        verbose_name = u'积分换购名单'
        verbose_name_plural = u'积分换购名单列表'


class WeixinClickScore(models.Model):
    description = models.CharField(max_length=64, verbose_name=u"描述")
    redirect_link = models.URLField(blank=True, verbose_name=u"跳转链接")
    score = models.IntegerField(default=0, verbose_name=u"积分数")
    expiry = models.DateTimeField(blank=True, null=True, verbose_name=u'过期时间')
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'shop_weixin_click_score'
        app_label = 'weixin'
        verbose_name = u'积分链接'
        verbose_name_plural = u'积分链接列表'


class WeixinClickScoreRecord(models.Model):
    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"微信ID")
    click_score_id = models.IntegerField(default=0, verbose_name=u"积分链接ID")
    score = models.IntegerField(default=0, verbose_name=u"积分数")
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'shop_weixin_click_score_item'
        unique_together = ('user_openid', 'click_score_id')
        app_label = 'weixin'
        verbose_name = u'积分链接点击'
        verbose_name_plural = u'积分链接点击列表'


from shopapp.signals import (confirm_trade_signal,
                             weixin_referal_signal,
                             weixin_refund_signal,
                             weixin_readclick_signal,
                             weixin_verifymobile_signal,
                             weixin_surveyconfirm_signal,
                             weixin_sampleconfirm_signal)


def click2score(sender, click_score_record_id, *args, **kwargs):
    try:
        record = WeixinClickScoreRecord.objects.get(pk=click_score_record_id)
        user_openid = record.user_openid
        score = record.score
        click_score_id = record.click_score_id
        WeixinScoreItem.objects.create(user_openid=user_openid,
                                       score=score,
                                       score_type=WeixinScoreItem.READCLICK,
                                       expired_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                       memo=u"阅读点击(%d)。" % click_score_id)
        wx_user_score, state = WeixinUserScore.objects.get_or_create(user_openid=user_openid)
        wx_user_score.user_score = models.F('user_score') + score
        wx_user_score.save()
    except Exception, exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'阅读点击积分转换失败:%s' % exc.message, exc_info=True)


weixin_readclick_signal.connect(click2score, sender=WeixinClickScoreRecord)


def sample_confirm_answer2score(sender, sample_order_id, *args, **kwargs):
    try:
        sample_order = SampleOrder.objects.get(pk=sample_order_id)
        user_openid = sample_order.user_openid
        sample_score = sample_order.problem_score
        WeixinScoreItem.objects.create(user_openid=user_openid,
                                       score=sample_score,
                                       score_type=WeixinScoreItem.ACTIVE,
                                       expired_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                       memo=u"试用问答(%d)获得积分。" % sample_order.id)
        wx_user_score, state = WeixinUserScore.objects.get_or_create(user_openid=user_openid)
        wx_user_score.user_score = models.F('user_score') + sample_score
        wx_user_score.save()
    except Exception, exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'试用问答积分转换失败:%s' % exc.message, exc_info=True)


weixin_sampleconfirm_signal.connect(sample_confirm_answer2score, sender=SampleOrder)


# 订单确认收货增加积分
def convert_trade_payment2score(sender, trade_id, *args, **kwargs):
    try:
        from shopback import paramconfig as pcfg
        instance = MergeTrade.objects.get(id=trade_id)
        # the order is finished , print express or handsale
        if (instance.sys_status != pcfg.FINISHED_STATUS
            or (not instance.is_express_print
                and instance.shipping_type != pcfg.EXTRACT_SHIPPING_TYPE)
            or instance.type in (pcfg.FENXIAO_TYPE,
                                 pcfg.EXCHANGE_TYPE,
                                 pcfg.REISSUE_TYPE)):
            return

        trade_score_relev, state = TradeScoreRelevance.objects.get_or_create(trade_id=instance.id)
        if state:
            trade_score_relev.mobile = instance.receiver_mobile
            payment_dict = instance.merge_orders.filter(sys_status=pcfg.IN_EFFECT) \
                .aggregate(total_payment=models.Sum('payment'))
            trade_score_relev.payment = int((payment_dict.get('total_payment') or 0) * 100)
            trade_score_relev.save()

        if trade_score_relev.is_used:
            return

        mobiles = set([m.strip() for m in instance.receiver_mobile.split(',') if len(m.strip()) == 11])
        mobiles.update([m.strip() for m in instance.receiver_phone.split(',') if len(m.strip()) == 11])
        wx_users = WeiXinUser.objects.filter(mobile__in=mobiles)

        if wx_users.count() > 0:
            user_openid = wx_users[0].openid
            payment_score = int(round(trade_score_relev.payment / 1000.0))
            WeixinScoreItem.objects.create(user_openid=user_openid,
                                           score=payment_score,
                                           score_type=WeixinScoreItem.SHOPPING,
                                           expired_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                           memo=u"订单(%s)确认收货，结算积分。" % (instance.id))

            wx_user_score, state = WeixinUserScore.objects.get_or_create(user_openid=user_openid)
            wx_user_score.user_score = models.F('user_score') + payment_score
            wx_user_score.save()

            trade_score_relev.user_openid = user_openid
            trade_score_relev.is_used = True
            trade_score_relev.save()

    except Exception, exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'订单积分转换失败:%s' % exc.message, exc_info=True)


#confirm_trade_signal.connect(convert_trade_payment2score, sender=MergeTrade)
#包裹确认收货增加积分
def convert_package_payment2score(sender,package_order_id,*args,**kwargs):
    try:
        from shopback import paramconfig as pcfg
        instance = PackageOrder.objects.get(id = package_order_id)
        #the order is finished , print express or handsale
        if (instance.sys_status != PackageOrder.FINISHED_STATUS
            or (not instance.is_express_print)
            or instance.type in (pcfg.FENXIAO_TYPE,
                                 pcfg.EXCHANGE_TYPE,
                                 pcfg.REISSUE_TYPE)):
            return

        trade_score_relev,state = TradeScoreRelevance.objects.get_or_create(trade_id=instance.id)
        if state:
            trade_score_relev.mobile = instance.receiver_mobile
            payment_dict = instance.merge_orders.filter(sys_status=pcfg.IN_EFFECT)\
                            .aggregate(total_payment=models.Sum('payment'))
            trade_score_relev.payment = int((payment_dict.get('total_payment') or 0)*100)
            trade_score_relev.save()

        if trade_score_relev.is_used:
            return

        mobiles  = set([m.strip() for m in instance.receiver_mobile.split(',') if len(m.strip())==11 ])
        mobiles.update([m.strip() for m in instance.receiver_phone.split(',') if len(m.strip())==11  ])
        wx_users = WeiXinUser.objects.filter(mobile__in=mobiles)

        if wx_users.count() > 0:

            user_openid = wx_users[0].openid
            payment_score = int(round(trade_score_relev.payment/1000.0))
            WeixinScoreItem.objects.create(user_openid=user_openid,
                                           score=payment_score,
                                           score_type=WeixinScoreItem.SHOPPING,
                                           expired_at=datetime.datetime.now()+datetime.timedelta(days=365),
                                           memo=u"订单(%s)确认收货，结算积分。"%(instance.id))

            wx_user_score,state = WeixinUserScore.objects.get_or_create(user_openid=user_openid)
            wx_user_score.user_score  = models.F('user_score') + payment_score
            wx_user_score.save()

            trade_score_relev.user_openid = user_openid
            trade_score_relev.is_used = True
            trade_score_relev.save()

    except Exception,exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'订单积分转换失败:%s'%exc.message,exc_info=True)


confirm_trade_signal.connect(convert_package_payment2score, sender=PackageOrder)



# 推荐关系增加积分

def convert_referal2score(sender, user_openid, referal_from_openid, *args, **kwargs):
    invite_score = 1
    try:
        WeixinScoreItem.objects.create(user_openid=referal_from_openid,
                                       score=invite_score,
                                       score_type=WeixinScoreItem.INVITE,
                                       expired_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                       memo=u"邀请好友(%s)获得积分。" % (user_openid))

        wx_user_score, state = WeixinUserScore.objects.get_or_create(user_openid=referal_from_openid)
        wx_user_score.user_score = models.F('user_score') + invite_score
        wx_user_score.save()

    except Exception, exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'邀请好友积分保存失败:%s' % exc.message, exc_info=True)


weixin_referal_signal.connect(convert_referal2score, sender=SampleOrder)


# 试用订单审核通过消耗积分
def decrease_sample_score(sender, refund_id, *args, **kwargs):
    try:
        refund = Refund.objects.get(id=refund_id, refund_type=1, refund_status=3)

        sample_score = 20
        wx_user_score, state = WeixinUserScore.objects.get_or_create(
            user_openid=refund.user_openid)

        dec_score = 0 - min(sample_score, wx_user_score.user_score)
        WeixinScoreItem.objects.create(user_openid=refund.user_openid,
                                       score=dec_score,
                                       score_type=WeixinScoreItem.AWARD,
                                       expired_at=datetime.datetime.now(),
                                       memo=u"试用订单(%s)审核通过扣除积分。" % (refund.trade_id))

        wx_user_score.user_score = models.F('user_score') + dec_score
        wx_user_score.save()

    except Refund.DoesNotExist:
        pass

    except Exception, exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'返现积分更新失败:%s' % exc.message, exc_info=True)


weixin_refund_signal.connect(decrease_sample_score, sender=Refund)


# 试用订单审核通过取消订单确认收货积分
def decrease_refund_trade_score(sender, refund_id, *args, **kwargs):
    try:
        refund = Refund.objects.get(id=refund_id, refund_type__in=(1, 3), refund_status=3)

        is_award = refund.refund_type == 1
        refund_score = int(round(refund.pay_amount / 1000.0))

        wx_user_score, state = WeixinUserScore.objects.get_or_create(
            user_openid=refund.user_openid)

        dec_score = 0 - min(refund_score, wx_user_score.user_score)
        WeixinScoreItem.objects.create(user_openid=refund.user_openid,
                                       score=dec_score,
                                       score_type=(WeixinScoreItem.CONSUME, WeixinScoreItem.AWARD)[is_award and 1 or 0],
                                       expired_at=datetime.datetime.now(),
                                       memo=u"%s返现(%s)扣除积分。" % ((u'积分', u'试用')[is_award and 1 or 0], refund.trade_id))

        wx_user_score.user_score = models.F('user_score') + dec_score
        wx_user_score.save()

    except Refund.DoesNotExist:
        pass

    except Exception, exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'试用（返现）积分更新失败:%s' % exc.message, exc_info=True)


weixin_refund_signal.connect(decrease_refund_trade_score, sender=Refund)


def decrease_scorebuy_score(sender, refund_id, *args, **kwargs):
    """积分换购审核通过，扣除换购积分"""

    try:
        refund = Refund.objects.get(id=refund_id, refund_type=2, refund_status=3)
        score_buys = WeixinScoreBuy.objects.filter(user_openid=refund.user_openid)
        if score_buys.count() > 0:
            wx_user_score, state = WeixinUserScore.objects.get_or_create(
                user_openid=refund.user_openid)

            dec_score = 0 - min(score_buys[0].buy_score, wx_user_score.user_score)
            WeixinScoreItem.objects.create(user_openid=refund.user_openid,
                                           score=dec_score,
                                           score_type=WeixinScoreItem.AWARD,
                                           expired_at=datetime.datetime.now(),
                                           memo=u"积分换购通过(%s)消耗积分。" % (refund.trade_id))

            wx_user_score.user_score = models.F('user_score') + dec_score
            wx_user_score.save()

    except Refund.DoesNotExist:
        pass

    except Exception, exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'返现积分更新失败:%s' % exc.message, exc_info=True)


weixin_refund_signal.connect(decrease_scorebuy_score, sender=Refund)


def calc_trade_payment2score(sender, user_openid, *args, **kwargs):
    """手机验证后，将订单金额转换成积分"""

    try:
        from shopback import paramconfig as pcfg
        wx_user = WeiXinUser.objects.get(openid=user_openid)

        trade_scores = TradeScoreRelevance.objects.filter(mobile=wx_user.mobile, is_used=False)
        for trade_score_relev in trade_scores:
            payment_score = int(round(trade_score_relev.payment / 1000.0))
            WeixinScoreItem.objects.create(user_openid=user_openid,
                                           score=payment_score,
                                           score_type=WeixinScoreItem.SHOPPING,
                                           expired_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                           memo=u"微信验证(%s)订单结算积分。" % (trade_score_relev.trade_id))

            wx_user_score, state = WeixinUserScore.objects.get_or_create(user_openid=user_openid)
            wx_user_score.user_score = models.F('user_score') + payment_score
            wx_user_score.save()

            trade_score_relev.user_openid = user_openid
            trade_score_relev.is_used = True
            trade_score_relev.save()

    except Exception, exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'返现积分更新失败:%s' % exc.message, exc_info=True)


weixin_verifymobile_signal.connect(calc_trade_payment2score, sender=WeiXinUser)


def survey_confirm_score(sender, survey_id, *args, **kwargs):
    """手机验证后，将订单金额转换成积分"""

    try:
        survey = Survey.objects.get(id=survey_id)
        user_openid = survey.wx_user.openid
        survey_score = 5
        WeixinScoreItem.objects.create(user_openid=user_openid,
                                       score=survey_score,
                                       score_type=WeixinScoreItem.ACTIVE,
                                       expired_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                       memo=u"调查问卷(%s)获得积分。" % (survey_id))

        wx_user_score, state = WeixinUserScore.objects.get_or_create(user_openid=user_openid)
        wx_user_score.user_score = models.F('user_score') + survey_score
        wx_user_score.save()

    except Exception, exc:

        import logging
        logger = logging.getLogger("celery.handler")
        logger.error(u'问卷积分更新失败:%s' % exc.message, exc_info=True)


weixin_surveyconfirm_signal.connect(survey_confirm_score, sender=Survey)
