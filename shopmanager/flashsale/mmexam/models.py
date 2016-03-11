# coding:utf-8 
from django.db import models

from core.models import BaseModel
from flashsale.xiaolumm.signals import signal_push_pending_carry_to_cash
from flashsale.xiaolumm.models import XiaoluMama


class Question(BaseModel):
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


class Choice(BaseModel):
    question = models.ForeignKey(Question)
    choice_title = models.CharField(max_length=200, verbose_name=u'选项编号')  # 这是ABCD的编号
    choice_text = models.CharField(max_length=200, verbose_name=u'选项描述')
    choice_score = models.IntegerField(default=0,verbose_name=u'分值')
    def __unicode__(self):
        return self.choice_text

    class Meta:
        db_table = 'flashsale_mmexam_choice'
        app_label = 'xiaolumm'
        verbose_name = u'代理考试选项'
        verbose_name_plural = u'代理考试选项列表'


class Result(BaseModel):
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


class MamaDressResult(BaseModel):
    """ 穿衣风格测试结果 """
    UNFINISHED = 0
    FINISHED = 1
    STATUS_CHOICES = ((UNFINISHED, u'未完成'),
                      (FINISHED, u'已完成'),)
    user_unionid = models.CharField(max_length=28, unique=True, verbose_name=u'妈妈Unionid')
    mama_age   = models.IntegerField(default=0, verbose_name=u'妈妈年龄')
    mama_headimg = models.CharField(max_length=256, verbose_name=u'头像')
    mama_nick  = models.CharField(max_length=32, verbose_name=u'昵称')
    referal_from = models.CharField(max_length=28,blank=True,db_index=True, verbose_name=u'推荐人Unoinid')
    exam_score = models.IntegerField(default=0, verbose_name=u'答题分数')
    exam_date = models.DateTimeField(null=True, auto_now_add=True, verbose_name=u'答题日期')
    exam_state = models.IntegerField(choices=STATUS_CHOICES, default=UNFINISHED, verbose_name=u"是否通过")
    
    class Meta:
        db_table = 'flashsale_mmexam_dressresult'
        app_label = 'promotion'
        verbose_name = u'推广/穿衣风格测试结果'
        verbose_name_plural = u'推广/穿衣风格测试结果列表'

    def __unicode__(self):
        return self.user_unionid
    
    def is_aged(self):
        return self.mama_age > 0
    
    def is_finished(self):
        return self.exam_state == self.FINISHED
    
    def confirm_finished(self,score):
        self.exam_score = score
        self.exam_state = self.FINISHED
        self.save()
        
        #TODO send envelop
    
    def get_referal_mamadress(self):
        if not self.referal_from:
            return None
        
        referals = self.__class__.objects.filter(user_unionid=self.referal_from)
        if referals.exists():
            return referals[0]
        return None
    
