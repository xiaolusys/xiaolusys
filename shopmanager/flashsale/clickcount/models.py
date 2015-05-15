# -*- coding:utf-8 -*-
from django.db import models


class ClickCount(models.Model):
    
    linkid = models.IntegerField(verbose_name=u'链接ID')
    weikefu = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'微客服')
    agencylevel = models.IntegerField(default=1, verbose_name=u"类别")
    mobile = models.CharField(max_length=11, verbose_name=u"手机")
    
    user_num = models.IntegerField(default=0, verbose_name=u'人数')
    valid_num = models.IntegerField(default=0, verbose_name=u'有效点击人数')
    click_num = models.IntegerField(default=0, verbose_name=u'次数')
    date = models.DateField(verbose_name=u'日期')
    write_time = models.DateTimeField(auto_now_add=True, verbose_name=u'写入时间')
    username = models.IntegerField(default=0, db_index=True, verbose_name=u'接管人')

    class Meta:
        db_table = 'flashsale_clickcount'
        unique_together = ('date', 'linkid')  # 联合索引
        app_label = 'xiaolumm'
        verbose_name = u'点击统计表'
        verbose_name_plural = u'点击统计表列表'
        ordering=['-date','-user_num','-click_num']

    def __unicode__(self):
        return self.weikefu
