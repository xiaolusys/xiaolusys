# coding=utf-8

from django.db import models
from core.models import BaseModel
from .managers import XlmmFansManager
from flashsale.pay.models_user import Customer


class XlmmFans(BaseModel):
    xlmm = models.BigIntegerField(verbose_name='小鹿妈妈id')
    xlmm_cusid = models.BigIntegerField(db_index=True, verbose_name='小鹿妈妈用户id')
    refreal_cusid = models.BigIntegerField(db_index=True, verbose_name='推荐人用户id')
    fans_cusid = models.BigIntegerField(unique=True, verbose_name='粉丝用户id')
    fans_nick = models.CharField(max_length=32, blank=True, null=True, verbose_name='粉丝昵称')
    fans_thumbnail = models.CharField(max_length=256, blank=True, null=True, verbose_name='粉丝头像')
    objects = XlmmFansManager()

    class Meta:
        unique_together = ('xlmm', 'fans_cusid')
        db_table = 'flashsale_xlmm_fans'
        verbose_name = u'代理/粉丝表'
        verbose_name_plural = u'代理/粉丝列表'

    def __unicode__(self):
        return "<%s,%s>" % (self.xlmm, self.fans_cusid)

    def getCustomer(self):
        """ 获取粉丝在特卖客户列表中的信息 """
        try:
            cus = Customer.objects.get(id=self.fans_cusid)
            return cus
        except Customer.DoesNotExist:
            return None


from django.db.models.signals import post_save


def update_activevalue(sender, instance, created, **kwargs):
    """
    更新妈妈活跃度
    """
    if not created:
        return
    
    from flashsale.xiaolumm import tasks_mama_activevalue 
    mama_id = instance.xlmm
    fans_customer_id = instance.fans_cusid
    date_field = instance.created.date()
    tasks_mama_activevalue.task_fans_update_activevalue.s(mama_id, fans_customer_id, date_field)()


post_save.connect(update_activevalue,
                  sender=XlmmFans, dispatch_uid='post_save_update_activevalue')

def update_mamafortune_fans_num(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm import tasks_mama_fortune
    mama_id = instance.xlmm
    tasks_mama_fortune.task_update_mamafortune_fans_num.s(mama_id)()

post_save.connect(update_mamafortune_fans_num,
                  sender=XlmmFans, dispatch_uid='post_save_update_mamafortune_fans_num')


class FansNumberRecord(BaseModel):
    xlmm = models.BigIntegerField(db_index=True, verbose_name='小鹿妈妈id')
    xlmm_cusid = models.BigIntegerField(db_index=True, verbose_name='小鹿妈妈用户id')
    fans_num = models.IntegerField(default=1, verbose_name='粉丝数量')

    class Meta:
        unique_together = ('xlmm', 'xlmm_cusid')
        db_table = 'flashsale_xlmm_fans_nums'
        verbose_name = u'代理/粉丝数量表'
        verbose_name_plural = u'代理/粉丝数量列表'

    def __unicode__(self):
        return "<%s,%s>" % (self.xlmm, self.fans_num)

