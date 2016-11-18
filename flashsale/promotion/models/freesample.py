# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from core.models import BaseModel
from django.contrib.auth.models import User

from .managers.redpack import ReadPacketManager
from django.db.models.signals import post_save


class XLFreeSample(BaseModel):
    """ 试用商品 """
    outer_id = models.CharField(max_length=64, blank=True, verbose_name=u'商品编码')
    name = models.CharField(max_length=64, blank=True, verbose_name=u'活动名称')
    expiried = models.DateTimeField(null=False, blank=False, verbose_name=u'过期时间')

    pic_url = models.URLField(blank=True, verbose_name='商品图片')
    sale_url = models.URLField(blank=True, verbose_name='销售链接')

    class Meta:
        db_table = 'flashsale_promotion_freesample'
        app_label = 'promotion'
        verbose_name = u'推广/试用商品'
        verbose_name_plural = u'推广/试用商品列表'

    def __unicode__(self):
        return self.name


class XLSampleSku(BaseModel):
    """ 试用商品规格 """
    sample_product = models.ForeignKey(XLFreeSample, verbose_name=u'试用商品', related_name="skus")
    sku_code = models.CharField(max_length=32, null=False, blank=True, verbose_name=u'SKU编码')
    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'款式尺寸')

    class Meta:
        db_table = 'flashsale_promotion_samplesku'
        app_label = 'promotion'
        verbose_name = u'推广/试用商品SKU'
        verbose_name_plural = u'推广/试用商品SKU列表'

    def __unicode__(self):
        return '-'.join([str(self.sample_product), self.sku_name])


class DownloadMobileRecord(BaseModel):
    UNKNOWN = 0
    QRCODE = 1
    ACTIVITY = 2
    REDENVELOPE = 3
    UFROM = (
        (UNKNOWN, u'未知'),
        (QRCODE, u'二维码'),
        (ACTIVITY, u'活动'),
        (REDENVELOPE, u'红包')
    )

    from_customer = models.IntegerField(db_index=True, verbose_name=u'来自用户')
    mobile = models.CharField(max_length=11, db_index=True, verbose_name=u'用户手机号')
    ufrom = models.IntegerField(default=0, choices=UFROM, verbose_name=u'来源')
    uni_key = models.CharField(max_length=64, unique=True, verbose_name=u'唯一标识')

    class Meta:
        db_table = 'flashsale_promotion_download_mobile_record'
        app_label = 'promotion'
        verbose_name = u'推广/下载手机记录表'
        verbose_name_plural = u'推广/下载手机记录表'

    def __unicode__(self):
        return str(self.from_customer)


def sync_mobile_download_to_total_record(instance, created, *args, **kwargs):
    from flashsale.promotion.tasks_activity import task_collect_mobile_download_record
    task_collect_mobile_download_record.delay(instance)

post_save.connect(sync_mobile_download_to_total_record, sender=DownloadMobileRecord,
                  dispatch_uid='post_save_sync_mobile_download_to_total_record')


class DownloadUnionidRecord(BaseModel):

    from_customer = models.IntegerField(db_index=True, verbose_name=u'来自用户')
    ufrom = models.IntegerField(default=0, choices=DownloadMobileRecord.UFROM, verbose_name=u'来源')
    uni_key = models.CharField(max_length=64, unique=True, verbose_name=u'唯一标识')
    unionid = models.CharField(max_length=64, db_index=True, verbose_name=u'微信授权unionid')
    headimgurl = models.CharField(max_length=256, null=False, blank=True, verbose_name=u'头图')
    nick = models.CharField(max_length=32, null=False, blank=True, verbose_name=u'昵称')

    class Meta:
        db_table = 'flashsale_promotion_download_unionid_record'
        app_label = 'promotion'
        verbose_name = u'推广/下载unionid记录表'
        verbose_name_plural = u'推广/下载unionid记录表'

    def __unicode__(self):
        return str(self.from_customer)


def sync_union_download_to_total_record(instance, created, *args, **kwargs):
    from flashsale.promotion.tasks_activity import task_collect_union_download_record
    task_collect_union_download_record.delay(instance)

post_save.connect(sync_union_download_to_total_record, sender=DownloadUnionidRecord,
                  dispatch_uid='post_save_sync_union_download_to_total_record')


class AppDownloadRecord(BaseModel):

    WXAPP = 'wxapp'
    PYQ = 'pyq'
    QQ = 'qq'
    SINAWB = 'sinawb'
    WAP = 'wap'
    QQSPA = 'qqspa'
    APP = 'app'
    LESSON = 'lesson'

    UFROM = ((WXAPP, u'微信'),
             (PYQ, u'朋友圈'),
             (SINAWB, u'新浪微博'),
             (WAP, u'WAP'),
             (QQSPA, u'QQ空间'),
             (APP, u'小鹿美美app'),
             (LESSON, u'小鹿大学'),)

    UNUSE = False
    USED = True

    UNKNOWN = 0
    QRCODE = 1
    ACTIVITY = 2
    REDENVELOPE = 3
    INNER_UFROM = (
        (UNKNOWN, u'未知'),
        (QRCODE, u'二维码'),
        (ACTIVITY, u'活动'),
        (REDENVELOPE, u'红包')
    )

    USE_STATUS = ((UNUSE, u'未注册'), (USED, u'已注册'))

    from_customer = models.IntegerField(default=0, db_index=True, verbose_name=u'来自用户')
    openid = models.CharField(max_length=128, db_index=True, blank=True, null=True, verbose_name=u'微信授权openid')
    unionid = models.CharField(max_length=128, db_index=True, blank=True, null=True, verbose_name=u'微信授权unionid')
    headimgurl = models.CharField(max_length=256, null=False, blank=True, verbose_name=u'头图')
    nick = models.CharField(max_length=32, null=False, blank=True, verbose_name=u'昵称')
    status = models.BooleanField(default=UNUSE, choices=USE_STATUS, db_index=True, verbose_name=u'是否注册APP')
    mobile = models.CharField(max_length=11, blank=True, null=True, db_index=True, verbose_name=u'手机号')
    ufrom = models.CharField(max_length=8, default=WXAPP, choices=UFROM, verbose_name=u'来自平台')
    inner_ufrom = models.IntegerField(default=UNKNOWN, db_index=True, choices=INNER_UFROM, verbose_name=u'内部渠道')
    uni_key = models.CharField(max_length=64, unique=True, null=True, verbose_name=u'唯一标识')

    class Meta:
        db_table = 'flashsale_promotion_download_record'
        app_label = 'promotion'
        verbose_name = u'推广/下载记录表'
        verbose_name_plural = u'推广/下载记录表'

    def __unicode__(self):
        return str(self.from_customer)

    def is_activated(self):
        return self.status == AppDownloadRecord.USED

    @property
    def from_mama(self):
        from flashsale.pay.models import Customer
        from flashsale.xiaolumm.models import XiaoluMama

        c = Customer.objects.filter(id=self.from_customer).first()
        if c:
            m = XiaoluMama.objects.filter(openid=c.unionid).first()
            if m:
                return m.id
        return 0
            
    @property
    def fans_customer(self):
        from flashsale.pay.models import Customer
        if self.unionid:
            c = Customer.objects.filter(unionid=self.unionid).first()
            if c:
                return c.id
        return 0

    @property
    def note(self):
        if self.status == AppDownloadRecord.UNUSE:
            if self.inner_ufrom == AppDownloadRecord.ACTIVITY:
                return '感谢活动邀请，马上粉你哦～'
            if self.inner_ufrom == AppDownloadRecord.QRCODE:
                return '已扫描二维码，马上粉你哦～'
            if self.inner_ufrom == AppDownloadRecord.REDENVELOPE:
                return '谢谢分享红包，马上粉你！'
            return '下载关联已确认，马上粉你哦～'
        return '通过分享成为你的粉丝～'


def appdownloadrecord_update_fans(sender, instance, created, *args, **kwargs):
    from flashsale.promotion.tasks_activity import task_appdownloadrecord_update_fans
    task_appdownloadrecord_update_fans.delay(instance)

post_save.connect(appdownloadrecord_update_fans, sender=AppDownloadRecord, dispatch_uid="appdownloadrecord_update_fans")


class XLSampleApply(BaseModel):
    """ 试用申请 """
    INACTIVE = 0
    ACTIVED = 1
    STATUS_CHOICES = (
        (INACTIVE, u'未激活'),
        (ACTIVED, u'已激活'),
    )
    FROM_WXAPP = 'wxapp'
    FROM_PYQ = 'pyq'
    FROM_QQ = 'qq'
    FROM_WB = 'sinawb'
    FROM_WEB = 'web'
    FROM_QQSPA = 'qqspa'
    XLMM_APP = 'app'

    FROM_CHOICES = (
        (FROM_WXAPP, u'微信好友'),
        (FROM_PYQ, u'朋友圈'),
        (FROM_QQ, u'QQ'),
        (FROM_WB, u'新浪微博'),
        (FROM_WEB, u'外部网页'),
        (XLMM_APP, u'小鹿美美APP')
    )

    outer_id = models.CharField(max_length=32, null=False, blank=True, verbose_name=u'商品编码')
    sku_code = models.CharField(max_length=32, null=False, blank=True, verbose_name=u'SKU编码')
    event_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name=u'活动ID')
    from_customer = models.BigIntegerField(null=True, blank=True, db_index=True, verbose_name=u'分享人用户ID')
    ufrom = models.CharField(max_length=8, choices=FROM_CHOICES, blank=True, verbose_name=u'来自平台')
    user_openid = models.CharField(max_length=28, db_index=True, blank=True, null=True, verbose_name=u'用户openid')
    user_unionid = models.CharField(max_length=64, db_index=True, blank=True, null=True, verbose_name=u'用户unionid')
    mobile = models.CharField(max_length=11, null=False, db_index=True, blank=False, verbose_name=u'试用手机')
    vipcode = models.CharField(max_length=16, db_index=True, blank=True, null=True, verbose_name=u'试用邀请码')
    event_imei = models.CharField(max_length=64, verbose_name=u'设备标识号')
    status = models.IntegerField(default=INACTIVE, choices=STATUS_CHOICES, db_index=True, verbose_name=u"状态")

    customer_id = models.IntegerField(null=True, blank=True, verbose_name=u"申请者ID")
    headimgurl = models.CharField(max_length=256, null=False, blank=True, verbose_name=u'头图')
    nick = models.CharField(max_length=32, null=False, blank=True, verbose_name=u'昵称')

    class Meta:
        db_table = 'flashsale_promotion_sampleapply'
        app_label = 'promotion'
        verbose_name = u'推广/试用申请'
        verbose_name_plural = u'推广/试用申请列表'

    def is_activated(self):
        return self.status == self.ACTIVED

from django.db import connection


def handler_event_imei_unique():
    """
    XLSampleApply　model 处理　-->  event_imei　unique处理

    处理方法：
    1. 添加普通字段
    2. 给历史数据生成唯一记录的　event_imei　字段　event_id + '_' + id
    3. sql 添加 unique 到　event_imei　字段
    """
    sql = "UPDATE flashsale_promotion_sampleapply " \
          "SET " \
          "event_imei = CONCAT('3_', id) " \
          "WHERE id != 0; " \
          "ALTER TABLE flashsale_promotion_sampleapply ADD UNIQUE (event_imei);"
    cursor = connection.cursor()
    cursor.execute(sql)
    cursor.close()


def generate_red_envelope(sender, instance, created, *args, **kwargs):
    if not instance.is_activated():
        return

    from flashsale.promotion.tasks_activity import task_generate_red_envelope
    task_generate_red_envelope.delay(instance)


post_save.connect(generate_red_envelope, sender=XLSampleApply, dispatch_uid="sampleapply_generate_red_envelope")


def update_appdownloadrecord(sender, instance, created, *args, **kwargs):
    # We only update downloadrecord if unionid or mobile exists.
    if instance.user_unionid or instance.mobile:
        from flashsale.promotion.tasks_activity import task_sampleapply_update_appdownloadrecord
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


class RedEnvelope(BaseModel):
    STATUS = ((0, 'new'), (1, 'open'))
    TYPE_CHOICES = ((0, 'cash'), (1, 'card'))

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
        app_label = 'promotion'
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


def envelope_create_budgetlog(sender, instance, created, *args, **kwargs):
    if not created:
        return
    from flashsale.promotion.tasks_activity import task_envelope_create_budgetlog
    task_envelope_create_budgetlog.delay(instance)


post_save.connect(envelope_create_budgetlog, sender=RedEnvelope)


def open_envelope_update_budgetlog(sender, instance, created, *args, **kwargs):
    if not instance.is_cashable():
        return
    from flashsale.promotion.tasks_activity import task_envelope_update_budgetlog
    task_envelope_update_budgetlog.delay(instance)


post_save.connect(open_envelope_update_budgetlog, sender=RedEnvelope)


def open_envelope_decide_awardwinner(sender, instance, created, *args, **kwargs):
    if not instance.is_card_open():
        return
    from flashsale.promotion.tasks_activity import task_decide_award_winner
    task_decide_award_winner.delay(instance)


post_save.connect(open_envelope_decide_awardwinner, sender=RedEnvelope)


class AwardWinner(BaseModel):
    STATUS = ((0, '未领取'), (1, '已领取'), (2, '已作废'))
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
        app_label = 'promotion'
        verbose_name_plural = u'活动/中奖列表'


class XLSampleOrder(BaseModel):
    """ 正式试用订单 """

    xlsp_apply = models.IntegerField(db_index=True, verbose_name=u'试用申请id', default=0, blank=True)
    customer_id = models.CharField(max_length=64, db_index=True, verbose_name=u"用户ID")
    outer_id = models.CharField(max_length=32, null=False, blank=True, verbose_name=u'商品编码')
    sku_code = models.CharField(max_length=32, null=False, blank=True, verbose_name=u'SKU编码')
    vipcode = models.CharField(max_length=16, null=False, db_index=True, blank=False, verbose_name=u'试用邀请码')
    problem_score = models.IntegerField(default=0, verbose_name=u"答题分数")
    status = models.IntegerField(default=0, db_index=True, verbose_name=u"中奖批次")
    award_status = models.BooleanField(default=False, db_index=True, verbose_name="领取奖品")

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

        from flashsale.coupon.apis.v1.usercoupon import create_user_coupon
        from flashsale.pay import constants
        create_user_coupon(customer_id=int(self.customer_id), coupon_template_id=constants.COUPON_ID_FOR_20160223_AWARD)


class ReadPacket(BaseModel):
    """ 红包记录 """

    EXCHANGE = 1
    NOT_EXCHANGE = 0
    EXCHANGE_STATUS = ((EXCHANGE, u'已打开'), (NOT_EXCHANGE, u'未打开'))

    TYPE_CHOICES = ((0, 'cash'), (1, 'card'))

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
