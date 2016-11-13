# coding=utf-8
from django.db import models
from core.models import BaseModel
from core.fields import JSONCharMyField
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
    STATUS_EFFECT = 1
    STATUS_CANCELED = 2
    STATUS_TYPES = ((STATUS_EFFECT, u'有效'), (STATUS_CANCELED, u'取消'))

    LESSON_NEWEST_COURSE = 3
    LESSON_COURSE = 0
    LESSON_PRACTICE = 1
    LESSON_KNOWLEDGE = 2
    LESSON_TYPES = ((LESSON_NEWEST_COURSE, u'基础课程'), (LESSON_COURSE, u'课程'),
                    (LESSON_PRACTICE, u'实战'), (LESSON_KNOWLEDGE, u'知识'))

    title = models.CharField(max_length=128, blank=True, verbose_name=u'课程主题')
    cover_image = models.CharField(max_length=256, blank=True, verbose_name=u'课程封面图')
    description = models.TextField(max_length=512, blank=True, verbose_name=u'课程描述')

    num_attender = models.IntegerField(default=0, verbose_name=u'总听课人数')
    content_link = models.CharField(max_length=256, blank=True, verbose_name=u'内容链接')

    lesson_type = models.IntegerField(default=0, choices=LESSON_TYPES, verbose_name=u'类型')
    is_show = models.BooleanField(default=False, db_index=True, verbose_name=u'是否显示')
    status = models.IntegerField(default=1, choices=STATUS_TYPES, verbose_name=u'状态')
    order_weight = models.IntegerField(default=1, db_index=True, verbose_name=u'排序值')
    click_num = models.IntegerField(default=0, db_index=True, verbose_name=u'点击数')

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
    STATUS_EFFECT = 1
    STATUS_PENDING = 2
    STATUS_DISABLED = 3
    STATUS_TYPES = ((STATUS_EFFECT, u'审核合格'), (STATUS_PENDING, u'待审核'), (STATUS_DISABLED, u'取消'))

    name = models.CharField(max_length=32, blank=True, verbose_name=u'讲师昵称')
    title = models.CharField(max_length=64, blank=True, verbose_name=u'讲师头衔')
    image = models.CharField(max_length=256, blank=True, verbose_name=u'讲师头像')
    introduction = models.TextField(max_length=512, blank=True, verbose_name=u'讲师简介')

    mama_id = models.IntegerField(default=0, unique=True, verbose_name=u'Mama ID')
    num_lesson = models.IntegerField(default=0, verbose_name=u'总课时')
    num_attender = models.IntegerField(default=0, verbose_name=u'总听课人数')
    status = models.IntegerField(default=STATUS_PENDING, choices=STATUS_TYPES, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_xlmm_instructor'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿大学/资深讲师'
        verbose_name_plural = u'小鹿大学/资深讲师列表'

    def __unicode__(self):
        return "%s:%s" % (self.name, self.title)

    @property
    def status_display(self):
        return get_choice_name(Instructor.STATUS_TYPES, self.status)

    @property
    def apply_date(self):
        return self.created.date()

    def update_status(self, status):
        if self.status != status:
            self.status = status
            self.save(update_fields=['status'])
            return True
        return False

    @classmethod
    def create_instruct(cls,
                        name,
                        title,
                        image,
                        introduction,
                        mama_id,
                        status):
        instruct = cls.objects.filter(mama_id=mama_id).first()
        if instruct:
            return instruct
        instruct = cls(name=name,
                       title=title,
                       image=image,
                       introduction=introduction,
                       mama_id=mama_id,
                       status=status)
        instruct.save()
        return instruct


class Lesson(BaseModel):
    STATUS_EFFECT = 1
    STATUS_FINISHED = 2
    STATUS_CANCELED = 3
    STATUS_TYPES = ((STATUS_EFFECT, u'有效'), (STATUS_FINISHED, u'已完成'), (STATUS_CANCELED, u'取消'))

    lesson_topic_id = models.IntegerField(default=0, db_index=True, verbose_name=u'课程主题ID')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'课程主题')
    description = models.TextField(max_length=512, blank=True, verbose_name=u'课程描述')
    content_link = models.CharField(max_length=256, blank=True, verbose_name=u'内容链接')

    instructor_id = models.IntegerField(default=0, db_index=True, verbose_name=u'讲师ID')
    instructor_name = models.CharField(max_length=32, blank=True, verbose_name=u'讲师昵称')
    instructor_title = models.CharField(max_length=64, blank=True, verbose_name=u'讲师头衔')
    instructor_image = models.CharField(max_length=256, blank=True, verbose_name=u'讲师头像')

    num_attender = models.IntegerField(default=0, verbose_name=u'总听课人数')
    effect_num_attender = models.IntegerField(default=0, verbose_name=u'有效听课人数')
    num_score = models.IntegerField(default=0, verbose_name=u'课程评分')
    start_time = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name=u'开始时间')

    # at most 10 qrcode_links
    qrcode_links = JSONCharMyField(max_length=1024, default={}, blank=True, verbose_name=u'群二维码链接')

    # uni_key: lesson_topic_id + instructor_id + start_time
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')

    status = models.IntegerField(db_index=True, default=1, choices=STATUS_TYPES, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_xlmm_lesson'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿大学/课程'
        verbose_name_plural = u'小鹿大学/课程列表'

    def __unicode__(self):
        return "%s:%s:%s" % (self.title, self.instructor_name, self.start_time)

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
        qrcode_release_time = self.start_time - datetime.timedelta(minutes=30)
        if datetime.datetime.now() > qrcode_release_time and self.status == Lesson.STATUS_EFFECT:
            return 1
        return 0

    @property
    def m_static_url(self):
        return settings.M_STATIC_URL

    def carry(self):
        base_carry = 3000 # 6000 cents == 60RMB
        if self.effect_num_attender >= 100:
            base_carry = 6000
        if self.effect_num_attender >= 300:
            base_carry = 8000
        if self.effect_num_attender >= 400:
            base_carry = 10000
        return base_carry

    def customer_idx(self):
        return None

    def is_canceled(self):
        return self.status == Lesson.STATUS_CANCELED

    def is_confirmed(self):
        return self.status == Lesson.STATUS_FINISHED

    @classmethod
    def create_instruct_lesson(cls,
                               lesson_topic_id,
                               title,
                               description,
                               content_link,
                               instructor_id,
                               instructor_name,
                               instructor_title,
                               instructor_image,
                               start_time,
                               uni_key,
                               status):
        lesson = cls.objects.filter(uni_key=uni_key).first()
        if lesson:
            return lesson
        lesson = cls(lesson_topic_id=lesson_topic_id,
                     title=title,
                     description=description,
                     content_link=content_link,
                     instructor_id=instructor_id,
                     instructor_name=instructor_name,
                     instructor_title=instructor_title,
                     instructor_image=instructor_image,
                     start_time=start_time,
                     uni_key=uni_key,
                     status=status)
        lesson.save()
        return lesson


def lesson_update_instructor_attender_num(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_lesson_update_instructor_attender_num
    task_lesson_update_instructor_attender_num.delay(instance.instructor_id)

post_save.connect(lesson_update_instructor_attender_num,
                  sender=Lesson, dispatch_uid='post_save_lesson_update_instructor_attender_num')


def lesson_update_instructor_payment(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_lesson_update_instructor_payment
    task_lesson_update_instructor_payment.delay(instance)

post_save.connect(lesson_update_instructor_payment,
                  sender=Lesson, dispatch_uid='post_save_lesson_update_instructor_payment')


class LessonAttendRecord(BaseModel):
    STATUS_EFFECT = 1
    STATUS_CANCELED = 2
    STATUS_TYPES = ((STATUS_EFFECT, u'有效'), (STATUS_CANCELED, u'无效'))

    lesson_id = models.IntegerField(default=0, db_index=True, verbose_name=u'课程ID')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'课程主题')

    student_unionid = models.CharField(max_length=64, db_index=True, verbose_name=u"学员UnionID")
    student_nick = models.CharField(max_length=64, verbose_name=u"学员昵称")
    student_image = models.CharField(max_length=256, verbose_name=u"学员头像")

    num_score = models.IntegerField(default=0, verbose_name=u'课程评分')

    # uni_key = lesson_id + student_unionid
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u"唯一ID")

    status = models.IntegerField(default=2, choices=STATUS_TYPES, db_index=True, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_xlmm_lesson_attend_record'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿大学/课程学员记录'
        verbose_name_plural = u'小鹿大学/课程学员记录列表'

    def __unicode__(self):
        return "%s:%s" % (self.lesson_id, self.student_nick)

    @property
    def status_display(self):
        if self.status == LessonAttendRecord.STATUS_EFFECT:
            return u'签到成功'
        return u'重复学员'

    @property
    def signup_date(self):
        month = self.created.month
        day = self.created.day
        return "%02d-%02d" % (month,day)

    @property
    def signup_time(self):
        hour = self.created.hour
        minute = self.created.minute
        second = self.created.second
        return "%02d:%02d:%02d" % (hour,minute,second)


def lessonattendrecord_create_topicattendrecord(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_lessonattendrecord_create_topicattendrecord
    task_lessonattendrecord_create_topicattendrecord.delay(instance)

post_save.connect(lessonattendrecord_create_topicattendrecord,
                  sender=LessonAttendRecord, dispatch_uid='post_save_lessonattendrecord_topicattendrecord')

def update_lesson_attender_num(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_update_lesson_attender_num
    task_update_lesson_attender_num.delay(instance.lesson_id)

post_save.connect(update_lesson_attender_num,
                  sender=LessonAttendRecord, dispatch_uid='post_save_update_lesson_attender_num')


class TopicAttendRecord(BaseModel):
    STATUS_EFFECT = 1
    STATUS_CANCELED = 2
    STATUS_TYPES = ((STATUS_EFFECT, u'EFFECT'), (STATUS_CANCELED, u'CANCELED'))


    topic_id = models.IntegerField(default=0, db_index=True, verbose_name=u'主题ID')
    title = models.CharField(max_length=128, blank=True, verbose_name=u'课程主题')

    student_unionid = models.CharField(max_length=64, db_index=True, verbose_name=u"学员UnionID")
    student_nick = models.CharField(max_length=64, blank=True, verbose_name=u"学员昵称")
    student_image = models.CharField(max_length=256, blank=True, verbose_name=u"学员头像")

    # uni_key = topic_id + student_unionid + year + week_num
    # This means a person can only attend the same topic once per week.
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u"唯一ID")

    # TopicAttendRecord must be generated by a LessonAttendRecord
    lesson_attend_record_id = models.IntegerField(default=0, verbose_name=u'课程参加记录ID')

    status = models.IntegerField(default=1, choices=STATUS_TYPES, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_xlmm_topic_attend_record'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿大学/主题学员记录'
        verbose_name_plural = u'小鹿大学/主题学员记录列表'

    def __unicode__(self):
        return "%s:%s" % (self.topic_id, self.student_nick)


def topicattendrecord_validate_lessonattendrecord(sender, instance, created, **kwargs):
    if created:
        from flashsale.xiaolumm.tasks import task_topicattendrecord_validate_lessonattendrecord
        lesson_attend_record_id = instance.lesson_attend_record_id
        task_topicattendrecord_validate_lessonattendrecord.delay(lesson_attend_record_id)

post_save.connect(topicattendrecord_validate_lessonattendrecord,
                  sender=TopicAttendRecord, dispatch_uid='post_save_topicattendrecord_lessonattendrecord')

def update_topic_attender_num(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_update_topic_attender_num
    task_update_topic_attender_num.delay(instance.topic_id)

post_save.connect(update_topic_attender_num, sender=TopicAttendRecord, dispatch_uid='post_save_update_topic_attender_num')

