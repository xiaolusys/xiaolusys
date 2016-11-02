# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User


class ExamUser(models.Model):
    user = models.ForeignKey(User, null=True, default=None, verbose_name=u'答题人')
    exam_grade = models.IntegerField(default=0, verbose_name=u'考试得分')
    paper_id = models.CharField(max_length=100, blank=True, verbose_name=u'卷')
    exam_selected_num = models.IntegerField(null=True, db_index=True, verbose_name=u'答题人答题数')
    exam_date = models.DateTimeField(blank=True, null=True, auto_now_add=True, verbose_name='答题日期')

    class Meta:
        db_table = 'shop_examination_user'
        app_label = 'examination'
        verbose_name = u'考试用户信息'
        verbose_name_plural = u'考试用户信息列表'


class ExamProblemSelect(models.Model):
    exam_problem = models.CharField(max_length=1500, blank=True, verbose_name=u'题目')
    exam_answer = models.CharField(max_length=4, blank=True, verbose_name=u'正确选项')
    option_a = models.CharField(max_length=200, blank=True, verbose_name=u'选项A')
    option_b = models.CharField(max_length=200, blank=True, verbose_name=u'选项B')
    option_c = models.CharField(max_length=200, blank=True, verbose_name=u'选项C')
    option_d = models.CharField(max_length=200, blank=True, verbose_name=u'选项D')
    exam_problem_score = models.IntegerField(null=True, db_index=True, verbose_name=u'题目分数')
    exam_problem_created = models.DateTimeField(blank=True, null=True, verbose_name=u'创建日期')

    class Meta:
        db_table = 'shop_examination_problem_select'
        app_label = 'examination'
        verbose_name = u'考试题库'
        verbose_name_plural = u'考试题库列表'


class ExamSelectProblemPaper(models.Model):
    SELECTED_A = 'A'
    SELECTED_B = 'B'
    SELECTED_C = 'C'
    SELECTED_D = 'D'
    SELECTED_CHOICE = (
        (SELECTED_A, u'A'),
        (SELECTED_B, u'B'),
        (SELECTED_C, u'C'),
        (SELECTED_D, u'D')
    )

    examproblemselects = models.ManyToManyField(ExamProblemSelect)

    paper_id = models.CharField(max_length=100, null=True, db_index=True)
    user = models.ForeignKey(User, null=True, default=None, verbose_name=u'答题人')
    problem_id = models.IntegerField(null=False, db_index=True, verbose_name=u'题码')
    exam_selected = models.CharField(max_length=10, blank=True, choices=SELECTED_CHOICE, verbose_name=u'答题人选项')
    exam_answer = models.CharField(max_length=10, blank=True, verbose_name=u'正确选项')
    exam_problem_score = models.IntegerField(null=True, db_index=True, verbose_name=u'题目分数')

    class Meta:
        db_table = 'shop_examination_paper_select_problem'
        unique_together = ('user', 'problem_id', 'paper_id')
        app_label = 'examination'
        verbose_name = u'考试卷信息'
        verbose_name_plural = u'考试卷信息列表'


class ExmaEssayQuestion(models.Model):
    exam_problem = models.CharField(max_length=1500, blank=True, verbose_name=u'题目')
    exam_selected = models.CharField(max_length=6000, blank=True, verbose_name=u'答题人选项')
    exam_answer = models.CharField(max_length=6000, blank=True, verbose_name=u'选项')
    exam_problem_score = models.IntegerField(null=True, default=2, db_index=True, verbose_name=u'题目分数')
    exam_problem_created = models.DateTimeField(blank=True, null=True, verbose_name=u'创建日期')

    class Meta:
        db_table = 'shop_examination_essay_question'
        app_label = 'examination'
        verbose_name = u'考试wenda题库'
        verbose_name_plural = u'考试wenda题库列表'


class ExamEssayQuestionPaper(models.Model):
    examessayquestion = models.ManyToManyField(ExmaEssayQuestion)

    paper_id = models.CharField(max_length=100, null=True, db_index=True)
    user = models.ForeignKey(User, null=True, default=None, verbose_name=u'答题人')
    problem_id = models.IntegerField(null=False, db_index=True, verbose_name=u'题码')
    exam_answer = models.CharField(max_length=6000, blank=True, verbose_name=u'选项')
    exam_selected = models.CharField(max_length=6000, blank=True, verbose_name=u'答题人选项')
    exam_problem_score = models.IntegerField(null=True, db_index=True, verbose_name=u'题目分数')

    class Meta:
        db_table = 'shop_examination_paper_essay_question'
        unique_together = ('user', 'problem_id', 'paper_id')
        app_label = 'examination'
        verbose_name = u'考试wenda卷信息'
        verbose_name_plural = u'考试wenda卷信息列表'
