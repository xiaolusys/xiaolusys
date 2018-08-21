# -*- coding:utf8 -*-
from __future__ import unicode_literals

import time
import json
import datetime
from django.db import models
from core.models import BaseModel
from shopback import paramconfig as pcfg
import logging

logger = logging.getLogger('django.request')

SMS_NOTIFY_POST = 'notify'  # 发货告知
SMS_NOTIFY_DELAY_POST = 's_delay'  # 延迟了 几天发货 发货时候发送短信
SMS_NOTIFY_ACTIVITY = 'activity'  # 活动宣传
SMS_NOTIFY_MAMARENEW   = 'mama_renew'
SMS_NOTIFY_PAYCALL = 'paycall'  # 付款提醒
SMS_NOTIFY_TOCITY = 'tocity'  # 同城提醒

SMS_NOTIFY_SIGN = 'sign'  # 签收提醒
SMS_NOTIFY_BIRTH = 'birth'  # 生日祝福

SMS_NOTIFY_REGISTER_CODE = 'code'  # 注册验证码
SMS_NOTIFY_RESET_PASSWORD = 'reset_code'  # 重置验证码
SMS_NOTIFY_LOGIN_CODE  = 'login_code'  # 登录验证码
SMS_NOTIFY_CASHOUT_CODE = 'cashout_code'  # 提现验证码

SMS_NOTIFY_GOODS_LACK = 'goods_lack'  # 缺货通知提醒
SMS_NOTIFY_LACK_REFUND = 'lackrefund' # 缺货退款通知
SMS_NOTIFY_REFUND_DENY = 'refund_deny'
SMS_NOTIFY_REFUN_APPROVE = 'refund_approve'
SMS_NOTIFY_REFUND_RETURN = 'refund_return'
SMS_NOTIFY_REFUND_OK = 'refund_ok'

SMS_NOTIFY_MAMA_ORDERCARRY = 'ordercarry'  # 小鹿妈妈订单收益
SMS_NOTIFY_APP_UPDATE = 'appupdate'        # APP更新通知
SMS_NOTIFY_MAMA_SUBSCRIBE_WEIXIN = 'sbweixin'  # 提醒妈妈关注微信

SMS_RECORD_STATUS = (
    (pcfg.SMS_CREATED, u'初始创建'),
    (pcfg.SMS_COMMIT, u'任务提交'),
    (pcfg.SMS_COMPLETE, u'任务完成'),
    (pcfg.SMS_ERROR, u'任务出错'),
    (pcfg.SMS_CANCLE, u'任务取消'),
)


def choice_sms_notify_type():
    sms_notify_type = (
        (SMS_NOTIFY_PAYCALL, u'付款提醒'),
        (SMS_NOTIFY_POST, u'发货通知'),
        (SMS_NOTIFY_DELAY_POST, u'延迟发货通知'),

        (SMS_NOTIFY_REGISTER_CODE, u'注册验证码'),
        (SMS_NOTIFY_RESET_PASSWORD, u'重置密码验证码'),
        (SMS_NOTIFY_LOGIN_CODE, u'登录验证码'),
        (SMS_NOTIFY_CASHOUT_CODE, u'提现验证码'),

        (SMS_NOTIFY_GOODS_LACK, u'缺货退款提醒'),
        (SMS_NOTIFY_APP_UPDATE, u'APP更新'),

        (SMS_NOTIFY_LACK_REFUND, u'缺货退款通知'),
        (SMS_NOTIFY_REFUND_DENY, u'拒绝退款申请通知'),
        (SMS_NOTIFY_REFUN_APPROVE, u'同意退款返款通知'),
        (SMS_NOTIFY_REFUND_RETURN, u'同意退货申请通知'),
        (SMS_NOTIFY_REFUND_OK, u'退货退款成功提醒'),

        (SMS_NOTIFY_MAMA_ORDERCARRY, u'妈妈订单收益通知'),
        (SMS_NOTIFY_MAMARENEW, u'妈妈续费提醒'),
        (SMS_NOTIFY_MAMA_SUBSCRIBE_WEIXIN, u'提醒妈妈关注微信'),

        (SMS_NOTIFY_TOCITY, '同城提醒'),
    )
    return sms_notify_type


class SMSPlatform(BaseModel):
    """ 短信服务商 """
    code = models.CharField(max_length=16, verbose_name=u'编码')
    name = models.CharField(max_length=64, verbose_name=u'服务商名称')

    user_id = models.CharField(max_length=32, verbose_name=u'企业ID')
    account = models.CharField(max_length=64, verbose_name=u'帐号')
    password = models.CharField(max_length=64, verbose_name=u'密码')

    remainums = models.IntegerField(default=0, verbose_name=u'剩余条数')
    sendnums = models.IntegerField(default=0, verbose_name=u'已发条数')
    sign_name = models.CharField(max_length=16, blank=True, verbose_name='签名内容')

    is_force_sign = models.BooleanField(default=False, verbose_name='强制签名')
    is_default = models.BooleanField(default=False, verbose_name=u'首选服务商')

    class Meta:
        db_table = 'shop_smsmgr_smsplatform'
        app_label = 'smsmgr'
        verbose_name = u'短信服务商'
        verbose_name_plural = u'短信服务商列表'

    def __unicode__(self):
        return u'<%s>' % (self.code)


class SMSRecord(BaseModel):
    """ 短信平台发送记录 """

    SMS_CREATED  = pcfg.SMS_CREATED
    SMS_COMMIT   = pcfg.SMS_COMMIT
    SMS_COMPLETE = pcfg.SMS_COMPLETE
    SMS_ERROR    = pcfg.SMS_ERROR
    SMS_CANCLE   = pcfg.SMS_CANCLE

    platform = models.ForeignKey(SMSPlatform, null=True, default=None, related_name='sms_records', verbose_name=u'短信服务商')

    task_type = models.CharField(max_length=16, choices=choice_sms_notify_type(), db_index=True, verbose_name=u'类型')
    task_id   = models.CharField(null=True, blank=True, default='', max_length=128, verbose_name=u'服务商返回任务ID')
    task_name = models.CharField(null=True, blank=True, default='', max_length=256, verbose_name=u'任务标题')
    mobiles = models.CharField(max_length=64,  blank=True, default='', db_index=True, verbose_name=u'发送号码')
    content = models.CharField(null=True, blank=True, default='', max_length=1000, verbose_name=u'发送内容')

    sendtime = models.DateTimeField(null=True, blank=True, verbose_name=u'定时发送时间')
    # finishtime = models.DateTimeField(null=True,blank=True,verbose_name='完成时间')

    countnums = models.IntegerField(default=0, verbose_name=u'发送数量')
    mobilenums = models.IntegerField(default=0, verbose_name=u'手机数量')
    telephnums = models.IntegerField(default=0, verbose_name=u'固话数量')
    succnums = models.IntegerField(default=0, verbose_name=u'成功数量')

    retmsg = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'任务返回结果')

    memo = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'备注说明')
    status = models.IntegerField(default=pcfg.SMS_CREATED, db_index=True, choices=SMS_RECORD_STATUS, verbose_name=u'任务返回结果')

    class Meta:
        db_table = 'shop_smsmgr_smsrecord'
        app_label = 'smsmgr'
        verbose_name = u'短信记录'
        verbose_name_plural = u'短信记录列表'

    def __unicode__(self):
        return '<%s,%s,%d,%d>' % (self.platform, self.task_name, self.countnums, self.succnums)


class SMSActivity(BaseModel):
    """ 活动短信模板 """
    NORMAL = True
    DELETE = False

    sms_type = models.CharField(max_length=16, choices=choice_sms_notify_type(), verbose_name=u'类型')
    text_tmpl = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'内容')
    sms_template_code =  models.CharField(max_length=32, blank=True, null=True, verbose_name=u'外部模板编号')
    status = models.BooleanField(default=True, verbose_name=u"使用")

    class Meta:
        db_table = 'shop_smsmgr_activity'
        app_label = 'smsmgr'
        verbose_name = u'短信模板'
        verbose_name_plural = u'短信模板列表'

    def __unicode__(self):
        return str(self.id)

    def render_to_message(self, kwargs):
        return self.text_tmpl.format(**kwargs)
