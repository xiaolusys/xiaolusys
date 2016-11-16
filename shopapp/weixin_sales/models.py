# -*- coding:utf8 -*-
from __future__ import unicode_literals

import datetime
from django.db import models


class WeixinUserPicture(models.Model):
    SHARE = 'SDPP'
    COMMENT = 'HPPP'
    MATCH = 'BBPP'
    OTHER = 'OTHER'

    PIC_STATUS = ((SHARE, u'晒单截图'),
                  (COMMENT, u'好评截图'),
                  (MATCH, u'宝宝秀'),
                  (OTHER, u'其它'),)

    APPLY = 0
    COMPLETE = 1
    INVALID = 2

    PICTURE_STATUS = ((APPLY, u'申请中'),
                      (COMPLETE, u'已提交'),
                      (INVALID, u'已取消'),)

    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"用户ID")

    mobile = models.CharField(max_length=12, db_index=True, blank=True, verbose_name=u"手机")

    pic_url = models.URLField(max_length=1024, blank=True, verbose_name=u'图片URL')
    pic_type = models.CharField(max_length=8, choices=PIC_STATUS, default=OTHER, verbose_name=u'图片类型')
    pic_num = models.IntegerField(default=0, verbose_name=u'图片张数')

    upload_ended = models.DateTimeField(blank=True, null=True, verbose_name=u'上传有效时间')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    status = models.IntegerField(choices=PICTURE_STATUS, default=APPLY, verbose_name=u'状态')

    class Meta:
        db_table = 'shop_weixin_user_picture'
        app_label = 'weixin'
        verbose_name = u'微信用户图片'
        verbose_name_plural = u'微信用户图片列表'

    def __unicode__(self):
        return self.get_pic_type_display()


class WeixinUserAward(models.Model):
    user_openid = models.CharField(max_length=64, unique=True, verbose_name=u"申请人ID")
    referal_from_openid = models.CharField(max_length=64, db_index=True,
                                           blank=True, verbose_name=u"邀请人ID")

    is_receive = models.BooleanField(default=False, verbose_name=u"领取")
    is_share = models.BooleanField(default=False, verbose_name=u"发送")

    is_notify = models.BooleanField(default=False, verbose_name=u"提醒通知")

    remind_count = models.IntegerField(default=0, verbose_name=u"提醒次数")
    remind_time = models.DateTimeField(blank=True, null=True, verbose_name=u'提醒时间')

    select_val = models.IntegerField(default=0, verbose_name=u"选择值")
    award_val = models.IntegerField(default=0, verbose_name=u"奖励值")

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    class Meta:
        db_table = 'shop_weixin_user_award'
        app_label = 'weixin'
        verbose_name = u'微信邀请奖励'
        verbose_name_plural = u'微信邀请奖励列表'

    def __unicode__(self):
        return self.user_openid


from django.db import transaction
from shopapp.signals import weixin_referal_signal
from shopapp.weixin.models import WeiXinUser, WeixinScoreItem, WeixinUserScore


# 推荐关系增加积分
@transaction.atomic
def convert_awardreferal2score(sender, user_openid, referal_from_openid, *args, **kwargs):
    transaction.commit()
    invite_score = 1

    wx_user = WeiXinUser.objects.get(openid=user_openid)
    if not wx_user.referal_from_openid:
        wx_user.referal_from_openid = referal_from_openid
        wx_user.save()

    WeixinScoreItem.objects.create(user_openid=referal_from_openid,
                                   score=invite_score,
                                   score_type=WeixinScoreItem.INVITE,
                                   expired_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                   memo=u"邀请好友(%s)获得积分。" % (user_openid))

    wx_user_score, state = WeixinUserScore.objects.get_or_create(user_openid=referal_from_openid)
    wx_user_score.user_score = models.F('user_score') + invite_score
    wx_user_score.save()


weixin_referal_signal.connect(convert_awardreferal2score, sender=WeixinUserAward)


class WeixinLinkClicks(models.Model):
    SAMPLE_LINK = 'sample'
    SALE_LINK = 'sale'
    LINK_TYPE_CHOICES = (
        (SAMPLE_LINK, u'试用链接'),
        (SALE_LINK, u'特卖链接'))

    user_openid = models.CharField(max_length=64, verbose_name=u"OPEN ID")

    link_url = models.CharField(max_length=128, db_index=True, blank=True, verbose_name=u'分享链接')
    link_type = models.CharField(max_length=8, choices=LINK_TYPE_CHOICES
                                 , db_index=True, default=SAMPLE_LINK, verbose_name=u'链接类型')

    clicker_num = models.IntegerField(default=0, verbose_name=u"点击人数")
    click_count = models.IntegerField(default=0, verbose_name=u"点击次数")

    validated_in = models.IntegerField(default=0, verbose_name=u"有效间隔(s)")

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    class Meta:
        db_table = 'shop_weixin_sale_linkclicks'
        unique_together = ("user_openid", "link_url", "link_type")
        app_label = 'weixin'
        verbose_name = u'微信分享点击'
        verbose_name_plural = u'微信分享点击列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.link_url, self.click_count)


from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from shopapp.weixin.models import SampleOrder


def create_weixin_link_click(sender, instance, *args, **kwargs):
    user_openid = instance.user_openid
    try:
        wx_user = WeiXinUser.objects.get(openid=user_openid)
        link_url = reverse('weixin_sampleads', args=(wx_user.pk,))

        wlc, state = WeixinLinkClicks.objects.get_or_create(
            user_openid=user_openid,
            link_url=link_url,
            link_type=WeixinLinkClicks.SAMPLE_LINK)


    except Exception, exc:
        import logging
        logger = logging.getLogger("django.request")
        logger.error(u'分享记录错误:%s' % exc.message, exc_info=True)


post_save.connect(create_weixin_link_click, sender=SampleOrder)


class WeixinLinkClickRecord(models.Model):
    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"申请人ID")

    link_url = models.CharField(max_length=128, db_index=True, verbose_name=u"点击链接")

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    class Meta:
        db_table = 'shop_weixin_sale_clickrecord'
        app_label = 'weixin'
        verbose_name = u'微信点击记录'
        verbose_name_plural = u'微信点击记录列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.user_openid, self.link_url)


class WeixinLinkShare(models.Model):
    APP_LINK = 'APP'
    PYQ_LINK = 'PYQ'
    QQ_LINK = 'QQ'
    WB_LINK = 'WB'

    SHARE_TYPE_CHOICES = (
        (APP_LINK, u'微信好友'),
        (PYQ_LINK, u'朋友圈'),
        (QQ_LINK, u'QQ'),
        (WB_LINK, u'微博'),)

    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"OPEN ID")

    link_url = models.CharField(max_length=128, db_index=True, blank=True, verbose_name=u'分享链接')
    link_type = models.CharField(max_length=8, choices=SHARE_TYPE_CHOICES
                                 , db_index=True, verbose_name=u'分享类型')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    class Meta:
        db_table = 'shop_weixin_sale_linkshare'
        app_label = 'weixin'
        verbose_name = u'微信分享链接'
        verbose_name_plural = u'微信分享链接列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.link_url, self.link_type)
