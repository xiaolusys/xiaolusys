# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import hashlib
from django.db import models, transaction
from django.dispatch import receiver
from django.utils.functional import cached_property

from signals.jimay import signal_jimay_agent_enrolled

class JimayAgent(models.Model):

    LEVEL_SPE = 0
    LEVEL_CIT = 1
    LEVEL_PRO = 2
    LEVEL_TOP = 3
    LEVEL_CHOICES = (
        (LEVEL_TOP, '总代'),
        (LEVEL_PRO, '省代'),
        (LEVEL_CIT, '市代'),
        (LEVEL_SPE, '特约'),
    )

    nick = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='昵称')

    name = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='姓名')
    idcard_no = models.CharField(max_length=18, blank=True, verbose_name='身份证号')

    weixin = models.CharField(max_length=24, db_index=True, blank=True, verbose_name='微信')
    mobile = models.CharField(max_length=11, unique=True, blank=True, verbose_name='手机')
    level = models.IntegerField(default=LEVEL_SPE, choices=LEVEL_CHOICES, db_index=True, verbose_name='级别')

    parent_agent_id = models.IntegerField(default=0, db_index=True, verbose_name='父级特约代理ID')

    address = models.CharField(max_length=128, blank=True, verbose_name='收货地址')

    certification = models.CharField(max_length=256, blank=True, verbose_name='证书地址', help_text='暂不使用链接')

    unionid = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='UNIONID'
                               ,help_text='微信unionid')

    manager = models.CharField(max_length=24, db_index=True, blank=True, verbose_name='管理员')
    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name='修改日期')

    class Meta:
        db_table = 'jimay_agent'
        app_label = 'jimay'
        verbose_name = '己美医学/特约代理'
        verbose_name_plural = '己美医学/特约代理'

    def __unicode__(self):
        return '%s,%s' % (self.id, self.name)

    def gen_certification_filename(self):
        agent_key_str =  '%s-%s-%s-%s' % (self.name, self.idcard_no, self.weixin, self.level)
        sha1_str = hashlib.sha1(agent_key_str).hexdigest()
        return '{mobile}-{sha1}'.format(mobile=self.mobile, sha1=sha1_str)

    @cached_property
    def buyer(self):
        from flashsale.pay.models import Customer
        return Customer.objects.filter(mobile=self.mobile).order_by('status', '-unionid').first()

    @cached_property
    def parent_agent(self):
        if self.parent_agent_id > 0:
            return JimayAgent.objects.filter(id=self.parent_agent_id).first()
        return None

    @cached_property
    def is_purchase_enable(self):
        """ 如果没有上级就允许直接订货 """
        return self.parent_agent_id == 0

    def set_certification(self, certification_url):
        self.certification = certification_url

    def action_enroll(self, time_enrolled):
        """ 代理注册 """
        transaction.on_commit(lambda : signal_jimay_agent_enrolled.send_robust(
            sender=JimayAgent,
            obj=self,
            time_enrolled=time_enrolled
        ))

    def save(self, *args, **kwargs):
        resp = super(JimayAgent, self).save(*args, **kwargs)
        self.action_enroll(self.created)
        return resp


@receiver(signal_jimay_agent_enrolled, sender=JimayAgent, dispatch_uid='jimay_agent_enroll_update_stat')
def jimay_agent_enroll_update_stat(sender, obj, time_enrolled, **kwargs):

    from .stat import JimayAgentStat
    if obj.parent_agent:
        JimayAgentStat.calc_direct_invite_num_by_agent(obj.parent_agent)
        JimayAgentStat.calc_indirect_invite_num_by_agent(obj.parent_agent)
