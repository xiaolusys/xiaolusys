# coding=utf-8
from django.db import models

from core.models import BaseModel
from flashsale.xiaolumm.signals import signal_push_pending_carry_to_cash
from flashsale.xiaolumm.models import XiaoluMama
from core.fields import JSONCharMyField
from flashsale.mmexam import constants


def default_mamaexam_extras():
    return {
        "single_point": 2,  # 单选题分值
        "multiple_point": 2,  # 多选题分值
        "judge_point": 2,  # 判断题分值
        "past_point": 70,  # 考试通过的分数
        "upper_agencylevel": 12  # 考试通过后代理要升级的等级数
    }


def exam_participant_choice():
    return constants.EXAM_PARTICIPANT_CHOICE


class Mamaexam(BaseModel):
    sheaves = models.IntegerField(db_index=True, verbose_name=u'考试轮数')
    start_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'开放时间')
    expire_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'结束时间')
    valid = models.BooleanField(db_index=True, default=False, verbose_name=u'是否有效')
    participant = models.IntegerField(choices=exam_participant_choice(), default=constants.XLMM_EXAM,
                                      verbose_name=u'目标用户')
    extras = JSONCharMyField(max_length=512, blank=True, null=True,
                             default=default_mamaexam_extras,
                             verbose_name=u"附加信息")

    def __unicode__(self):
        return '%s' % self.sheaves

    @property
    def single_point(self):
        return self.extras['single_point']

    @property
    def multiple_point(self):
        return self.extras['multiple_point']

    @property
    def judge_point(self):
        return self.extras['judge_point']

    @property
    def past_point(self):
        return self.extras['past_point']

    @property
    def upper_agencylevel(self):
        return self.extras['upper_agencylevel']

    def get_question_type_point(self, question_type):
        if question_type == 1:
            return self.single_point
        if question_type == 2:
            return self.multiple_point
        if question_type == 3:
            return self.judge_point
        return 0

    class Meta:
        db_table = 'flashsale_mmexam_sheaves'
        app_label = 'mmexam'
        verbose_name = u'代理考试轮数'
        verbose_name_plural = u'代理考试题目轮数列表'


class Question(BaseModel):
    SINGLE = 1
    MANY = 2
    TUFA = 3
    NUM_CHOICES = (
        (SINGLE, u'单选'),
        (MANY, u'多选'),
        (TUFA, u'对错题')
    )
    question = models.CharField(max_length=200, verbose_name=u'问题')
    sheaves = models.IntegerField(default=0, db_index=True, verbose_name=u'考试轮数')
    start_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'考试开始日期')
    expire_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'考试截止日期')
    real_answer = models.CharField(max_length=200, verbose_name=u'正确选项(请按照顺序输入)')
    question_types = models.IntegerField(default=SINGLE, choices=NUM_CHOICES, verbose_name=u'题型')
    score = models.IntegerField(default=0, verbose_name=u'分值')

    def __unicode__(self):
        return self.question

    class Meta:
        db_table = 'flashsale_mmexam_question'
        app_label = 'mmexam'
        verbose_name = u'代理考试题目'
        verbose_name_plural = u'代理考试题目列表'


class Choice(BaseModel):
    question = models.ForeignKey(Question, related_name='question_choices')
    choice_title = models.CharField(max_length=200, verbose_name=u'选项编号')  # 这是ABCD的编号
    choice_text = models.CharField(max_length=200, verbose_name=u'选项描述')
    choice_score = models.IntegerField(default=0, verbose_name=u'分值')

    def __unicode__(self):
        return self.choice_text

    class Meta:
        db_table = 'flashsale_mmexam_choice'
        app_label = 'mmexam'
        verbose_name = u'代理考试选项'
        verbose_name_plural = u'代理考试选项列表'


class Result(BaseModel):
    UNFINISHED = 0
    FINISHED = 1
    STATUS_CHOICES = ((UNFINISHED, u'未通过'),
                      (FINISHED, u'已通过'),)
    customer_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'用户id')
    xlmm_id = models.IntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    daili_user = models.CharField(max_length=32, verbose_name=u'代理unionid')
    sheaves = models.IntegerField(default=0, db_index=True, verbose_name=u'考试轮数')
    exam_date = models.DateTimeField(null=True, auto_now_add=True, verbose_name=u'答题日期')
    total_point = models.FloatField(default=0.0, verbose_name=u'总分')
    exam_state = models.IntegerField(choices=STATUS_CHOICES, default=UNFINISHED, verbose_name=u"是否通过")

    class Meta:
        unique_together = ('customer_id', 'sheaves')
        db_table = 'flashsale_mmexam_result'
        app_label = 'mmexam'
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
            # xlmm = xlmms[0]
            # 发送完成后的信号
            # signal_push_pending_carry_to_cash.send(sender=XiaoluMama, obj=xlmm.id)


class ExamResultDetail(BaseModel):
    """ 考试答题明细 """
    customer_id = models.BigIntegerField(db_index=True, verbose_name=u'用户ID')
    sheaves = models.IntegerField(default=0, db_index=True, verbose_name=u'考试轮数')
    question_id = models.BigIntegerField(db_index=True, verbose_name=u'题号')
    answer = models.CharField(max_length=32, verbose_name=u'用户回答')
    is_right = models.BooleanField(default=False, verbose_name=u'是否正确')
    point = models.FloatField(default=0.0, verbose_name=u'分值')
    uni_key = models.CharField(max_length=64, verbose_name=u'唯一标识')
    # 唯一id customer_id/question_id　一个用户一个题目　只会有一个记录结果

    class Meta:
        db_table = 'flashsale_mmexam_result_detail'
        app_label = 'mmexam'
        verbose_name = u'代理考试结果明细'
        verbose_name_plural = u'代理考试结果明细列表'

    @classmethod
    def customer_answer(cls, customer_id, question_id):
        """ 用户的回答 """
        return cls.objects.filter(customer_id=customer_id, question_id=question_id).first()


class MamaDressResult(BaseModel):
    """ 穿衣风格测试结果 """
    UNFINISHED = 0
    FINISHED = 1
    SHAREDRESS = 2
    STATUS_CHOICES = ((UNFINISHED, u'未完成'),
                      (FINISHED, u'已完成'))
    user_unionid = models.CharField(max_length=28, unique=True, verbose_name=u'用户Unionid')
    openid = models.CharField(max_length=28, verbose_name=u'用户openid')
    mama_age = models.IntegerField(default=0, verbose_name=u'妈妈年龄')
    mama_headimg = models.CharField(max_length=256, verbose_name=u'头像')
    mama_nick = models.CharField(max_length=32, verbose_name=u'昵称')
    referal_from = models.CharField(max_length=28, blank=True, db_index=True, verbose_name=u'推荐人Unoinid')
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

    def confirm_finished(self, score):
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

    def add_share_type(self, share_to):
        self.share_from += ',' + share_to
        self.save()


class DressProduct(BaseModel):
    """ 穿衣测试推荐商品 """

    age_min = models.IntegerField(db_index=True, verbose_name=u"年龄大等于")
    age_max = models.IntegerField(verbose_name=u"年龄小等于")
    category = models.IntegerField(verbose_name=u'分类ID')
    product_id = models.BigIntegerField(verbose_name=u'推荐商品ID')
    in_active = models.BooleanField(verbose_name=u'生效')

    class Meta:
        db_table = 'flashsale_mmexam_dressproduct'
        app_label = 'promotion'
        verbose_name = u'推广/穿衣测试推荐商品'
        verbose_name_plural = u'推广/穿衣测试推荐商品列表'

    def __unicode__(self):
        return '%d' % self.id

    @classmethod
    def filter_by_many(cls, category=None, lnum=1, max_age=100, min_age=1, **kwargs):
        """ 如果设置了年龄则优先根据年龄来过滤,没有则根据类别来过滤 """
        qs = cls.objects.filter(in_active=True).order_by('-modified')
        if max_age or min_age:
            if max_age is not None:
                qs = qs.filter(age_max__gte=max_age)
            if min_age is not None:
                qs = qs.filter(age_min__lte=min_age)

        elif category is not None:
            qs = qs.filter(category=category)
        else:
            return []
        return [p.product_id for p in qs[:lnum]]
