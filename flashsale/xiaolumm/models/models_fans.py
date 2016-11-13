# coding=utf-8

from django.db import models
from django.db.models.signals import post_save, pre_save
from core.models import BaseModel
from flashsale.xiaolumm.managers import XlmmFansManager
from flashsale.pay.models import Customer


class XlmmFans(BaseModel):
    xlmm = models.BigIntegerField(verbose_name=u'小鹿妈妈id')
    xlmm_cusid = models.BigIntegerField(db_index=True, verbose_name=u'小鹿妈妈用户id')
    refreal_cusid = models.BigIntegerField(db_index=True, verbose_name=u'推荐人用户id')
    fans_cusid = models.BigIntegerField(unique=True, verbose_name=u'粉丝用户id')
    fans_nick = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'粉丝昵称')
    fans_thumbnail = models.CharField(max_length=256, blank=True, null=True, verbose_name=u'粉丝头像')
    objects = XlmmFansManager()

    class Meta:
        unique_together = ('xlmm', 'fans_cusid')
        db_table = 'flashsale_xlmm_fans'
        app_label = 'xiaolumm'
        verbose_name = u'代理/粉丝表'
        verbose_name_plural = u'代理/粉丝列表'

    def __unicode__(self):
        return "<%s,%s>" % (self.xlmm, self.fans_cusid)

    def getCustomer(self):
        """ 获取粉丝在特卖客户列表中的信息 """
        if not hasattr(self, '_fans_customer_'):
            self._fans_customer_ = Customer.objects.normal_customer.filter(id=self.fans_cusid).first()
        return self._fans_customer_

    @staticmethod
    def get_by_customer_id(cusid):
        return XlmmFans.objects.filter(fans_cusid=cusid).first()

    def fans_description(self):
        if self.xlmm_cusid == self.refreal_cusid:
            return u"通过您的分享成为粉丝"
        return u"来自好友的分享"

    def nick_display(self):
        if not self.fans_nick:
            return u"匿名用户"
        return self.fans_nick

    def change_mama(self, mama):
        old_mama = self.xlmm
        self.xlmm = mama.id
        self.xlmm_cusid = mama.get_mama_customer().id
        self.save()
        FansChangeMamaRecord.create(self, old_mama, self.xlmm)

    @staticmethod
    def bind_mama(customer, mama):
        if customer.getXiaolumm():  # 一元试用的也是妈妈 （除非等到冻结， 才可以成为别人粉丝）
            raise Exception(u'小鹿妈妈不能成为粉丝')
        if not XlmmFans.objects.filter(fans_cusid=customer.id).first():
            # 没有粉丝则建立粉丝
            xlmm_cusid = mama.get_mama_customer().id
            fans_cusid = customer.id
            if xlmm_cusid == fans_cusid:
                raise Exception(u'自己不能成为自己的粉丝哦~')

            XlmmFans(xlmm=mama.id, xlmm_cusid=xlmm_cusid, refreal_cusid=mama.get_mama_customer().id,
                     fans_cusid=fans_cusid, fans_nick=customer.nick, fans_thumbnail=customer.thumbnail).save()
        else:
            raise Exception(u'此粉丝已经绑定过小鹿妈妈')

    def update_nick_thumbnail(self, nick='', thumbnail=''):
        """ 更新昵称以及头像 """
        update_fields = []
        if nick and self.fans_nick != nick:
            self.fans_nick = nick
            update_fields.append('fans_nick')
        if thumbnail and self.fans_thumbnail != thumbnail:
            self.fans_thumbnail = thumbnail
            update_fields.append('fans_thumbnail')
        if update_fields:
            self.save(update_fields=update_fields)
            return True
        return False


def update_activevalue(sender, instance, created, **kwargs):
    """
    更新妈妈活跃度
    """
    if not created:
        return

    from flashsale.xiaolumm.tasks import task_fans_update_activevalue
    mama_id = instance.xlmm
    fans_customer_id = instance.fans_cusid
    date_field = instance.created.date()
    task_fans_update_activevalue.delay(mama_id, fans_customer_id, date_field)


post_save.connect(update_activevalue, sender=XlmmFans, dispatch_uid='post_save_update_activevalue')


def update_mamafortune_fans_num(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm.tasks import task_update_mamafortune_fans_num
    mama_id = instance.xlmm
    task_update_mamafortune_fans_num.delay(mama_id)


post_save.connect(update_mamafortune_fans_num,
                  sender=XlmmFans, dispatch_uid='post_save_update_mamafortune_fans_num')


def xlmmfans_xlmm_newtask(sender, instance, **kwargs):
    """
    检测新手任务：　获取第一个粉丝
    """
    from flashsale.xiaolumm.tasks import task_push_new_mama_task
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask
    from flashsale.xiaolumm.models.models import XiaoluMama

    xlmm_fans = instance
    xlmm_id = xlmm_fans.xlmm
    xlmm = XiaoluMama.objects.filter(id=xlmm_id).first()

    fans_record = XlmmFans.objects.filter(xlmm=xlmm_id).exists()

    if not fans_record:
        task_push_new_mama_task.delay(xlmm, NewMamaTask.TASK_FIRST_FANS)

pre_save.connect(xlmmfans_xlmm_newtask,
                 sender=XlmmFans, dispatch_uid='pre_save_xlmmfans_xlmm_newtask')


class FansNumberRecord(BaseModel):
    xlmm = models.BigIntegerField(db_index=True, verbose_name='小鹿妈妈id')
    xlmm_cusid = models.BigIntegerField(db_index=True, verbose_name='小鹿妈妈用户id')
    fans_num = models.IntegerField(default=1, verbose_name='粉丝数量')

    class Meta:
        unique_together = ('xlmm', 'xlmm_cusid')
        db_table = 'flashsale_xlmm_fans_nums'
        app_label = 'xiaolumm'
        verbose_name = u'代理/粉丝数量表'
        verbose_name_plural = u'代理/粉丝数量列表'

    def __unicode__(self):
        return "<%s,%s>" % (self.xlmm, self.fans_num)


def login_activate_appdownloadrecord(user):
    """
    Only check whether this user has download-relationship, if he/she has
    and that download-relationship record is not used yet, we confirm he/she is
    a fan of the related user.
    """

    from flashsale.xiaolumm.tasks import task_login_activate_appdownloadrecord, \
        task_login_create_appdownloadrecord
    task_login_activate_appdownloadrecord.delay(user)
    # task_login_create_appdownloadrecord.delay()


class FansChangeMamaRecord(BaseModel):
    fans = models.ForeignKey(XlmmFans, verbose_name=u'粉丝')
    old_xlmm = models.BigIntegerField(verbose_name=u'原小鹿妈妈id')
    new_xlmm = models.BigIntegerField(verbose_name=u'新小鹿妈妈id')

    class Meta:
        db_table = 'flashsale_xlmm_fans_change_mama'
        app_label = 'xiaolumm'
        verbose_name = u'粉丝更换妈妈记录'
        verbose_name_plural = u'粉丝更换妈妈记录'

    @staticmethod
    def create(fans, old_xlmm, new_xlmm):
        return FansChangeMamaRecord(fans, old_xlmm, new_xlmm).save()
