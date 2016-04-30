# coding=utf-8
from django.db import models
from core.models import BaseModel
from django.db.models.signals import post_save
from django.conf import settings

import datetime, urlparse


def get_choice_name(choices, val):
    """
    iterate over choices and find the name for this val
    """
    name = ""
    for entry in choices:
        if entry[0] == val:
            name = entry[1]
    return name




class LessonTopic(BaseModel):
    STATUS_TYPES = ((0, u'有效'), (1, u'取消'))
    LESSON_TYPES = ((0, u'课程'), (1, u'实战'), (2, u'知识'))

    title = models.CharField(max_length=128, blank=True, verbose_name=u'课程主题')
    description = models.TextField(max_length=512, blank=True, verbose_name=u'课程描述')

    num_attender = models.IntegerField(default=0, verbose_name=u'总听课人数')
    content_link = models.CharField(max_length=256, blank=True, verbose_name=u'内容链接')

    lesson_type = models.IntegerField(default=0, choices=LESSON_TYPES, verbose_name=u'类型')
    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态')

    @property
    def lesson_type_display(self):
        return get_choice_name(LessonTopic.LESSON_TYPES, self.lesson_type)

    @property
    def status_display(self):
        return get_choice_name(LessonTopic.STATUS_TYPES, self.status)
    
    class Meta:
        db_table = 'flashsale_xlmm_lesson_topic'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿大学/课程主题'
        verbose_name_plural = u'小鹿大学/课程主题列表'

    def __unicode__(self):
        return "%s:%s" % (self.lesson_type, self.title)

    
class Instructor(BaseModel):
    STATUS_TYPES = ((0, u'有效'), (1, u'取消'))

    name = models.CharField(max_length=32, blank=True, verbose_name=u'讲师昵称')
    title = models.CharField(max_length=64, blank=True, verbose_name=u'讲师头衔')
    image = models.CharField(max_length=256, blank=True, verbose_name=u'讲师头像')
    introduction = models.TextField(max_length=512, blank=True, verbose_name=u'讲师简介')

    num_lesson = models.IntegerField(default=0, verbose_name=u'总课时')
    num_attender = models.IntegerField(default=0, verbose_name=u'总听课人数')
    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态')
    
    class Meta:
        db_table = 'flashsale_xlmm_instructor'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿大学/资深讲师'
        verbose_name_plural = u'小鹿大学/资深讲师列表'

    def __unicode__(self):
        return "%s:%s" % (self.name, self.title)


class Lesson(BaseModel):
    STATUS_TYPES = ((0, u'有效'), (1, u'已完成'), (2, u'取消'))
    
    lesson_topic_id = models.IntegerField(default=0, db_index=True, verbose_name=u'课程主题ID')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'课程主题')
    description = models.TextField(max_length=512, blank=True, verbose_name=u'课程描述')
    content_link = models.CharField(max_length=256, blank=True, verbose_name=u'内容链接')

    instructor_id = models.IntegerField(default=0, db_index=True, verbose_name=u'讲师ID')
    instructor_name = models.CharField(max_length=32, blank=True, verbose_name=u'讲师昵称')
    instructor_title = models.CharField(max_length=64, blank=True, verbose_name=u'讲师头衔')
    instructor_image = models.CharField(max_length=256, blank=True, verbose_name=u'讲师头像')
    
    num_attender = models.IntegerField(default=0, verbose_name=u'听课人数')
    num_score = models.IntegerField(default=0, verbose_name=u'课程评分')
    start_time = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name=u'开始时间')
    qrcode_link = models.CharField(max_length=256, blank=True, verbose_name=u'群二维码链接')
    
    # uni_key: lesson_topic_id + instructor_id + start_time
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    
    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态')

    @property
    def status_display(self):
        return get_choice_name(Lesson.STATUS_TYPES, self.status)

    @property
    def start_time_display(self):
        year = self.start_time.year
        month = self.start_time.month
        day = self.start_time.day
        hour = self.start_time.hour
        minute = self.start_time.minute

        return "%02d月%02d日 %02d:%02d" % (month,day,hour,minute)

    @property
    def is_started(self):
        if datetime.datetime.now() > self.start_time and self.status == 0:
            return 1
        return 0
            
    class Meta:
        db_table = 'flashsale_xlmm_lesson'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿大学/课程'
        verbose_name_plural = u'小鹿大学/课程列表'

    def __unicode__(self):
        return "%s:%s:%s" % (self.title, self.instructor_name, self.start_time)

    
class AttendRecord(BaseModel):
    STATUS_TYPES = ((0, u'EFFECT'), (1, u'CANCELED'))
    
    lesson_id = models.IntegerField(default=0, db_index=True, verbose_name=u'课程ID')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'课程主题')

    student_unionid = models.CharField(max_length=64, db_index=True, verbose_name=u"学员UnionID")
    student_nick = models.CharField(max_length=64, verbose_name=u"学员昵称")
    student_image = models.CharField(max_length=256, verbose_name=u"学员头像")
    
    num_score = models.IntegerField(default=0, verbose_name=u'课程评分')
    
    # uni_key = lesson_id + student_unionid
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u"唯一ID")

    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态')
    
    class Meta:
        db_table = 'flashsale_xlmm_attend_record'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿大学/课程学员'
        verbose_name_plural = u'小鹿大学/课程学员列表'

    def __unicode__(self):
        return "%s:%s" % (self.lesson_id, self.student_nick)
