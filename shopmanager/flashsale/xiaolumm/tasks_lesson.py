# -*- encoding:utf-8 -*-

import logging

from celery.task import task
from django.db.models import Sum

from flashsale.xiaolumm import util_description

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models.models_lesson import LessonAttendRecord, LessonTopic, Lesson, Instructor, TopicAttendRecord
from flashsale.xiaolumm.models.models_fortune import AwardCarry
from flashsale.xiaolumm import util_unikey
from flashsale.xiaolumm.models import XiaoluMama

import sys


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@task()
def task_create_lessonattendrecord(lesson_id, userinfo):
    student_unionid = userinfo.get("unionid")
    student_nick = userinfo.get("nickname")
    student_image = userinfo.get("headimgurl")
    
    uni_key = util_unikey.gen_lessonattendrecord_unikey(lesson_id, student_unionid)
    records = LessonAttendRecord.objects.filter(uni_key=uni_key)

    if records.count() <= 0:
        lessons = Lesson.objects.filter(id=lesson_id)
        if lessons.count() > 0:
            lesson = lessons[0]
            title = lesson.title
            ar = LessonAttendRecord(lesson_id=lesson_id, title=title, student_unionid=student_unionid,
                                    student_nick=student_nick, student_image=student_image, uni_key=uni_key)
            ar.save()

@task()
def task_create_instructor_application(userinfo):
    unionid = userinfo.get("unionid")
    nick = userinfo.get("nickname")
    image = userinfo.get("headimgurl")

    mamas = XiaoluMama.objects.filter(openid=unionid, status=XiaoluMama.EFFECT, charge_status=XiaoluMama.CHARGED)
    mama = mamas.first()
    if not mama:
        return

    mama_id = mama.id
                                     
    title = u'特聘讲师'
    instructors = Instructor.objects.filter(mama_id=mama_id)
    if instructors.count() <= 0:
        instructor = Instructor(name=nick,title=title,image=image,mama_id=mama_id)
        instructor.save()
    
    
    
@task()
def task_lessonattendrecord_create_topicattendrecord(lesson_attend_record):
    unionid = lesson_attend_record.student_unionid
    lesson_id = lesson_attend_record.lesson_id
    lesson = Lesson.objects.get(id=lesson_id)

    topic_id = lesson.lesson_topic_id
    uni_key = util_unikey.gen_topicattendrecord_unikey(topic_id, unionid)

    records = TopicAttendRecord.objects.filter(uni_key=uni_key)
    if records.count() <= 0:
        t = TopicAttendRecord(topic_id=topic_id,title=lesson.title,student_unionid=unionid,
                              student_nick=lesson_attend_record.student_nick,
                              student_image=lesson_attend_record.student_image,
                              uni_key=uni_key,lesson_attend_record_id=lesson_attend_record.id)
        t.save()

    
@task()
def task_topicattendrecord_validate_lessonattendrecord(lesson_attend_record_id):
    record = LessonAttendRecord.objects.get(id=lesson_attend_record_id)
    record.status = LessonAttendRecord.STATUS_EFFECT
    record.save(update_fields=['status'])


@task()
def task_update_topic_attender_num(topic_id):
    num_attender = TopicAttendRecord.objects.filter(topic_id=topic_id).count()
    topic = LessonTopic.objects.get(id=topic_id)
    topic.num_attender = num_attender
    topic.save(update_fields=['num_attender'])


@task()
def task_update_lesson_attender_num(lesson_id):
    num_attender = LessonAttendRecord.objects.filter(lesson_id=lesson_id).count()
    effect_num_attender = LessonAttendRecord.objects.filter(lesson_id=lesson_id, status=LessonAttendRecord.STATUS_EFFECT).count()
    lesson = Lesson.objects.get(id=lesson_id)
    lesson.num_attender = num_attender
    lesson.effect_num_attender = effect_num_attender
    lesson.save(update_fields=['num_attender', 'effect_num_attender'])


@task()
def task_lesson_update_instructor_attender_num(instructor_id):
    res = Lesson.objects.filter(instructor_id=instructor_id).aggregate(total=Sum('num_attender'))
    num_attender = res['total'] or 0

    instructor = Instructor.objects.get(id=instructor_id)
    instructor.num_attender = num_attender
    instructor.save(update_fields=['num_attender'])


@task()
def task_lesson_update_instructor_payment(lesson):
    instructor_id = lesson.instructor_id
    instructor = Instructor.objects.get(id=instructor_id)
    mama_id = instructor.mama_id

    status = 1 # pending
    if lesson.is_canceled():
        status = 3 # cancel
    if lesson.is_confirmed():
        status = 2

    if status == 1:
        # Only cancel/confirm we revise/create awardcarry for lesson
        return
    
    carry_type = 3 # 授课奖金
    carry_description = util_description.get_awardcarry_description(carry_type)
    contributor_nick = 'lesson-%s' % lesson.id
    date_field = lesson.start_time.date()
    carry_num = lesson.carry()
    
    uni_key = util_unikey.gen_awardcarry_unikey('lesson', lesson.id)
    records = AwardCarry.objects.filter(uni_key=uni_key)
    if records.count() <= 0:
        ac = AwardCarry(mama_id=mama_id,carry_num=carry_num,carry_type=carry_type,
                        carry_description=carry_description,contributor_nick=contributor_nick,
                        date_field=date_field,uni_key=uni_key,status=status)
        ac.save()
    else:
        ac = records[0]
        if ac.status != status:
            ac.status = status
            ac.save(update_fields=['status'])


