# coding=utf-8
"""
推送消息内容model
"""
from core.models import BaseModel
from django.db import models


class PushMsgTpl(BaseModel):
    """推送消息模板"""
    name = models.CharField(max_length=64, verbose_name=u'模板名称')
    tpl_content = models.CharField(max_length=128, verbose_name=u'推送消息模板')
    is_valid = models.BooleanField(db_index=True, default=False, verbose_name=u'是否有效')

    class Meta:
        db_table = 'push_msg_tpl'
        app_label = 'push'
        verbose_name = u'推送/推送信息模板表'
        verbose_name_plural = u'推送/推送信息模板列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.tpl_content)

    def get_emoji_content(self, abs_content=None):
        """　获取含emoji的内容 """
        from flashsale.xiaolumm.util_emoji import gen_emoji, match_emoji

        message = match_emoji(abs_content) if abs_content else match_emoji(self.tpl_content)
        return message
