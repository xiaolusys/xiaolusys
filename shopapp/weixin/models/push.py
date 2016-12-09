# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models
from core.models import BaseModel
from core.fields import JSONCharMyField

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