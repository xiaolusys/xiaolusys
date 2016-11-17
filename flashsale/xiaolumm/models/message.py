# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from core.models import AdminModel, BaseModel
from django.db.models import Q
from django.db.models.signals import post_save
from flashsale.xiaolumm.models import XiaoluMama

import logging
logger = logging.getLogger('django.request')


class XlmmMessage(AdminModel):
    title = models.CharField(max_length=500, verbose_name=u'消息标题')
    content_link = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'内容链接', help_text=u'优先使用消息链接')
    content = models.CharField(max_length=512, blank=True, verbose_name=u'消息内容')
    dest = models.CharField(max_length=10000, null=True, blank=True, verbose_name=u'接收人',
                            help_text=u'null表示发给了所有小鹿妈妈;否则填写django orm查询条件字典json')
    STATUS_CHOICES = ((0, u'无效'), (1, u'有效'))
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name=u'状态')

    class Meta:
        app_label = 'xiaolumm'
        db_table = 'xiaolumm_message'
        verbose_name = u'妈妈消息/通知'
        verbose_name_plural = u'妈妈消息/通知列表'

    @property
    def read_count(self):
        return self.rel_messages.all().count()
        
    @property
    def read(self):
        if not hasattr(self, '_read_'):
            return False
        return self._read_

    @staticmethod
    def get_msg_list(mama_id, limit_time=None, begin=None, end=None):
        """
            优先最新未读消息，老的已读放后头。

        :param mama_id:
        :return:
        """
        queryset = XlmmMessage.objects.filter(status=1).filter(Q(dest=None) | Q(dest__in=['', str(mama_id)])).order_by('-id')
        rel_queryset = XlmmMessageRel.objects.filter(mama_id=mama_id, read=True)
        if limit_time:
            queryset = queryset.filter(created__gt=limit_time)
            rel_queryset = rel_queryset.filter(created__gt=limit_time)
        messages = {r.message_id: r.read for r in rel_queryset}
        if not begin and not end:
            # 无需分页
            res1 = list(queryset.exclude(id__in=messages.keys()))
            res2 = list(queryset.filter(id__in=messages.keys()))
            unread_cnt = queryset.exclude(id__in=messages.keys()).count()
            for r in res2:
                r._read_ = True
            return res1 + res2, unread_cnt
        else:
            # todo@hy 分页
            cnt = queryset.exclude(id__in=messages.keys()).count()

        return

    @staticmethod
    def set_all_read(mama):
        queryset = XlmmMessage.objects.filter(status=1).filter(Q(dest=None) | Q(dest__in=['', str(mama.id)])).order_by('-id')
        for q in queryset:
            q.set_read(mama)

    def set_read(self, mama):
        rel = mama.rel_messages.filter(message_id=self.id).first()
        if not rel:
            rel = XlmmMessageRel(message=self, mama=mama, read=True)
            rel.save()
        else:
            rel.read = True
            rel.save()


class XlmmMessageRel(BaseModel):
    message = models.ForeignKey(XlmmMessage, related_name='rel_messages')
    mama = models.ForeignKey(XiaoluMama, related_name='rel_messages', verbose_name=u'接受者')
    read = models.BooleanField(default=True, verbose_name=u'状态')

    class Meta:
        unique_together = ('mama', 'message')
        app_label = 'xiaolumm'
        db_table = 'xiaolumm_message_rel'
        verbose_name = u'妈妈消息/阅读状态'
        verbose_name_plural = u'妈妈消息/阅读状态列表'


def read_stats(sender, instance, created, **kwargs):
    from django_statsd.clients import statsd
    read_count = XlmmMessageRel.objects.filter(message=instance.message).count()
    key = "MamaNotificationMessage.%d" % instance.message.id
    statsd.timing(key, read_count)
    #logger.error("read_stats: %s, %d" % (key, read_count))

post_save.connect(read_stats, sender=XlmmMessageRel, dispatch_uid='post_save_xlmmmessagerel_read_stats')
