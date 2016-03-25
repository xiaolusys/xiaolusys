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
    FINISHED   = 1
    SHAREDRESS = 2
    STATUS_CHOICES = ((UNFINISHED, u'未完成'),
                      (FINISHED, u'已完成'))
    user_unionid = models.CharField(max_length=28, unique=True, verbose_name=u'用户Unionid')
    openid = models.CharField(max_length=28, verbose_name=u'用户openid')
    mama_age   = models.IntegerField(default=0, verbose_name=u'妈妈年龄')
    mama_headimg = models.CharField(max_length=256, verbose_name=u'头像')
    mama_nick  = models.CharField(max_length=32, verbose_name=u'昵称')
    referal_from = models.CharField(max_length=28,blank=True,db_index=True, verbose_name=u'推荐人Unoinid')
    exam_score = models.IntegerField(default=0, verbose_name=u'答题分数')
    share_from = models.CharField(max_length=64, verbose_name=u'分享平台')
    exam_date = models.DateTimeField(null=True, auto_now_add=True, verbose_name=u'答题日期')
    exam_state = models.IntegerField(choices=STATUS_CHOICES, default=UNFINISHED, verbose_name=u"状态")
    
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
        return self.exam_state in (self.SHAREDRESS, self.FINISHED)
    
    @property
    def active_id(self):
        return 1
    
    def confirm_finished(self,score):
        """ 完成测试 """
        self.exam_score = score
        self.exam_state = self.FINISHED
        self.save()
        
    def replay(self):
        """ 再测一次 """
        self.exam_state = self.UNFINISHED
        self.save()
        
    def get_referal_mamadress(self):
        if not self.referal_from:
            return None
        
        referals = self.__class__.objects.filter(user_unionid=self.referal_from)
        if referals.exists():
            return referals[0]
        return None
    
    @property
    def is_sendenvelop(self):
        return self.share_from.strip() != ''
    
    def add_share_type(self,share_to):
        self.share_from += ','+share_to
        self.save()
        
    def send_envelop(self):
        
        from flashsale.pay.models import Customer
        from flashsale.pay.models_coupon_new import UserCoupon
        customers = Customer.objects.filter(unionid=self.user_unionid,status=Customer.NORMAL)
        if customers.exists():
            customer = customers[0]
            user_coupon = UserCoupon()
            user_coupon.release_by_template(buyer_id=customer.id,template_id=34)
            
class DressProduct(BaseModel):
    """ 穿衣测试推荐商品 """
    
    age_min  = models.IntegerField(db_index=True, verbose_name=u"年龄大等于")
    age_max  = models.IntegerField(verbose_name=u"年龄小等于")
    category = models.IntegerField(verbose_name=u'分类ID')
    product_id = models.BigIntegerField(verbose_name=u'推荐商品ID')
    in_active = models.BooleanField(verbose_name=u'生效')
        
    class Meta:
        db_table = 'flashsale_mmexam_dressproduct'
        app_label = 'promotion'
        verbose_name = u'推广/穿衣测试推荐商品'
        verbose_name_plural = u'推广/穿衣测试推荐商品列表'

    def __unicode__(self):
        return '%d'%self.id
    
    @classmethod
    def filter_by_many(cls, category=None, lnum=1, max_age=100, min_age=1,**kwags):
        qs = cls.objects.filter(in_active=True).order_by('-modified')
        if category:
            qs = qs.filter(category=category)
        if max_age is not None:
            qs = qs.filter(age_max__lte=max_age)
        if min_age is not None:
            qs = qs.filter(age_min__lte=min_age)
        if min_age is not None:
            qs = qs.filter(age_min__lte=min_age)
        return [p.product_id for p in qs[:lnum]]
            