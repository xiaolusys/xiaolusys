# -*- coding:utf-8 -*-
import datetime
from django.db import models
from django.contrib.auth.models import User


class ExamProblem(models.Model):
    ACTIVE = 0
    DEACTIVE = 1
    STATUS_CHOICES = ((ACTIVE, u'使用'),
                      (DEACTIVE, u'待用'),)

    problem_title = models.CharField(max_length=1500, blank=True, verbose_name=u'题目')
    problem_answer = models.CharField(max_length=4, blank=True, verbose_name=u'正确选项')
    option_a = models.CharField(max_length=200, blank=True, verbose_name=u'选项A')
    option_b = models.CharField(max_length=200, blank=True, verbose_name=u'选项B')
    option_c = models.CharField(max_length=200, blank=True, verbose_name=u'选项C')
    option_d = models.CharField(max_length=200, blank=True, verbose_name=u'选项D')
    problem_score = models.IntegerField(default=1, verbose_name=u'题目分数')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    status = models.IntegerField(choices=STATUS_CHOICES, default=ACTIVE, verbose_name=u"状态")

    class Meta:
        db_table = 'shop_weixin_exam_problem'
        app_label = 'weixin'
        verbose_name = u'微信考试题库'
        verbose_name_plural = u'微信考试题库列表'


class ExamPaper(models.Model):
    SCRIPT = 0
    ACTIVE = 1
    DEACTIVE = 2
    FINISHED = 3
    STATUS_CHOICES = ((SCRIPT, u'草稿'),
                      (ACTIVE, u'进行中'),
                      (DEACTIVE, u'已取消'),
                      (FINISHED, u'已结束'),)

    paper_title = models.CharField(max_length=200, blank=True, verbose_name=u'卷标')
    problem_num = models.IntegerField(null=True, db_index=True, verbose_name=u'题目数')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    status = models.IntegerField(choices=STATUS_CHOICES, default=SCRIPT, verbose_name=u"状态")

    class Meta:
        db_table = 'shop_weixin_exam_paper'
        app_label = 'weixin'
        verbose_name = u'微信考试答卷'
        verbose_name_plural = u'微信考试答卷列表'


class ExamUserPaper(models.Model):
    UNFINISHED = 0
    FINISHED = 1
    STATUS_CHOICES = ((UNFINISHED, u'未完成'),
                      (FINISHED, u'已完成'),)

    user_openid = models.CharField(max_length=64, db_index=True, verbose_name=u"微信ID")
    paper_id = models.CharField(max_length=100, blank=True, verbose_name=u'卷')

    answer_num = models.IntegerField(default=0, verbose_name=u'答题数')
    grade = models.IntegerField(default=0, verbose_name=u'考试得分')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='答题日期')

    status = models.IntegerField(choices=STATUS_CHOICES, default=UNFINISHED, verbose_name=u"状态")

    class Meta:
        db_table = 'shop_weixin_exam_user_paper'
        unique_together = ('user_openid', 'paper_id')
        app_label = 'weixin'
        verbose_name = u'用户答卷'
        verbose_name_plural = u'用户答卷列表'


class ExamUserProblem(models.Model):
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

    user_openid = models.CharField(max_length=64, verbose_name=u"微信ID")
    paper_id = models.IntegerField(null=False, db_index=True, verbose_name=u'卷码')
    problem_id = models.IntegerField(null=False, db_index=True, verbose_name=u'题码')

    selected = models.CharField(max_length=10, blank=True,
                                choices=SELECTED_CHOICE, verbose_name=u'答题人选项')

    problem_score = models.IntegerField(null=True, db_index=True, verbose_name=u'题目分数')

    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'答题时间')

    status = models.BooleanField(default=False, verbose_name=u'回答正确')

    class Meta:
        db_table = 'shop_weixin_exam_user_problem'
        unique_together = ('user_openid', 'paper_id', 'problem_id')
        app_label = 'weixin'
        verbose_name = u'用户答题'
        verbose_name_plural = u'用户答题列表'


class Invitationship(models.Model):
    from_openid = models.CharField(max_length=64, verbose_name=u"邀请人微信ID")
    invite_openid = models.CharField(max_length=64, verbose_name=u"被邀请微信ID")
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'shop_weixin_exam_invitationship'
        unique_together = ('from_openid', 'invite_openid')
        app_label = 'weixin'
        verbose_name = u'答题关系'
        verbose_name_plural = u'答题关系列表'


from django.db import transaction
from shopapp.weixin.models import WeiXinUser, WeixinUserScore, WeixinScoreItem
from shopapp.signals import weixin_active_signal, weixin_verifymobile_signal


@transaction.atomic
def convert_examgrade2score(sender, active_id, *args, **kwargs):
    exam_user_paper = ExamUserPaper.objects.get(id=active_id)
    user_openid = exam_user_paper.user_openid
    exam_score = exam_user_paper.grade

    wx_user_score, state = WeixinUserScore.objects.get_or_create(
        user_openid=user_openid)

    WeixinScoreItem.objects.create(user_openid=user_openid,
                                   score=exam_score,
                                   score_type=WeixinScoreItem.ACTIVE,
                                   expired_at=datetime.datetime.now(),
                                   memo=u"答题活动积分(%d)。" % (exam_user_paper.id))

    wx_user_score.user_score = models.F('user_score') + exam_score
    wx_user_score.save()

    transaction.commit()

    invite_ships = Invitationship.objects.filter(invite_openid=user_openid).order_by('-created')
    if invite_ships.count() > 0:

        from_openid = invite_ships[0].from_openid
        if from_openid != exam_user_paper.user_openid:

            wx_user = WeiXinUser.objects.get(openid=user_openid)
            subscribe_time = wx_user.subscribe_time
            new_subscribe = not (subscribe_time and subscribe_time < datetime.datetime(2014, 9, 15))
            is_invited = wx_user.isvalid and not wx_user.referal_from_openid

            if is_invited:
                wx_user.referal_from_openid = from_openid
                wx_user.save()

            invite_score = new_subscribe and (is_invited and 12 or 2) or 1
            wx_user_score, state = WeixinUserScore.objects.get_or_create(
                user_openid=from_openid)

            WeixinScoreItem.objects.create(user_openid=from_openid,
                                           score=invite_score,
                                           score_type=WeixinScoreItem.ACTIVE,
                                           expired_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                           memo=u"邀请好友(%s)答题积分。" % (user_openid))

            wx_user_score.user_score = models.F('user_score') + invite_score
            wx_user_score.save()


weixin_active_signal.connect(convert_examgrade2score, sender=ExamUserPaper)


@transaction.atomic
def convert_inviteship2score(sender, user_openid, *args, **kwargs):
    wx_user = WeiXinUser.objects.get(openid=user_openid)
    invite_ships = Invitationship.objects.filter(invite_openid=user_openid).order_by('-created')
    if not wx_user.referal_from_openid and invite_ships.count() > 0:

        from_openid = invite_ships[0].from_openid
        if from_openid != user_openid:
            invite_score = 10

            wx_user.referal_from_openid = from_openid
            wx_user.save()

            wx_user_score, state = WeixinUserScore.objects.get_or_create(
                user_openid=from_openid)

            WeixinScoreItem.objects.create(user_openid=from_openid,
                                           score=invite_score,
                                           score_type=WeixinScoreItem.ACTIVE,
                                           expired_at=datetime.datetime.now() + datetime.timedelta(days=365),
                                           memo=u"邀请好友(%s)积分。" % (user_openid))

            wx_user_score.user_score = models.F('user_score') + invite_score
            wx_user_score.save()


weixin_verifymobile_signal.connect(convert_inviteship2score, sender=WeiXinUser)
