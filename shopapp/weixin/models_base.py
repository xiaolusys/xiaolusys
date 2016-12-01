# -*- coding:utf-8 -*-
from datetime import datetime
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, pre_save

from core.models import BaseModel
from core.fields import JSONCharMyField
from flashsale.xiaolumm.models import XiaoluMama
from shopback.monitor.models import XiaoluSwitch


class WeixinUnionID(BaseModel):
    openid = models.CharField(max_length=32, verbose_name=u'OPENID')
    app_key = models.CharField(max_length=24, verbose_name=u'APPKEY')
    unionid = models.CharField(max_length=32, verbose_name=u'UNIONID')

    class Meta:
        db_table = 'shop_weixin_unionid'
        unique_together = [('unionid', 'app_key')]
        index_together = [('openid', 'app_key')]
        app_label = 'weixin'
        verbose_name = u'微信用户授权ID'
        verbose_name_plural = u'微信用户授权ID列表'

    def __unicode__(self):
        return u'<%s>' % self.openid

    @classmethod
    def get_unionid_by_openid(cls, openid, appkey):
        wxunoinids = cls.objects.filter(openid=openid, app_key=appkey)
        if wxunoinids.exists():
            return wxunoinids[0].unionid
        return ''

    @classmethod
    def get_openid_by_unionid(cls, unionid, appkey):
        wxunoinids = cls.objects.filter(unionid=unionid, app_key=appkey)
        if wxunoinids.exists():
            return wxunoinids[0].openid
        return ''


class WeixinFans(BaseModel):
    openid = models.CharField(max_length=32, verbose_name=u'OPENID')
    app_key = models.CharField(max_length=24, verbose_name=u'APPKEY')
    unionid = models.CharField(max_length=32, verbose_name=u'UNIONID')
    subscribe = models.BooleanField(default=False, verbose_name=u"订阅该号")
    subscribe_time = models.DateTimeField(blank=True, null=True, verbose_name=u"订阅时间")
    unsubscribe_time = models.DateTimeField(blank=True, null=True, verbose_name=u"取消订阅时间")
    extras = JSONCharMyField(max_length=512, default={'qrscene': '0'}, verbose_name=u'额外参数')

    class Meta:
        db_table = 'shop_weixin_fans'
        unique_together = [('unionid', 'app_key')]
        index_together = [('openid', 'app_key')]
        app_label = 'weixin'
        verbose_name = u'微信公众号粉丝'
        verbose_name_plural = u'微信公众号粉丝列表'

    @classmethod
    def get_openid_by_unionid(cls, unionid, app_key):
        """
        没关注也返回 None
        """
        fans = cls.objects.filter(unionid=unionid, app_key=app_key, subscribe=True).first()
        if fans:
            return fans.openid
        else:
            return None

    @classmethod
    def get_unionid_by_openid_and_appkey(cls, openid, app_key):
        fans = cls.objects.filter(openid=openid, app_key=app_key, subscribe=True).first()
        if fans:
            return fans.unionid
        return None

    def set_qrscene(self, qrscene, force_update=False):
        if not self.extras:
            self.extras = {}
        if not self.get_qrscene() or force_update:
            self.extras['qrscene'] = qrscene.strip()

    def get_qrscene(self):
        qrscene = self.extras.get('qrscene')
        if qrscene and (not qrscene.isdigit()):
            # 如果是订单编号，仍然返回空。
            return ''
        if qrscene == '0' or qrscene == 0:
            return ''
        return qrscene


def weixinfans_update_xlmmfans(sender, instance, created, **kwargs):
    referal_from_mama_id = None
    qrscene = instance.get_qrscene()
    if qrscene and qrscene.isdigit():
        referal_from_mama_id = int(qrscene)
    else:
        return

    if referal_from_mama_id < 1:
        return

    referal_to_unionid = instance.unionid

    from shopapp.weixin.tasks import task_weixinfans_update_xlmmfans
    task_weixinfans_update_xlmmfans.delay(referal_from_mama_id, referal_to_unionid)

post_save.connect(weixinfans_update_xlmmfans,
                  sender=WeixinFans, dispatch_uid='post_save_weixinfans_update_xlmmfans')

def weixinfans_create_awardcarry(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.app_key != settings.WX_PUB_APPID: # 关注小鹿美美有奖励，否则没有
        return
    
    if XiaoluSwitch.is_switch_open(2):
        return

    referal_from_mama_id = None
    qrscene = instance.get_qrscene()
    if qrscene and qrscene.isdigit():
        referal_from_mama_id = int(qrscene)
    elif qrscene:
        # qrscene has content (not digital), we simply return
        return

    from shopapp.weixin.tasks import task_weixinfans_create_subscribe_awardcarry, task_weixinfans_create_fans_awardcarry

    referal_to_unionid = instance.unionid
    task_weixinfans_create_subscribe_awardcarry.delay(referal_to_unionid)
    if referal_from_mama_id >= 1:
        task_weixinfans_create_fans_awardcarry.delay(referal_from_mama_id, referal_to_unionid)

post_save.connect(weixinfans_create_awardcarry,
                  sender=WeixinFans, dispatch_uid='post_save_weixinfans_create_awardcarry')


#def weixinfans_xlmm_newtask(sender, instance, **kwargs):
#    """
#    检测新手任务：　关注公众号“小鹿美美”
#    """
#    from flashsale.xiaolumm.tasks_mama_push import task_push_new_mama_task
#    from flashsale.xiaolumm.tasks_mama_fortune import task_subscribe_weixin_send_award
#    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask
#    from flashsale.pay.models.user import Customer
#
#    fans = instance
#
#    if not fans.subscribe:
#        return
#
#    if fans.app_key != settings.WX_PUB_APPID:
#        return
#
#    customer = Customer.objects.filter(unionid=fans.unionid).first()
#
#    if not customer:
#        return
#
#    xlmm = customer.getXiaolumm()
#
#    if not xlmm:
#        return
#
#    # 取消关注，然后重新关注，不计入
#    fans_record = WeixinFans.objects.filter(
#        unionid=fans.unionid, app_key=settings.WX_PUB_APPID).exists()
#
#    if not fans_record:
#        # 发５元奖励
#        task_subscribe_weixin_send_award.delay(xlmm)
#        # 通知完成任务：
#        task_push_new_mama_task.delay(xlmm, NewMamaTask.TASK_SUBSCRIBE_WEIXIN)
#
#pre_save.connect(weixinfans_xlmm_newtask,
#                 sender=WeixinFans, dispatch_uid='pre_save_weixinfans_xlmm_newtask')


class WeixinTplMsg(BaseModel):
    """
    """
    wx_template_id = models.CharField(max_length=255, verbose_name=u'微信模板ID')
    template_ids = JSONCharMyField(max_length=512, blank=True, default={}, verbose_name=u'模版ID集合')
    content = models.TextField(blank=True, null=True, verbose_name=u'模板内容')
    header = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'模板消息头部')
    footer = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'模板消息尾部')
    status = models.BooleanField(default=True, verbose_name=u"使用")

    class Meta:
        db_table = 'shop_weixin_template_msg'
        app_label = 'weixin'
        verbose_name = u'微信模板消息'
        verbose_name_plural = u'微信模板消息列表'


from core.weixin import signals


def fetch_weixin_userinfo(sender, appid, resp_data, *args, **kwargs):
    from .tasks import task_Update_Weixin_Userinfo
    openid = resp_data.get('openid')
    if not openid or not appid:
        return

        # 只对WEIXIN_APPID的公众号授权抓取用户信息
    if appid != settings.WEIXIN_APPID:
        return

    if resp_data.has_key('access_token'):
        task_Update_Weixin_Userinfo.delay(openid,
                                          accessToken=resp_data.get('access_token'))
    else:
        task_Update_Weixin_Userinfo.delay(openid, userinfo=resp_data)


signals.signal_weixin_snsauth_response.connect(fetch_weixin_userinfo)


class WeixinUserInfo(BaseModel):
    """
    We make sure every weixin user only have one record in this table.
    -- Zifei 2016-04-12
    """
    unionid = models.CharField(max_length=32, unique=True, verbose_name=u'UNIONID')
    nick = models.CharField(max_length=32, blank=True, verbose_name=u'昵称')
    thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u'头像')

    class Meta:
        db_table = 'shop_weixin_userinfo'
        app_label = 'weixin'
        verbose_name = u'微信用户基本信息'
        verbose_name_plural = u'微信用户基本信息列表'

    def __unicode__(self):
        return u'<%s>' % self.nick


class WeixinQRcodeTemplate(BaseModel):
    """
    """
    params = models.TextField(verbose_name=u'模板参数')
    preview_url = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'图片预览链接')
    status = models.BooleanField(default=True, verbose_name=u"使用")

    class Meta:
        db_table = 'shop_weixin_qrcode_templates'
        app_label = 'weixin'
        verbose_name = u'微信二维码模板'
        verbose_name_plural = u'微信二维码模板列表'

    def save(self, *args, **kwargs):
        import hashlib
        from shopapp.weixin.utils import generate_colorful_qrcode
        from core.upload.upload import upload_public_to_remote, generate_public_url
        import simplejson

        params = simplejson.loads(self.params)
        img = generate_colorful_qrcode(params)
        m = hashlib.md5()
        m.update(self.params)
        filepath = 'qrcode/%s.jpg' % m.hexdigest()

        print upload_public_to_remote(filepath, img)
        self.preview_url = generate_public_url(filepath)

        super(WeixinQRcodeTemplate, self).save(*args, **kwargs)
