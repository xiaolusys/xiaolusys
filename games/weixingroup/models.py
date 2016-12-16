# coding=utf-8
from core.models import BaseModel
from django.db import models
from django.db.models import Count
from flashsale.promotion.models import ActivityEntry
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.pay.models import Customer
from django.db.models.signals import post_save


class XiaoluAdministrator(BaseModel):
    user_id = models.IntegerField(verbose_name=u'管理员用户id')
    username = models.CharField(max_length=64, verbose_name=u'管理员用户名')
    nick = models.CharField(max_length=64, verbose_name=u'二维码归属人昵称', null=True, default=None)
    head_img_url = models.CharField(max_length=256, null=True, default=None, verbose_name=u'管理员头像')
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
    def groups_count(self):
        return self.mama_groups.count()

    @property
    def all_groups_count(self):
        return GroupMamaAdministrator.objects.all().count()

    @property
    def fans_count(self):
        return GroupFans.objects.filter(group__admin_id=self.id).count()

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
        app_label = 'weixingroup'
        verbose_name = u'小鹿微信群组'
        verbose_name_plural = u'小鹿微信群组列表'

    admin = models.ForeignKey(XiaoluAdministrator, related_name='mama_groups', verbose_name=u'管理员id')
    # mama = models.ForeignKey(XiaoluMama, verbose_name=u'妈妈用户')
    mama_id = models.IntegerField(verbose_name=u'妈妈用户id')
    group_uni_key = models.CharField(max_length=128, default=None, null=True, unique=True, verbose_name=u'微信群编号')
    STATUS_CHOICES = ((1, u'有效'),
                      (2, u'作废'),)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name=u'状态')

    @property
    def mama(self):
        if not hasattr(self, '_mama_'):
            self._mama_ = XiaoluMama.objects.get(id=self.mama_id)
        return self._mama_

    @property
    def customer(self):
        return Customer.objects.normal_customer.filter(unionid=self.mama.openid).first()
        # return self.mama.get_mama_customer()

    @property
    def nick(self):
        return self.customer.nick if self.customer else ''

    @property
    def head_img_url(self):
        return self.customer.thumbnail

    @property
    def union_id(self):
        return self.customer.unionid

    @property
    def open_id(self):
        return self.customer.openid

    @property
    def fans_count(self):
        return self.fans.count()

    @property
    def fans_count_dict(cls):
        if not hasattr(cls, '_fans_count_dict_'):
            group_cnt = GroupFans.objects.values("group_id").annotate(total=Count('id'))
            cls._fans_count_dict_ = {item['group_id']: item['total'] for item in group_cnt}
        return cls._fans_count_dict_

    @property
    def gifted_count_dict(cls):
        """
            已发礼物的用户数
        """
        if not hasattr(cls, '_gifted_count_dict_'):
            # group_cnt = GroupFans.objects.exclude(gifted=None).values("group_id").annotate(total=Count('id'))
            group_cnt = ActivityUsers.objects.exclude(gifted=None).values("group_id").annotate(total=Count('id'))
            cls._gifted_count_dict_ = {item['group_id']: item['total'] for item in group_cnt}
        return cls._gifted_count_dict_

    @property
    def gift_count_dict(cls):
        """
            将发礼物的粉丝数
        """
        if not hasattr(cls, '_gift_count_dict_'):
            group_cnt = GroupFans.objects.exclude(gifted=None).values("group_id").annotate(total=Count('id'))
            cls._gift_count_dict_ = {item['group_id']: item['total'] for item in group_cnt}
        return cls._gift_count_dict_

    @property
    def modified_display(self):
        return self.modified.strftime("%Y-%m-%d")

    @staticmethod
    def get_or_create(admin, mama_id):
        g = GroupMamaAdministrator.objects.filter(admin=admin, mama_id=mama_id).first()
        if not g:
            g = GroupMamaAdministrator(
                admin=admin, mama_id=mama_id, group_uni_key=mama_id
            )
            g.save()
        return g


class GroupFans(BaseModel):
    class Meta:
        app_label = 'weixingroup'
        verbose_name = u'小鹿微信群粉丝'
        verbose_name_plural = u'小鹿微信群粉丝表'

    group = models.ForeignKey(GroupMamaAdministrator, related_name='fans')
    user_id = models.IntegerField(null=True, blank=True, verbose_name=u'关联用户')
    head_img_url = models.CharField(max_length=256, verbose_name=u'用户微信头像')
    nick = models.CharField(max_length=100, verbose_name=u'用户微信昵称')
    union_id = models.CharField(max_length=100, verbose_name=u'用户微信unionid', unique=True)
    open_id = models.CharField(max_length=100, verbose_name=u'用户微信openid')
    gifted = models.IntegerField(null=True, verbose_name=u'获取赠品', help_text=u'1凉席')

    @staticmethod
    def create(group, user_id, head_img_url, nick, union_id, open_id):
        gf = GroupFans(group=group,
                       user_id=user_id,
                       head_img_url=head_img_url,
                       nick=nick,
                       union_id=union_id,
                       open_id=open_id
                       )
        gf.save()
        return gf

    def get_from_customer(self):
        return self.group.customer


def write_download_unionid_record(sender, instance, created, **kwargs):
    from .tasks import task_write_download_unionid_record
    task_write_download_unionid_record.delay(instance)


post_save.connect(write_download_unionid_record, sender=GroupFans)


class ActivityUsers(BaseModel):
    class Meta:
        app_label = 'weixingroup'
        verbose_name = u'参与用户'
        verbose_name_plural = u'参与用户列表'
        unique_together = ('activity', 'user_id')

    activity = models.ForeignKey(ActivityEntry)
    user_id = models.IntegerField()
    gifted = models.IntegerField(null=True, verbose_name=u'获取赠品', help_text=u'1凉席')
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


class ActivityStat(BaseModel):
    class Meta:
        app_label = 'weixingroup'
        verbose_name = u'微信活动参与用户统计'
        verbose_name_plural = u'微信活动参与用户统计列表'

    activity = models.ForeignKey(ActivityEntry)
    group = models.ForeignKey(GroupMamaAdministrator, related_name='group')
    join_user_cnt = models.IntegerField(default=0, verbose_name=u'微信群参与用户计数')
    active_user_cnt = models.IntegerField(default=0, verbose_name=u'本次活动激活用户计数')

    def update(self):
        self.join_user_cnt = GroupFans.objects.count()
        self.active_user_cnt = ActivityUsers.objects.filter(activity=self.activity).count()
        self.save()
