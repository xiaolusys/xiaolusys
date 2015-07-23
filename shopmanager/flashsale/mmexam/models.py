#-*- coding:utf-8 -*-
from django.db import models
from django.shortcuts import render
# Create your models here.
from django.db import models
import datetime
from django.utils import timezone

class Question(models.Model):
#     question_num=models.IntegerField(max_length=10,blank=True,verbose_name=u'题号'，)
    SINGLE=1
    MANY=2
    NUM_CHOICES = ((SINGLE,u'单选'),
                      (MANY,u'多选'),)
    question=models.CharField(max_length=200,verbose_name=u'问题')
    pub_date=models.DateTimeField(null=True,auto_now_add=True,verbose_name='出卷日期')
    real_answer=models.CharField(max_length=200,verbose_name='正确选项(请按照顺序输入)')
    single_many=models.IntegerField(choices=NUM_CHOICES,max_length=100,verbose_name=u'单选/多选')
   
    def __unicode__(self):
        return self.question
    #def was_published_recently(self):
    #return self.pub_date>=timezone.now() - datetime.timedelta(days=1)
    #was_published_recently.admin_order_field = 'pub_date'
    #was_published_recently.boolean = True
    #was_published_recently.short_description = 'Published recently?'
    class Meta:
        db_table = 'flashsale_mmexam_question'
        app_label = 'xiaolumm'
        verbose_name = u'代理考试题目'
        verbose_name_plural = u'代理考试题目列表'
        
        
class Choice(models.Model):
    question=models.ForeignKey(Question)
    
    choice_title= models.CharField(max_length=200,verbose_name=u'选项编号') 
    #这是ABCD的编号
    choice_text=models.CharField(max_length=200)      
    #votes=models.IntegerField(default=0)
    def __unicode__(self):
        return self.choice_text
    
    class Meta:
        db_table = 'flashsale_mmexam_choice'
        app_label = 'xiaolumm'
        verbose_name = u'代理考试选项'
        verbose_name_plural = u'代理考试选项列表'
        
        
class Result(models.Model):
    UNFINISHED = 0
    FINISHED   = 1
    STATUS_CHOICES = ((UNFINISHED,u'未通过'),
                      (FINISHED,u'已通过'),)
    
    daili_user  = models.CharField(max_length=32,unique=True,verbose_name=u'代理unionid')
    #exam_grade = models.IntegerField(max_length=10,blank=True,verbose_name=u'考试得分',default="60")
    exam_date  = models.DateTimeField(null=True,auto_now_add=True,verbose_name='答题日期')
    exam_state=models.IntegerField(choices=STATUS_CHOICES,default=UNFINISHED,verbose_name=u"是否通过") 
    
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
    
        self.exam_state = self.FINISHED
        self.save()
        
        from flashsale.xiaolumm.signals import signal_push_pending_carry_to_cash
        from flashsale.xiaolumm.models import XiaoluMama
        
        xlmms = XiaoluMama.objects.filter(openid=self.daili_user)
        if xlmms.count() == 0:
            return  
        
        xlmm = xlmms[0]
        signal_push_pending_carry_to_cash.send(sender=XiaoluMama,obj=xlmm.id)
        
        
    
    
    