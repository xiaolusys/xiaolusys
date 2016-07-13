# coding=utf-8
import datetime
from core.models import BaseModel
from django.db import models
from core.fields import JSONCharMyField
from django.contrib.auth.models import User
from flashsale.promotion.models import ActivityEntry


# class Activity(BaseModel):
#     """
#         分离微信群和活动报名
#     """
#
#     class Meta:
#         app_label = 'weixingroup'
#         verbose_name = u'活动'
#         verbose_name_plural = u'活动列表'
#
#     name = models.CharField(max_length=100)
#     begin_time = models.DateTimeField()
#     end_time = models.DateTimeField()
#     content = models.CharField(max_length=1000, verbose_name=u'活动内容', help_text=u'详细介绍说明')
#     desc = models.CharField(max_length=500, verbose_name=u'描述', help_text=u'可能展现给用户的描述')
#     note = models.CharField(max_length=200, verbose_name=u'备注', help_text=u'展示给普通用户的说明')
#     homepage = models.CharField(max_length=512, verbose_name=u'活动主页')
#     pages = JSONCharMyField(max_length=10240, null=True, verbose_name=u'相关页面', help_text=u'冗余的订货单关联')
#     STATUS_CHOICES = ((0, u'初始'),
#                       (1, u'有效'),
#                       (2, u'作废'),)
#     status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name=u'状态')
#
#     def join(self, user_id, group_id):
#         au = ActivityUsers.objects.filter(activity=self, user_id=user_id).first()
#         if not au:
#             au = ActivityUsers(activity=self,
#                                user_id=user_id,
#                                group_id=group_id)
#             au.save()
#         elif au.group_id == group_id:
#             au.group_id = group_id
#             au.save()
#
#     def has_joined(self, user_id):
#         return ActivityUsers.objects.filter(user_id=user_id).exists()
#
#     @staticmethod
#     def init_liangxi():
#         Activity(name="LIANGXI",
#                      begin_time=datetime.datetime(2016, 7, 13),
#                      end_time=datetime.datetime(2016, 7, 14),
#                      content=u'凉席活动流程说明',
#                      desc=u"凉席活动对外描述",
#                      note="",
#                      homepage="").save()


class ActivityUsers(BaseModel):
    class Meta:
        app_label = 'weixingroup'
        verbose_name = u'活动'
        verbose_name_plural = u'活动列表'

    activity = models.ForeignKey(ActivityEntry)
    user_id = models.IntegerField()
    group = models.ForeignKey('GroupMamaAdministrator')
