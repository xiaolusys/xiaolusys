# -*- encoding:utf-8 -*-

from celery.task import task
from django.db import IntegrityError
from flashsale.xiaolumm import util_description

import logging

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models_lesson import AttendRecord, Lesson
from flashsale.xiaolumm import util_unikey

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
def task_userinfo_update_attendrecord(lesson_id, userinfo):
    student_unionid = userinfo.get("unionid")
    student_nick = userinfo.get("nickname")
    student_image = userinfo.get("headimgurl")
    
    uni_key = util_unikey.gen_attendrecord_unikey(lesson_id, student_unionid)
    records = AttendRecord.objects.filter(uni_key=uni_key)

    if records.count() <= 0:
        lessons = Lesson.objects.filter(id=lesson_id)
        if lessons.count() > 0:
            lesson = lessons[0]
            title = lesson.title
            ar = AttendRecord(lesson_id=lesson_id, title=title, student_unionid=student_unionid,
                              student_nick=student_nick, student_image=student_image, uni_key=uni_key)
            ar.save()
        
    
