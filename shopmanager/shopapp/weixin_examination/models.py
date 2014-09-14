#-*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

class ExamProblem(models.Model):
    
    ACTIVE   = 0
    DEACTIVE = 1
    STATUS_CHOICES = ((ACTIVE,u'使用'),
                      (DEACTIVE,u'待用'),)
    
    problem_title   = models.CharField(max_length=1500,blank=True,verbose_name=u'题目')
    problem_answer  = models.CharField(max_length=4,blank=True,verbose_name=u'正确选项')
    option_a = models.CharField(max_length=200,blank=True,verbose_name=u'选项A')
    option_b = models.CharField(max_length=200,blank=True,verbose_name=u'选项B')
    option_c = models.CharField(max_length=200,blank=True,verbose_name=u'选项C')
    option_d = models.CharField(max_length=200,blank=True,verbose_name=u'选项D')
    problem_score = models.IntegerField(default=1,verbose_name=u'题目分数')
    
    modified   = models.DateTimeField(auto_now=True,blank=True,null=True,verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True,blank=True,null=True,verbose_name=u'创建日期')
    
    status  = models.IntegerField(choices=STATUS_CHOICES,default=ACTIVE,verbose_name=u"状态")
    class Meta:
        db_table = 'shop_weixin_exam_problem'
        verbose_name = u'微信考试题库'
        verbose_name_plural = u'微信考试题库列表'
        
        
class ExamPaper(models.Model):
    
    SCRIPT = 0
    ACTIVE = 1
    DEACTIVE = 2
    FINISHED = 3
    STATUS_CHOICES = ((SCRIPT,u'草稿'),
                      (ACTIVE,u'进行中'),
                      (DEACTIVE,u'已取消'),
                      (FINISHED,u'已结束'),)
    
    paper_title = models.CharField(max_length=200,blank=True,verbose_name=u'卷标')
    problem_num = models.IntegerField(null=True,db_index=True,verbose_name=u'题目数')
    
    modified   = models.DateTimeField(auto_now=True,blank=True,null=True,verbose_name=u'修改时间')
    created    = models.DateTimeField(auto_now_add=True,null=True,verbose_name=u'创建时间')
    
    status  = models.IntegerField(choices=STATUS_CHOICES,default=SCRIPT,verbose_name=u"状态")  
    
    class Meta:
        db_table = 'shop_wexin_exam_paper'
        verbose_name = u'微信考试答卷'
        verbose_name_plural = u'微信考试答卷列表'
        
        
class ExamUserPaper(models.Model):
    
    UNFINISHED = 0
    FINISHED   = 1
    STATUS_CHOICES = ((UNFINISHED,u'未完成'),
                      (FINISHED,u'已完成'),)
    
    user_openid = models.CharField(max_length=64,db_index=True,verbose_name=u"微信ID")
    paper_id    = models.CharField(max_length=100,blank=True,verbose_name=u'卷')
    
    answer_num  = models.IntegerField(default=0,verbose_name=u'答题数')
    
    grade       = models.IntegerField(default=0,verbose_name=u'考试得分')
    
    modified   = models.DateTimeField(auto_now=True,blank=True,null=True,verbose_name=u'修改时间')
    created     = models.DateTimeField(auto_now_add=True,blank=True,null=True,verbose_name='答题日期')
    
    status     = models.IntegerField(choices=STATUS_CHOICES,default=UNFINISHED,verbose_name=u"状态") 
    
    class Meta:
        db_table = 'shop_wexin_user_paper'
        verbose_name = u'用户答卷'
        verbose_name_plural = u'用户答卷列表'    
    
        
class ExamUserProblem(models.Model):
    
    SELECTED_A = 'A'
    SELECTED_B = 'B'
    SELECTED_C = 'C'
    SELECTED_D = 'D'
    SELECTED_CHOICE = (
                (SELECTED_A,u'A'),
                (SELECTED_B,u'B'),
                (SELECTED_C,u'C'),
                (SELECTED_D,u'D')
                )
    
    user_openid = models.CharField(max_length=64,verbose_name=u"微信ID")
    paper_id   = models.IntegerField(null=False,db_index=True,verbose_name=u'卷码')
    problem_id = models.IntegerField(null=False,db_index=True,verbose_name=u'题码')
    
    selected = models.CharField(max_length=10,blank=True,
                                     choices=SELECTED_CHOICE,verbose_name=u'答题人选项')
    
    problem_score = models.IntegerField(null=True,db_index=True,verbose_name=u'题目分数')
    
    created    = models.DateTimeField(auto_now_add=True,null=True,verbose_name=u'答题时间')
    
    status  = models.BooleanField(default=False,verbose_name=u'回答正确')
    class Meta:
        db_table = 'shop_weixin_exam_user_proble'
        unique_together = ('user_openid', 'paper_id', 'problem_id')
        verbose_name = u'用户答题'
        verbose_name_plural = u'用户答题列表'
    
    
    