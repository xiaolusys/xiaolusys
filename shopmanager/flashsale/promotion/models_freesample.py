#-*- coding:utf-8 -*-
from django.db import models
from core.models import BaseModel,CacheModel
from django.contrib.auth.models import User

from .managers import ReadPacketManager
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.pay.models import Customer
from django.db.models.signals import post_save

class XLFreeSample(CacheModel):
    """ 试用商品 """
    outer_id = models.CharField(max_length=64,blank=True,verbose_name=u'商品编码')
    name     = models.CharField(max_length=64,blank=True,verbose_name=u'活动名称')
    expiried = models.DateTimeField(null=False,blank=False,verbose_name=u'过期时间')

    pic_url  = models.URLField(blank=True,verbose_name='商品图片')
    sale_url = models.URLField(blank=True,verbose_name='销售链接')

    class Meta:
        db_table = 'flashsale_promotion_freesample'
        app_label = 'promotion'
        verbose_name = u'推广/试用商品'
        verbose_name_plural = u'推广/试用商品列表'

    def __unicode__(self):
        return self.name


class XLSampleSku(CacheModel):
    """ 试用商品规格 """
    sample_product = models.ForeignKey(XLFreeSample, verbose_name=u'试用商品', related_name="skus")
    sku_code = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'SKU编码')
    sku_name = models.CharField(max_length=64,blank=True,verbose_name=u'款式尺寸')

    class Meta:
        db_table = 'flashsale_promotion_samplesku'
        app_label = 'promotion'
        verbose_name = u'推广/试用商品SKU'
        verbose_name_plural = u'推广/试用商品SKU列表'

    def __unicode__(self):
        return '-'.join([str(self.sample_product), self.sku_name])


class AppDownloadRecord(BaseModel):
    WAP = 0
    WX = 1
    QQ = 2

    UFROM = ((WAP, u'WAP'), (WX, u'微信'), (QQ, u'QQ'))
    UNUSE = 0
    USED = 1

    USE_STATUS = ((UNUSE, u'未注册'), (USED, u'已注册'))

    from_customer = models.IntegerField(default=0, db_index=True, verbose_name=u'来自用户')
    openid = models.CharField(max_length=128, db_index=True,blank=True, null=True, verbose_name=u'微信授权openid')
    unionid = models.CharField(max_length=128, db_index=True,blank=True, null=True, verbose_name=u'微信授权unionid')
    status = models.BooleanField(default=UNUSE, choices=USE_STATUS, db_index=True, verbose_name=u'是否注册APP')
    mobile = models.CharField(max_length=11, blank=True, null=True, db_index=True,verbose_name=u'手机号')
    ufrom = models.IntegerField(default=0, choices=UFROM, verbose_name=u'来自平台')

    class Meta:
        db_table = 'flashsale_promotion_download_record'
        app_label = 'promotion'
        verbose_name = u'推广/下载记录表'
        verbose_name_plural = u'推广/下载记录表'

    def __unicode__(self):
        return str(self.from_customer)



class XLSampleApply(CacheModel):
    """ 试用申请 """
    INACTIVE = 0
    ACTIVED  = 1
    STATUS_CHOICES = (
        (INACTIVE, u'未激活'),
        (ACTIVED, u'已激活'),
    )
    FROM_WXAPP = 'wxapp'
    FROM_PYQ  = 'pyq'
    FROM_QQ   = 'qq'
    FROM_WB   = 'sinawb'
    FROM_WEB  = 'web'
    FROM_QQSPA = 'qqspa'
    XLMM_APP = 'app'

    FROM_CHOICES = (
        (FROM_WXAPP,u'微信好友'),
        (FROM_PYQ,u'朋友圈'),
        (FROM_QQ,u'QQ'),
        (FROM_WB,u'新浪微博'),
        (FROM_WEB,u'外部网页'),
        (XLMM_APP,u'小鹿美美APP')
    )

    outer_id = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'商品编码')
    sku_code = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'SKU编码')
    event_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name=u'活动ID')
    from_customer = models.BigIntegerField(null=True, blank=True, db_index=True, verbose_name=u'分享人用户ID')
    ufrom    = models.CharField(max_length=8,choices=FROM_CHOICES,blank=True,verbose_name=u'来自平台')
    user_openid  = models.CharField(max_length=28,db_index=True,blank=True,null=True,verbose_name=u'用户openid')
    user_unionid  = models.CharField(max_length=64,db_index=True,blank=True,null=True,verbose_name=u'用户unionid')
    mobile   = models.CharField(max_length=11,null=False,db_index=True,blank=False,verbose_name=u'试用手机')
    vipcode  = models.CharField(max_length=16,db_index=True,blank=True,null=True,verbose_name=u'试用邀请码')
    status   = models.IntegerField(default=INACTIVE,choices=STATUS_CHOICES,db_index=True, verbose_name=u"状态")

    customer_id = models.IntegerField(null=True,blank=True,verbose_name=u"申请者ID")
    headimgurl = models.CharField(max_length=256,null=False,blank=True,verbose_name=u'头图')
    nick = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'昵称')
    class Meta:
        db_table = 'flashsale_promotion_sampleapply'
        app_label = 'promotion'
        verbose_name = u'推广/试用申请'
        verbose_name_plural = u'推广/试用申请列表'

    def is_activated(self):
        return self.status == self.ACTIVED


def generate_red_envelope(sender,instance,created,*args,**kwargs):
    if not instance.is_activated():
        return

    from tasks_activity import task_generate_red_envelope
    task_generate_red_envelope.delay(instance)

post_save.connect(generate_red_envelope, sender=XLSampleApply, dispatch_uid="sampleapply_generate_red_envelope")


def update_appdownloadrecord(sender,instance,created,*args,**kwargs):
    # We only update downloadrecord if unionid or mobile exists.
    if instance.user_unionid or instance.mobile:
        from tasks_activity import task_sampleapply_update_appdownloadrecord
        task_sampleapply_update_appdownloadrecord.delay(instance)

post_save.connect(update_appdownloadrecord, sender=XLSampleApply, dispatch_uid="sampleapply_update_appdownloadrecord")




def get_choice_name(choices, val):
    """
    iterate over choices and find the name for this val
    """
    name = ""
    for entry in choices:
        if entry[0] == val:
            name = entry[1]
    return name


class RedEnvelope(CacheModel):
    STATUS = ((0, 'new'), (1, 'open'))
    TYPE_CHOICES = ((0, 'cash'),(1, 'card'))

    customer_id = models.IntegerField(default=0, db_index=True, verbose_name=u"用户ID")
    event_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name=u'活动ID')
    value = models.IntegerField(default=0, verbose_name=u'金额')
    description = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'文字内容')

    # uni_key: event_id + friend's customer_id
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    
    friend_img = models.CharField(max_length=256, blank=True, null=True, verbose_name=u'朋友头像')
    friend_nick = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'朋友昵称')
    type = models.IntegerField(default=0, choices=TYPE_CHOICES, db_index=True, verbose_name=u'类型')
    status = models.IntegerField(default=0, choices=STATUS, db_index=True, verbose_name=u'打开状态')
    
    class Meta:
        db_table = 'flashsale_promotion_red_envelope'
        verbose_name = u'活动/红包'
        verbose_name_plural = u'活动/红包列表'
    
    def status_display(self):
        return get_choice_name(self.STATUS, self.status)

    def type_display(self):
        return get_choice_name(self.TYPE_CHOICES, self.type)

    def is_cashable(self):
        return self.status == 1 and self.type == 0

    def is_card_open(self):
        return self.status == 1 and self.type == 1

    def value_display(self):
        return float("%.2f" % (self.value * 0.01))
    
def envelope_create_budgetlog(sender,instance,created,*args,**kwargs):
    if not created:
        return
    from tasks_activity import task_envelope_create_budgetlog
    task_envelope_create_budgetlog.delay(instance)

post_save.connect(envelope_create_budgetlog, sender=RedEnvelope)


def open_envelope_update_budgetlog(sender,instance,created,*args,**kwargs):
    if not instance.is_cashable():
        return
    from tasks_activity import task_envelope_update_budgetlog
    task_envelope_update_budgetlog.delay(instance)

post_save.connect(open_envelope_update_budgetlog, sender=RedEnvelope)


def open_envelope_decide_awardwinner(sender,instance,created,*args,**kwargs):
    if not instance.is_card_open():
        return
    from tasks_activity import task_decide_award_winner
    task_decide_award_winner.delay(instance)

post_save.connect(open_envelope_decide_awardwinner, sender=RedEnvelope)

    
class AwardWinner(CacheModel):
    STATUS = ((0, '未领取'),(1, '已领取'))
    customer_id = models.IntegerField(default=0, db_index=True, verbose_name=u"用户ID")
    customer_img = models.CharField(max_length=256, blank=True, null=True, verbose_name=u'头像')
    customer_nick = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'昵称')
    event_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name=u'活动ID')
    invite_num = models.IntegerField(default=0, verbose_name=u'中奖时邀请数')

    # uni_key: event_id + customer_id
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    status = models.IntegerField(default=0, choices=STATUS, verbose_name=u'领取状态')

    class Meta:
        db_table = 'flashsale_promotion_award_winner'
        verbose_name = u'活动/中奖'
        verbose_name_plural = u'活动/中奖列表'
    

class XLSampleOrder(CacheModel):
    """ 正式试用订单 """

    xlsp_apply = models.IntegerField(db_index=True, verbose_name=u'试用申请id', default=0, blank=True)
    customer_id = models.CharField(max_length=64,db_index=True,verbose_name=u"用户ID")
    outer_id = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'商品编码')
    sku_code = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'SKU编码')
    vipcode  = models.CharField(max_length=16,null=False,db_index=True,blank=False,verbose_name=u'试用邀请码')
    problem_score = models.IntegerField(default=0, verbose_name=u"答题分数")
    status = models.IntegerField(default=0,db_index=True, verbose_name=u"中奖批次")
    award_status  = models.BooleanField(default=False, db_index=True, verbose_name="领取奖品")

    class Meta:
        db_table = 'flashsale_promotion_sampleorder'
        app_label = 'promotion'
        verbose_name = u'推广/试用订单'
        verbose_name_plural = u'推广/试用订单列表'

    def is_sampleorder_pass(self):
        return self.status > 0

    def is_award_complete(self):
        return self.award_status == True

    def award_confirm(self):
        self.award_status = True
        self.save()

        from flashsale.pay.models_coupon_new import UserCoupon
        from flashsale.pay import constants
        user_coupon = UserCoupon()
        user_coupon.release_by_template(buyer_id=self.customer_id,
                                        template_id=constants.COUPON_ID_FOR_20160223_AWARD)

class ReadPacket(CacheModel):
    """ 红包记录 """
    
    
    EXCHANGE = 1
    NOT_EXCHANGE = 0
    EXCHANGE_STATUS = ((EXCHANGE, u'已打开'), (NOT_EXCHANGE, u'未打开'))

    TYPE_CHOICES = ((0, 'cash'),(1, 'card'))

    customer = models.CharField(max_length=64, db_index=True, verbose_name=u"用户ID")
    value = models.FloatField(default=0, verbose_name=u'金额')
    status = models.IntegerField(default=0, choices=EXCHANGE_STATUS, verbose_name=u'是否兑换')
    content = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'文字内容')

    objects = ReadPacketManager()

    class Meta:
        db_table = 'flashsale_promotion_red_packet'
        app_label = 'promotion'

        verbose_name = u'推广/discard'
        verbose_name_plural = u'推广/discard'



