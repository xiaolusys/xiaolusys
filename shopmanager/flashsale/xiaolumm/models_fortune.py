# coding=utf-8
from django.db import models
from core.models import BaseModel
from django.db.models.signals import post_save

import datetime


def gen_ordercarry_unikey(mama_id, order_id):
    return '-'.join(['order', str(mama_id), order_id])

def gen_awardcarry_unikey(mama_id, order_id):
    return '-'.join(['award', str(mama_id), order_id])

def gen_clickcarry_unikey(mama_id, date):
    return '-'.join(['click', str(mama_id), date])

def gen_activevalue_unikey(value_type, mama_id, date, order_id, contributor_id):
    if value_type == 1: # click                                                                                                                                                                 
        return '-'.join(['active',str(mama_id),str(value_type),str(date)])
    if value_type == 2: # order                                                                                                                                                                 
        return '-'.join(['active',str(mama_id),str(value_type),str(date),str(order_id)])
    if value_type == 3: # referal                                                                                                                                                               
        return '-'.join(['active',str(mama_id),str(value_type),str(contributor_id)])
    if value_type == 4: # fans                                                                                                                                                                  
        return '-'.join(['active',str(mama_id),str(value_type),str(contributor_id)])
    return ""


def get_choice_name(choices, val):
    """
    iterate over choices and find the name for this val
    """
    name = ""
    for entry in choices:
        if entry[0] == val:
            name = entry[1]
    return name


class MamaFortune(BaseModel):
    mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'小鹿妈妈id')
    mama_name = models.CharField(max_length=32, blank=True, verbose_name=u'名称')
    mam_level = models.IntegerField(default=0, verbose_name=u'级别')
    cash_num = models.IntegerField(default=0, verbose_name=u'余额')
    fans_num = models.IntegerField(default=0, verbose_name=u'粉丝数')
    invite_num = models.IntegerField(default=0, verbose_name=u'邀请数')
    order_num = models.IntegerField(default=0, verbose_name=u'订单数')
    carry_num = models.IntegerField(default=0, verbose_name=u'累计收益数')
    active_value_num = models.IntegerField(default=0, verbose_name=u'活跃数')
    today_visitor_num = models.IntegerField(default=0, verbose_name=u'今日访客数')

    class Meta:
        db_table = 'flashsale_xlmm_fortune'
        verbose_name = u'妈妈财富表'
        verbose_name_plural = u'妈妈财富列表'

    def __unicode__(self):
        return '%s,%s' % (self.mama_id, self.mama_name)

    def cash_num_display(self):
        return float('%.2f' %(self.cash_num * 0.01))

    def carry_num_display(self):
        return float('%.2f' %(self.carry_num * 0.01))



class CarryRecord(BaseModel):
    CARRY_TYPES = ((1, u'返现'),(2, u'佣金'),(3, u'奖金'),)
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'取消'),)
    
    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    carry_num = models.IntegerField(default=0, verbose_name=u'收益数')
    carry_type = models.IntegerField(default=0, choices=CARRY_TYPES, verbose_name=u'收益类型') #返/佣/奖
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_carry_record'
        verbose_name = u'妈妈收入记录'
        verbose_name_plural = u'妈妈收入记录列表'

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


def carryrecord_creation_update_mamafortune(sender, instance, created, **kwargs):
    """
    post_save signal only deal with creation
    """
    from flashsale.xiaolumm import tasks_mama

    print "carryrecord save signal +++", created
    if not created:
        return 
    
    mama_id = instance.mama_id
    amount  = instance.carry_num

    if instance.is_click_carry():
        # dont do anything
        return
    
    if instance.is_award_carry() and instance.is_carry_confirmed():
        # award carry has to be confirmed on creation
        action_key = "32" # increment both cash and carry
        tasks_mama.increment_mamafortune_cash_and_carry.s(mama_id, amount, action_key)()
        return
    
    if instance.is_order_carry():
        if instance.is_carry_pending():
            print "is_carry_pending"
            action_key = "31" # increment carry only
            tasks_mama.increment_mamafortune_cash_and_carry.s(mama_id, amount, action_key)()
        if instance.is_carry_confirmed(): 
            action_key = "32" # increment cash and carry
            tasks_mama.increment_mamafortune_cash_and_carry.s(mama_id, amount, action_key)()
        return


post_save.connect(carryrecord_creation_update_mamafortune, 
                  sender=CarryRecord, dispatch_uid='post_save_carry_record')


class OrderCarry(BaseModel):
    CARRY_TYPES = ((1, u'Web直接订单'),(2, u'App粉丝订单'),(3, u'下属订单'),)
    STATUS_TYPES = ((0, u'未付款'),(1, u'待确定'), (2, u'已确定'), (3, u'取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    order_id = models.CharField(max_length=64, blank=True, verbose_name=u'订单ID')
    order_value = models.IntegerField(default=0, verbose_name=u'订单金额')
    carry_num = models.IntegerField(default=0, verbose_name=u'提成金额')
    carry_type = models.IntegerField(default=1, choices=CARRY_TYPES, verbose_name=u'提成类型') #直接订单提成/粉丝订单提成/下属订单提成
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
        verbose_name = u'订单提成'
        verbose_name_plural = u'订单提成列表'

    def __unicode__(self):
        return '%s,%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num,self.date_field)

    def carry_type_name(self):
        return get_choice_name(self.CARRY_TYPES, self.carry_type)

    def order_value_display(self):
        return '%.2f' %(self.order_value * 0.01)

    def carry_num_display(self):
        return float('%.2f' %(self.carry_num * 0.01))

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

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
    from flashsale.xiaolumm import tasks_mama

    print "signaled ++"
    carryrecord_type = 2 # order carry
    tasks_mama.update_carryrecord.s(instance, carryrecord_type)()

    if instance.is_direct_or_fans_carry():
        # find out parent mama_id
        referal_relationships = ReferalRelationship.objects.filter(referal_to_mama_id=instance.mama_id)
        if referal_relationships.count() > 0:
            tasks_mama.update_second_level_ordercarry.s(referal_relationships[0], instance)()
        

post_save.connect(ordercarry_update_carryrecord,
                  sender=OrderCarry, dispatch_uid='post_save_order_carry')

def ordercarry_update_activevalue(sender, instance, created, **kwargs):
    from flashsale.xiaolumm import tasks_mama
    tasks_mama.task_ordercarry_update_activevalue.s(instance)()

post_save.connect(ordercarry_update_activevalue,
                  sender=OrderCarry, dispatch_uid='post_save_order_carry_update_active_value')


class AwardCarry(BaseModel):
    AWARD_TYPES = ((1, u'直荐奖励'),(2, u'团队奖励'),)
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    carry_num = models.IntegerField(default=0, verbose_name=u'奖励金额')
    carry_type = models.IntegerField(default=0, choices=AWARD_TYPES, verbose_name=u'奖励类型') #直接推荐奖励/团队成员奖励
    contributor_nick = models.CharField(max_length=64, blank=True, verbose_name=u'贡献者昵称')
    contributor_img  = models.CharField(max_length=256, blank=True, verbose_name=u'贡献者头像')    
    contributor_mama_id  = models.BigIntegerField(default=0, verbose_name=u'贡献者mama_id')
    carry_plan_name = models.CharField(max_length=32,blank=True,verbose_name=u'佣金计划')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_award_carry'
        verbose_name = u'奖励'
        verbose_name_plural = u'奖励列表'

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
    from flashsale.xiaolumm import tasks_mama
    
    carryrecord_type = 3 # award carry
    tasks_mama.update_carryrecord.s(instance, carryrecord_type)()


post_save.connect(awardcarry_update_carryrecord,
                  sender=AwardCarry, dispatch_uid='post_save_award_carry')


    
class ClickCarry(BaseModel):
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    init_click_num = models.IntegerField(default=0, verbose_name=u'初始点击数')
    init_order_num = models.IntegerField(default=0, verbose_name=u'初始订单人数') 
    init_click_price = models.IntegerField(default=0, verbose_name=u'初始点击价')
    init_click_limit = models.IntegerField(default=0, verbose_name=u'初始点击上限')
    confirmed_click_num = models.IntegerField(default=0, verbose_name=u'确定点击数')
    confirmed_order_num = models.IntegerField(default=0, verbose_name=u'确定订单人数') 
    confirmed_click_price = models.IntegerField(default=0, verbose_name=u'确定点击价')
    confirmed_click_limit = models.IntegerField(default=0, verbose_name=u'确定点击上限')
    carry_plan_name = models.CharField(max_length=32,blank=True,verbose_name=u'佣金计划')
    total_value = models.IntegerField(default=0, verbose_name=u'点击总价')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID') #date+mama_id
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_click_carry'
        verbose_name = u'点击返现'
        verbose_name_plural = u'点击返现列表'

    def __unicode__(self):
        return '%s,%s' % (self.mama_id, self.total_value)


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
    from flashsale.xiaolumm import tasks_mama
    tasks_mama.update_carryrecord_carry_num.s(instance)()


post_save.connect(clickcarry_update_carryrecord,
                  sender=ClickCarry, dispatch_uid='post_save_click_carry')


class ActiveValue(BaseModel):
    VALUE_MAP = {"1":1, "2":10, "3":50, "4":5}
    VALUE_TYPES = ((1, u'点击'),(2, u'订单'), (3, u'推荐'), (4, u'粉丝'),)
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'已取消'), (4, u'已过期'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    value_num = models.IntegerField(default=0, verbose_name=u'活跃值')
    value_type = models.IntegerField(default=0, choices=VALUE_TYPES, verbose_name=u'类型') #点击/订单/推荐/粉丝
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID') #
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_active_value_record'
        verbose_name = u'活跃值'
        verbose_name_plural = u'活跃值列表'

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
    from flashsale.xiaolumm.tasks_mama import task_activevale_update_mama_fortune
    if created and instance.status == 2:
        task_activevale_update_mama_fortune(instance, 'incr')

post_save.connect(activevalue_update_mamafortune,
                  sender=ClickCarry, dispatch_uid='post_save_active_value')


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
        verbose_name = u'推荐关系'
        verbose_name_plural = u'推荐关系列表'


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
        verbose_name = u'团队关系'
        verbose_name_plural = u'团队关系列表'
