# -*- coding:utf-8 -*-
from django.db import models
from flashsale.xiaolumm.signals import signal_push_pending_carry_to_cash
from flashsale.xiaolumm.models import XiaoluMama


class Question(models.Model):
    SINGLE = 1
    MANY = 2
    NUM_CHOICES = ((SINGLE, u'单选'),
                   (MANY, u'多选'),)
    question = models.CharField(max_length=200, verbose_name=u'问题')
    pub_date = models.DateTimeField(null=True, auto_now_add=True, verbose_name=u'出卷日期')
    real_answer = models.CharField(max_length=200, verbose_name=u'正确选项(请按照顺序输入)')
    single_many = models.IntegerField(choices=NUM_CHOICES, max_length=100, verbose_name=u'单选/多选')

    def __unicode__(self):
        return self.question

    class Meta:
        db_table = 'flashsale_mmexam_question'
        app_label = 'xiaolumm'
        verbose_name = u'代理考试题目'
        verbose_name_plural = u'代理考试题目列表'


class Choice(models.Model):
    question = models.ForeignKey(Question)
    choice_title = models.CharField(max_length=200, verbose_name=u'选项编号')  # 这是ABCD的编号
    choice_text = models.CharField(max_length=200)

    def __unicode__(self):
        return self.choice_text

    class Meta:
        db_table = 'flashsale_mmexam_choice'
        app_label = 'xiaolumm'
        verbose_name = u'代理考试选项'
        verbose_name_plural = u'代理考试选项列表'


class Result(models.Model):
    UNFINISHED = 0
    FINISHED = 1
    STATUS_CHOICES = ((UNFINISHED, u'未通过'),
                      (FINISHED, u'已通过'),)
    daili_user = models.CharField(max_length=32, unique=True, verbose_name=u'代理unionid')
    exam_date = models.DateTimeField(null=True, auto_now_add=True, verbose_name=u'答题日期')
    exam_state = models.IntegerField(choices=STATUS_CHOICES, default=UNFINISHED, verbose_name=u"是否通过")

    class Meta:
        db_table = 'flashsale_mmexam_result'
        app_label = 'xiaolumm'
        verbose_name = u'代理考试结果'
        verbose_name_plural = u'代理考试结果列表'

    def __unicode__(self):
        return self.daili_user

    def is_Exam_Funished(self):
        return self.exam_state == self.FINISHED

    def funish_Exam(self):
        """ 考试完成　"""
        self.exam_state = self.FINISHED
        self.save()  # 修改结果状态到完成状态
        xlmms = XiaoluMama.objects.filter(openid=self.daili_user)
        if xlmms.count() == 0:
            return
        xlmm = xlmms[0]
        # 发送完成后的信号
        signal_push_pending_carry_to_cash.send(sender=XiaoluMama, obj=xlmm.id)

