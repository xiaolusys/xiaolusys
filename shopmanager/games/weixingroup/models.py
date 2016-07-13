# coding=utf-8
from core.models import BaseModel
from django.db import models
from django.contrib.auth.models import User
from flashsale.promotion.models import ActivityEntry


class XiaoluAdministrator(BaseModel):
    user_id = models.IntegerField(verbose_name=u'关联用户')
    username = models.IntegerField(verbose_name=u'管理员用户名')
    nick = models.IntegerField(verbose_name=u'管理员昵称')
    weixin_qr_img = models.CharField(max_length=255, verbose_name=u'管理员二维码')
    STATUS_CHOICES = ((0, u'初始'),
                      (1, u'有效'),
                      (2, u'作废'),)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name=u'状态')

    class Meta:
        app_label = 'weixingroup'
        verbose_name = u'小鹿微信群管理员'
        verbose_name_plural = u'小鹿微信群管理员列表'

    @property
    def mama_count(self):
        pass

    @property
    def fans_count(self):
        pass

    @staticmethod
    def get_group_mincnt_admin():
        mincnt = 100000
        res = None
        for admin in XiaoluAdministrator.objects.filter(status=1):
            mama_groups_cnt = admin.mama_groups.count()
            if mama_groups_cnt < mincnt:
                mincnt = mama_groups_cnt
                res = admin
        return res


class GroupMamaAdministrator(BaseModel):
    class Meta:
        unique_together = ('mama_id', 'status')
        app_label = 'weixingroup'
        verbose_name = u'小鹿微信群组'
        verbose_name_plural = u'小鹿微信群组列表'

    admin = models.ForeignKey(XiaoluAdministrator, related_name='mama_groups', verbose_name=u'管理员id')
    mama_id = models.IntegerField(verbose_name=u'妈妈用户id')
    STATUS_CHOICES = ((1, u'有效'),
                      (2, u'作废'),)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name=u'状态')

    @property
    def mama(self):
        return User.objects.get(id=self.mama_id)

    @staticmethod
    def get_or_create(admin, mama_id):
        GroupMamaAdministrator.objects.get_or_create()


class GroupFans(BaseModel):
    class Meta:
        app_label = 'weixingroup'
        verbose_name = u'小鹿微信群粉丝'
        verbose_name_plural = u'小鹿微信群粉丝表'

    group = models.ForeignKey(GroupMamaAdministrator)
    user_id = models.IntegerField(null=True, verbose_name=u'关联用户')
    head_img_url = models.CharField(max_length=100, verbose_name=u'用户微信头像')
    nick = models.CharField(max_length=100, verbose_name=u'用户微信昵称')
    union_id = models.CharField(max_length=100, verbose_name=u'用户微信unionid')
    open_id = models.CharField(max_length=100, verbose_name=u'用户微信openid')

    def create(self, group, user_id, head_img_url, nick, union_id, open_id):
        gf = GroupFans(group=group,
            user_id=user_id,
            head_img_url=head_img_url,
            nick=nick,
            union_id=union_id,
            open_id=open_id
        )
        gf.save()
        return gf


class ActivityUsers(BaseModel):
    class Meta:
        app_label = 'weixingroup'
        verbose_name = u'活动'
        verbose_name_plural = u'活动列表'

    activity = models.ForeignKey(ActivityEntry)
    user_id = models.IntegerField()
    group = models.ForeignKey('GroupMamaAdministrator')

    @staticmethod
    def join(activity, user_id, group_id):
        au = ActivityUsers.objects.filter(activity=activity, user_id=user_id).first()
        if not au:
            au = ActivityUsers(activity=activity,
                               user_id=user_id,
                               group_id=group_id)
            au.save()
        elif au.group_id == group_id:
            au.group_id = group_id
            au.save()
        return au

    def has_joined(self, user_id):
        return ActivityUsers.objects.filter(user_id=user_id).exists()
