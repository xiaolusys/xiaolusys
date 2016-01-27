# coding=utf-8
from django.db import models


class Activities(models.Model):
    """ 活动记录　"""
    title = models.CharField(max_length=128, verbose_name=u"活动标题")
    explain = models.TextField(max_length=10240, verbose_name=u"活动说明")
    start_time = models.DateTimeField(blank=True, null=True, verbose_name=u"开始时间")
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u"结束时间")
    memo = models.TextField(max_length=10240, blank=True, null=True, verbose_name=u'活动备注')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u"创建时间")

    class Meta:
        db_table = 'flashsale_activities'
        verbose_name = u'特卖活动表'
        verbose_name_plural = u'特卖活动列表'

    def __unicode__(self):
        return '%s-%s' % (self.id, self.title)


class Participation(models.Model):
    """
    活动参与 activitiy 是活动记录的id; 用户绑定的是微信用户列表中的id；活动结果表示参与是否成功是否发放福利或其他.
    """
    activity = models.IntegerField(db_index=True, verbose_name=u"活动种类")
    weixinid = models.IntegerField(db_index=True, verbose_name=u"微信用户ID")
    phone_no = models.CharField(max_length=11, verbose_name=u"参与手机号")
    activation_code = models.CharField(max_length=32, unique=True, verbose_name=u'激活码')
    result = models.BooleanField(default=False, verbose_name=u"活动结果")
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u"参与时间")

    class Meta:
        db_table = 'flahsale_activity_participation'
        verbose_name = u'活动参与表'
        verbose_name_plural = u'活动参与列表'

    def __unicode__(self):
        return '%s-%s' % (self.id, self.weixinid)


class ParticipateDetail(models.Model):
    """
    参与细节 participation 是参与活动记录的id;　记录参与者参与对应活动的多条关键影响因素，比如邀请多少人下载，多少手机号来验证
    各明细内容字段可以为空　后来添加的明细内容字段也可以为空　创建记录的时候不一定有该字段
    """
    participation = models.IntegerField(db_index=True, verbose_name=u"参与记录号")
    verify_phone = models.CharField(blank=True, null=True, max_length=11, verbose_name=u"验证手机号码")
    is_activate = models.BooleanField(default=False, verbose_name=u'APP激活')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'flahsale_participation_detail'
        verbose_name = u'参与明细表'
        verbose_name_plural = u'参与明细列表'

    def __unicode__(self):
        return '%s-%s' % (self.id, self.participation)


