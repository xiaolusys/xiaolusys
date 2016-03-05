#-*- coding:utf8 -*-
from django.db import models
from core.models import BaseModel,CacheModel
from django.contrib.auth.models import User

from .managers import ReadPacketManager
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.pay.models import Customer

class XLFreeSample(CacheModel):
    """ 试用商品 """
    outer_id = models.CharField(max_length=64,blank=True,verbose_name=u'商品编码')
    name     = models.CharField(max_length=64,blank=True,verbose_name=u'活动名称')
    expiried = models.DateTimeField(null=False,blank=False,verbose_name=u'过期时间')

    pic_url  = models.URLField(verify_exists=False,blank=True,verbose_name='商品图片')
    sale_url = models.URLField(verify_exists=False,blank=True,verbose_name='销售链接')

    class Meta:
        db_table = 'flashsale_promotion_freesample'
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
        verbose_name = u'推广/试用商品SKU'
        verbose_name_plural = u'推广/试用商品SKU列表'

    def __unicode__(self):
        return '-'.join([str(self.sample_product), self.sku_name])


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
    from_customer = models.BigIntegerField(null=True, blank=True, verbose_name=u'分享人用户ID')
    ufrom    = models.CharField(max_length=8,choices=FROM_CHOICES,blank=True,verbose_name=u'来自平台')
    user_openid  = models.CharField(max_length=28,db_index=True,blank=True,null=True,verbose_name=u'用户openid')
    mobile   = models.CharField(max_length=11,null=False,db_index=True,blank=False,verbose_name=u'试用手机')
    vipcode  = models.CharField(max_length=16,db_index=True,blank=True,null=True,verbose_name=u'试用邀请码')
    status   = models.IntegerField(default=INACTIVE,choices=STATUS_CHOICES,db_index=True, verbose_name=u"状态")

    headimgurl = models.CharField(max_length=256,null=False,blank=True,verbose_name=u'头图')
    nick = models.CharField(max_length=32,null=False,blank=True,verbose_name=u'昵称')
    class Meta:
        db_table = 'flashsale_promotion_sampleapply'
        verbose_name = u'推广/试用申请'
        verbose_name_plural = u'推广/试用申请列表'


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
    EXCHANGE_STATUS = ((EXCHANGE, u'已兑换'), (NOT_EXCHANGE, u'未兑换'))

    customer = models.CharField(max_length=64, db_index=True, verbose_name=u"用户ID")
    value = models.FloatField(default=0, verbose_name=u'金额')
    status = models.IntegerField(default=0, choices=EXCHANGE_STATUS, verbose_name=u'是否兑换')
    content = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'文字内容')
    objects = ReadPacketManager()

    class Meta:
        db_table = 'flashsale_promotion_red_packet'
        verbose_name = u'推广/活动红包表'
        verbose_name_plural = u'推广/活动红包列表'


class AppDownloadRecord(BaseModel):
    WAP = 0
    WX = 1
    QQ = 2

    UFROM = ((WAP, u'WAP'), (WX, u'微信'), (QQ, u'QQ'))
    UNUSE = 0
    USED = 1

    USE_STATUS = ((UNUSE, u'未使用'), (USED, u'已经使用'))

    from_customer = models.IntegerField(default=0, db_index=True, verbose_name=u'来自用户')
    openid = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'微信授权openid')
    status = models.BooleanField(default=UNUSE, choices=USE_STATUS, verbose_name=u'是否是特卖用户')
    mobile = models.CharField(max_length=11, blank=True, null=True, verbose_name=u'手机号')
    ufrom = models.IntegerField(default=0, choices=UFROM, verbose_name=u'来自平台')

    class Meta:
        db_table = 'flashsale_promotion_download_record'
        verbose_name = u'推广/下载记录表'
        verbose_name_plural = u'推广/下载记录表'

    def __unicode__(self):
        return str(self.from_customer)

