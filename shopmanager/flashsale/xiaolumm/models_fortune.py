# coding=utf-8
from django.db import models
from core.models import BaseModel
from django.db.models.signals import post_save
from django.conf import settings

import datetime


def get_choice_name(choices, val):
    """
    iterate over choices and find the name for this val
    """
    name = ""
    for entry in choices:
        if entry[0] == val:
            name = entry[1]
    return name

#
# Use from flashsale.xiaolumm.models import CashOut 
#
#class CashOut(BaseModel):
#    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'取消'),)
#    mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'小鹿妈妈id')
#    amount = models.IntegerField(default=0, verbose_name=u'数额')
#    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态')
#
#    class Meta:
#        db_table = 'flashsale_xlmm_cashout'
#        verbose_name = u'妈妈提现'
#        verbose_name_plural = u'妈妈提现列表'
#
#    def is_confirmed(self):
#        return self.status == 2
#
#    def amount_display(self):
#        return float('%.2f' % (self.amount * 0.01))


# The time to switch to xiaolumama v2.0
MAMA_FORTUNE_HISTORY_LAST_DAY = datetime.date(2016,03,24)


class MamaFortune(BaseModel):
    MAMA_LEVELS = ((0, u'新手妈妈'),(1, u'金牌妈妈'),(2, u'钻石妈妈'),(3, u'皇冠妈妈'),(4,u'金冠妈妈'))
    mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'小鹿妈妈id')
    mama_name = models.CharField(max_length=32, blank=True, verbose_name=u'名称')
    mama_level = models.IntegerField(default=0, choices=MAMA_LEVELS, verbose_name=u'级别')

    fans_num = models.IntegerField(default=0, verbose_name=u'粉丝数')
    invite_num = models.IntegerField(default=0, verbose_name=u'邀请数')
    order_num = models.IntegerField(default=0, verbose_name=u'订单数')
    
    carry_pending = models.IntegerField(default=0, verbose_name=u'待确定收益')
    carry_confirmed = models.IntegerField(default=0, verbose_name=u'已确定收益')
    carry_cashout = models.IntegerField(default=0, verbose_name=u'已提现金额')

    history_pending = models.IntegerField(default=0, verbose_name=u'历史待确定收益')
    history_confirmed = models.IntegerField(default=0, verbose_name=u'历史已确定收益')
    history_last_day = models.DateField(default=MAMA_FORTUNE_HISTORY_LAST_DAY, verbose_name=u'历史结束日期')

    active_value_num = models.IntegerField(default=0, verbose_name=u'活跃值')
    today_visitor_num = models.IntegerField(default=0, verbose_name=u'今日访客数')

    class Meta:
        db_table = 'flashsale_xlmm_fortune'
        verbose_name = u'V2/妈妈财富表'
        verbose_name_plural = u'V2/妈妈财富列表'

    def __unicode__(self):
        return '%s,%s' % (self.mama_id, self.mama_name)

    def mama_level_display(self):
        return get_choice_name(self.MAMA_LEVELS, self.mama_level)

    def carry_num_display(self):
        """
        累计收益数
        """
        total = self.carry_pending + self.carry_confirmed + self.history_pending + self.history_confirmed
        return float('%.2f' % (total * 0.01))

    def cash_num_display(self):
        """
        余额
        """
        total = self.carry_confirmed + self.history_confirmed - self.carry_cashout
        return float('%.2f' % (total * 0.01))

    def carry_pending_display(self):
        total = self.carry_pending + self.history_pending
        return float('%.2f' % (total * 0.01))

    def carry_confirmed_display(self):
        total = self.carry_confirmed + self.history_confirmed
        return float('%.2f' % (total * 0.01))

    def carry_cashout_display(self):
        return float('%.2f' % (self.carry_cashout * 0.01))

    def mama_event_link(self):
        return "%s" % settings.M_SITE_URL

class DailyStats(BaseModel):
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), )
    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    today_visitor_num = models.IntegerField(default=0, verbose_name=u'今日访客数')
    today_order_num = models.IntegerField(default=0, verbose_name=u'今日订单数')
    today_carry_num = models.IntegerField(default=0, verbose_name=u'今日收益数')
    today_active_value = models.IntegerField(default=0, verbose_name=u'今日活跃值')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    status = models.IntegerField(default=1, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定

    class Meta:
        db_table = 'flashsale_xlmm_daily_stats'
        verbose_name = u'V2/每日数据'
        verbose_name_plural = u'V2/每日数据列表'

    def today_carry_num_display(self):
        return float('%.2f' % (self.today_carry_num * 0.01))

def confirm_previous_dailystats(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_dailystats
    if created:
        mama_id = instance.mama_id
        date_field = instance.date_field
        tasks_mama_dailystats.task_confirm_previous_dailystats.delay(mama_id, date_field, 2)


post_save.connect(confirm_previous_dailystats,
                  sender=DailyStats, dispatch_uid='post_save_confirm_previous_dailystats')

    

class CarryRecord(BaseModel):
    CARRY_TYPES = ((1, u'返现'),(2, u'佣金'),(3, u'奖金'),)
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'取消'),)
    
    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    carry_num = models.IntegerField(default=0, verbose_name=u'收益数')
    carry_type = models.IntegerField(default=0, choices=CARRY_TYPES, verbose_name=u'收益类型') #返/佣/奖
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_carry_record'
        verbose_name = u'V2/妈妈收入记录'
        verbose_name_plural = u'V2/妈妈收入记录列表'

    def __unicode__(self):
        return '%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num)
    
    def carry_type_name(self):
        return get_choice_name(self.CARRY_TYPES, self.carry_type)
    
    def carry_num_display(self):
        return float('%.2f' %(self.carry_num * 0.01))

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)
        
        
    def is_carry_confirmed(self):
        return self.status == 2

    def is_carry_pending(self):
        return self.status == 1

    def is_carry_canceled(self):
        return self.status == 0

    def is_award_carry(self):
        return self.carry_type == 3

    def is_order_carry(self):
        return self.carry_type == 2

    def is_click_carry(self):
        return self.carry_type == 1


def carryrecord_update_mamafortune(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_fortune
    tasks_mama_fortune.task_carryrecord_update_mamafortune.delay(instance.mama_id)

    from flashsale.xiaolumm import tasks_mama_dailystats
    tasks_mama_dailystats.task_carryrecord_update_dailystats.delay(instance.mama_id, instance.date_field)

post_save.connect(carryrecord_update_mamafortune, 
                  sender=CarryRecord, dispatch_uid='post_save_carryrecord_update_mamafortune')


class OrderCarry(BaseModel):
    CARRY_TYPES = ((1, u'Web直接订单'),(2, u'App粉丝订单'),(3, u'下属订单'),)
    STATUS_TYPES = ((0, u'待付款'),(1, u'待确定'), (2, u'已确定'), (3, u'买家取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    order_id = models.CharField(max_length=64, blank=True, verbose_name=u'订单ID')
    order_value = models.IntegerField(default=0, verbose_name=u'订单金额')
    carry_num = models.IntegerField(default=0, verbose_name=u'提成金额')
    carry_type = models.IntegerField(default=1, choices=CARRY_TYPES, verbose_name=u'提成类型') #直接订单提成/粉丝订单提成/下属订单提成
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'sku名称')
    sku_img  = models.CharField(max_length=256, blank=True, verbose_name=u'sku图片')
    contributor_nick = models.CharField(max_length=64, blank=True, verbose_name=u'贡献者昵称')
    contributor_img  = models.CharField(max_length=256, blank=True, verbose_name=u'贡献者头像')
    contributor_id  = models.BigIntegerField(default=0, verbose_name=u'贡献者ID')
    carry_plan_name = models.CharField(max_length=32,blank=True,verbose_name=u'佣金计划')
    agency_level = models.IntegerField(default=0,verbose_name=u'佣金级别')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID') #
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_order_carry'
        verbose_name = u'V2/订单提成'
        verbose_name_plural = u'V2/订单提成列表'

    def __unicode__(self):
        return '%s,%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num,self.date_field)

    def carry_type_name(self):
        # web order, we currently dont show name
        if self.carry_type == 1: 
            return ''
        return get_choice_name(self.CARRY_TYPES, self.carry_type)

    def order_value_display(self):
        return '%.2f' %(self.order_value * 0.01)

    def carry_num_display(self):
        return float('%.2f' %(self.carry_num * 0.01))

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def contributor_nick_display(self):
        if self.contributor_nick == "":
            return u"匿名用户"
        return self.contributor_nick

    def is_pending(self):
        return self.status == 1

    def is_confirmed(self):
        return self.status == 2

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None

    def is_direct_or_fans_carry(self):
        return self.carry_type == 1 or self.carry_type == 2


def ordercarry_update_carryrecord(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_carryrecord
    tasks_mama_carryrecord.task_ordercarry_update_carryrecord.delay(instance)

post_save.connect(ordercarry_update_carryrecord,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_update_carryrecord')


def ordercarry_update_ordercarry(sender, instance, created, **kwargs):
    if instance.is_direct_or_fans_carry():
        # find out parent mama_id
        referal_relationships = ReferalRelationship.objects.filter(referal_to_mama_id=instance.mama_id)
        if referal_relationships.count() > 0:
            from flashsale.xiaolumm import tasks_mama
            referal_relationship = referal_relationships[0]
            tasks_mama.task_update_second_level_ordercarry.delay(referal_relationship, instance)
        
post_save.connect(ordercarry_update_ordercarry,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_update_ordercarry')


def ordercarry_update_activevalue(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_activevalue
    tasks_mama_activevalue.task_ordercarry_update_activevalue.delay(instance.uni_key)

post_save.connect(ordercarry_update_activevalue,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_update_activevalue')


def ordercarry_update_order_number(sender, instance, created, **kwargs):
    mama_id = instance.mama_id
    date_field = instance.date_field

    from flashsale.xiaolumm import tasks_mama_clickcarry
    tasks_mama_clickcarry.task_update_clickcarry_order_number.delay(mama_id, date_field)

    from flashsale.xiaolumm import tasks_mama_fortune
    tasks_mama_fortune.task_update_mamafortune_order_num.delay(mama_id)

    if created:
        from flashsale.xiaolumm import tasks_mama_dailystats
        tasks_mama_dailystats.task_ordercarry_increment_dailystats.delay(mama_id, date_field)

post_save.connect(ordercarry_update_order_number,
                  sender=OrderCarry, dispatch_uid='post_save_order_carry_update_order_number')





class AwardCarry(BaseModel):
    AWARD_TYPES = ((1, u'直荐奖励'),(2, u'团队奖励'),)
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    carry_num = models.IntegerField(default=0, verbose_name=u'奖励金额')
    carry_type = models.IntegerField(default=0, choices=AWARD_TYPES, verbose_name=u'奖励类型') #直接推荐奖励/团队成员奖励
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    contributor_nick = models.CharField(max_length=64, blank=True, verbose_name=u'贡献者昵称')
    contributor_img  = models.CharField(max_length=256, blank=True, verbose_name=u'贡献者头像')    
    contributor_mama_id  = models.BigIntegerField(default=0, verbose_name=u'贡献者mama_id')
    carry_plan_name = models.CharField(max_length=32,blank=True,verbose_name=u'佣金计划')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_award_carry'
        verbose_name = u'V2/妈妈邀请奖励'
        verbose_name_plural = u'V2/妈妈邀请奖励列表'

    def __unicode__(self):
        return '%s,%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num, self.date_field)

    def is_pending(self):
        return self.status == 1

    def is_confirmed(self):
        return self.status == 2
    
    def carry_type_name(self):
        return get_choice_name(self.AWARD_TYPES, self.carry_type)

    def carry_num_display(self):
        return float('%.2f' %(self.carry_num * 0.01))

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None


def awardcarry_update_carryrecord(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_carryrecord
    tasks_mama_carryrecord.task_awardcarry_update_carryrecord.delay(instance)


post_save.connect(awardcarry_update_carryrecord,
                  sender=AwardCarry, dispatch_uid='post_save_awardcarry_update_carryrecord')


from core.fields import JSONCharMyField
class ClickPlan(BaseModel):
    STATUS_TYPES = ((0, u'使用'), (1, u'取消'),)
    name = models.CharField(max_length=32, verbose_name=u'名字')
    
    # {"0":[10, 10], "1":[20, 60], "2":[30, 110], "3":[40, 160], "4":[50, 210], "5":[60, 260]}
    order_rules = JSONCharMyField(max_length=256, blank=True, default={}, verbose_name=u'规则')
    max_order_num = models.IntegerField(default=0, verbose_name=u'最大订单人数') 
    
    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态') 
    
    class Meta:
        db_table = 'flashsale_xlmm_click_plan'
        verbose_name = u'V2/点击计划'
        verbose_name_plural = u'V2/点击计划列表'


    
class ClickCarry(BaseModel):
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    click_num = models.IntegerField(default=0, verbose_name=u'初始点击数')
    init_order_num = models.IntegerField(default=0, verbose_name=u'初始订单人数') 
    init_click_price = models.IntegerField(default=0, verbose_name=u'初始点击价')
    init_click_limit = models.IntegerField(default=0, verbose_name=u'初始点击上限')
    confirmed_order_num = models.IntegerField(default=0, verbose_name=u'确定订单人数') 
    confirmed_click_price = models.IntegerField(default=0, verbose_name=u'确定点击价')
    confirmed_click_limit = models.IntegerField(default=0, verbose_name=u'确定点击上限')
    carry_plan_name = models.CharField(max_length=32,blank=True,verbose_name=u'佣金计划')
    carry_plan_id = models.IntegerField(default=1, verbose_name=u'佣金计划ID')
    total_value = models.IntegerField(default=0, verbose_name=u'点击总价')
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID') #date+mama_id
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_click_carry'
        verbose_name = u'V2/妈妈点击返现'
        verbose_name_plural = u'V2/妈妈点击返现列表'

    def __unicode__(self):
        return '%s,%s' % (self.mama_id, self.total_value)

    def is_confirmed(self):
        return self.status == 2

    def init_click_price_display(self):
        return '%.2f' % (self.init_click_price * 0.01)

    def confirmed_click_price_display(self):
        return '%.2f' % (self.confirmed_click_price * 0.01)

    def total_value_display(self):
        return '%.2f' % (self.total_value * 0.01)

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None

            
def clickcarry_update_carryrecord(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_carryrecord
    tasks_mama_carryrecord.task_clickcarry_update_carryrecord.delay(instance)

post_save.connect(clickcarry_update_carryrecord,
                  sender=ClickCarry, dispatch_uid='post_save_clickcarry_update_carryrecord')


def confirm_previous_clickcarry(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_clickcarry
    if created:
        mama_id = instance.mama_id
        date_field = instance.date_field
        tasks_mama_clickcarry.task_confirm_previous_zero_order_clickcarry.delay(mama_id, date_field, 2)


post_save.connect(confirm_previous_clickcarry,
                  sender=ClickCarry, dispatch_uid='post_save_confirm_previous_clickcarry')



class ActiveValue(BaseModel):
    VALUE_MAP = {"1":1, "2":10, "3":50, "4":5}
    VALUE_TYPES = ((1, u'点击'),(2, u'订单'), (3, u'推荐'), (4, u'粉丝'),)
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'已取消'), (4, u'已过期'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    value_num = models.IntegerField(default=0, verbose_name=u'活跃值')
    value_type = models.IntegerField(default=0, choices=VALUE_TYPES, verbose_name=u'类型') #点击/订单/推荐/粉丝
    value_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID') #
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_active_value_record'
        verbose_name = u'V2/妈妈活跃值'
        verbose_name_plural = u'V2/妈妈活跃值列表'

    def __unicode__(self):
        return '%s,%s,%s' % (self.mama_id, self.value_type, self.value_num)

    def value_type_name(self):
        return get_choice_name(self.VALUE_TYPES, self.value_type)

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def is_confirmed(self):
        return self.status == 2
    
    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None


def activevalue_update_mamafortune(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_fortune
    mama_id = instance.mama_id
    tasks_mama_fortune.task_activevalue_update_mamafortune.delay(mama_id)

post_save.connect(activevalue_update_mamafortune,
                  sender=ActiveValue, dispatch_uid='post_save_activevalue_update_mamafortune')


def confirm_previous_activevalue(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama_activevalue
    if created:
        mama_id = instance.mama_id
        value_type = instance.value_type
        date_field = instance.date_field
        tasks_mama_activevalue.task_confirm_previous_activevalue.delay(mama_id, value_type, date_field, 2)

post_save.connect(confirm_previous_activevalue,
                  sender=ActiveValue, dispatch_uid='post_save_confirm_previous_activevalue')


class ReferalRelationship(BaseModel):
    """
    xiaolu mama referal relationship
    """
    referal_from_mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    referal_to_mama_id   = models.BigIntegerField(default=0, unique=True, verbose_name=u'被推荐妈妈id')    
    referal_to_mama_nick = models.CharField(max_length=64, blank=True, verbose_name=u'被推荐者昵称')
    referal_to_mama_img  = models.CharField(max_length=256, blank=True, verbose_name=u'被推荐者头像')    


    class Meta:
        db_table = 'flashsale_xlmm_referal_relationship'
        verbose_name = u'V2/妈妈推荐关系'
        verbose_name_plural = u'V2/妈妈推荐关系列表'

    def referal_to_mama_nick_display(self):
        if self.referal_to_mama_nick == "":
            return u"匿名用户"
        return self.referal_to_mama_nick


def update_mamafortune_invite_num(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm import tasks_mama_fortune
    mama_id = instance.referal_from_mama_id
    tasks_mama_fortune.task_update_mamafortune_invite_num.delay(mama_id)
    tasks_mama_fortune.task_update_mamafortune_mama_level.delay(mama_id)
    
post_save.connect(update_mamafortune_invite_num,
                  sender=ReferalRelationship, dispatch_uid='post_save_update_mamafortune_invite_num')



def update_group_relationship(sender, instance, created, **kwargs):
    if not created:
        return
    
    from flashsale.xiaolumm.tasks_mama_relationship_visitor import task_update_group_relationship
    records = ReferalRelationship.objects.filter(referal_to_mama_id=instance.referal_from_mama_id)
    if records.count() > 0:
        record = records[0]
        task_update_group_relationship.delay(record.referal_from_mama_id,instance)


post_save.connect(update_group_relationship,
                  sender=ReferalRelationship, dispatch_uid='post_save_update_group_relationship')


def referal_update_activevalue(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm.tasks_mama_activevalue import task_referal_update_activevalue
    mama_id = instance.referal_from_mama_id
    date_field = instance.created.date()
    contributor_id = instance.referal_to_mama_id
    task_referal_update_activevalue.delay(mama_id, date_field, contributor_id)

post_save.connect(referal_update_activevalue,
                  sender=ReferalRelationship, dispatch_uid='post_save_referal_update_activevalue')



def referal_update_awardcarry(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm.tasks_mama import task_referal_update_awardcarry
    task_referal_update_awardcarry.delay(instance)


post_save.connect(referal_update_awardcarry,
                  sender=ReferalRelationship, dispatch_uid='post_save_referal_update_awardcarry')



class GroupRelationship(BaseModel):
    """
    xiaolu mama group relationship
    """
    leader_mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'领队妈妈id')
    referal_from_mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'推荐妈妈id')
    member_mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'成员妈妈id')    
    member_mama_nick = models.CharField(max_length=64, blank=True, verbose_name=u'贡献者昵称')
    member_mama_img  = models.CharField(max_length=256, blank=True, verbose_name=u'贡献者头像')    

    class Meta:
        db_table = 'flashsale_xlmm_group_relationship'
        verbose_name = u'V2/妈妈团队关系'
        verbose_name_plural = u'V2/妈妈团队关系列表'


def group_update_awardcarry(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm import tasks_mama
    tasks_mama.task_group_update_awardcarry.delay(instance)
    
    from flashsale.xiaolumm import tasks_mama_fortune 
    tasks_mama_fortune.task_update_mamafortune_mama_level.delay(instance.leader_mama_id)

post_save.connect(group_update_awardcarry,
                  sender=GroupRelationship, dispatch_uid='post_save_group_update_awardcarry')


class UniqueVisitor(BaseModel):
    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    visitor_unionid = models.CharField(max_length=64,verbose_name=u"访客UnionID")
    visitor_nick = models.CharField(max_length=64, blank=True, verbose_name=u'访客昵称')
    visitor_img  = models.CharField(max_length=256, blank=True, verbose_name=u'访客头像')    
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID') #unionid+date
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    
    class Meta:
        db_table = 'flashsale_xlmm_unique_visitor'
        verbose_name = u'V2/独立访客'
        verbose_name_plural = u'V2/独立访客列表'

    def visitor_description(self):
        return u"来自微信点击访问"

    def nick_display(self):
        if self.visitor_nick == '':
            return u"匿名用户"
        return self.visitor_nick


def visitor_update_clickcarry_and_activevalue(sender, instance, created, **kwargs):
    if not created:
        return
    
    mama_id = instance.mama_id
    date_field = instance.date_field
    
    from flashsale.xiaolumm.tasks_mama_clickcarry import task_visitor_increment_clickcarry
    task_visitor_increment_clickcarry.delay(mama_id, date_field)

    from flashsale.xiaolumm.tasks_mama_activevalue import task_visitor_increment_activevalue
    task_visitor_increment_activevalue.delay(mama_id, date_field)

    from flashsale.xiaolumm.tasks_mama_dailystats import task_visitor_increment_dailystats
    task_visitor_increment_dailystats.delay(mama_id, date_field)

post_save.connect(visitor_update_clickcarry_and_activevalue,
                  sender=UniqueVisitor, dispatch_uid='post_save_visitor_update_clickcarry_and_activevalue')
