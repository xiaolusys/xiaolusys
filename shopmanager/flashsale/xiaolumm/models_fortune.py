# coding=utf-8
from django.db import models
from core.models import BaseModel


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
        return self.cash_num * 0.01

    def carry_num_display(self):
        return self.carry_num * 0.01




class CarryRecord(BaseModel):
    CARRY_TYPES = ((1, u'返现'),(2, u'佣金'),(3, u'奖金'),)
    STATUS_TYPES = ((0, u'待确定'),(1, u'已确定'),(2, u'取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    carry_num = models.IntegerField(default=0, verbose_name=u'收益数')
    carry_type = models.IntegerField(default=0, choices=CARRY_TYPES, verbose_name=u'收益类型') #返/佣/奖
    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_carry_record'
        verbose_name = u'妈妈收入记录'
        verbose_name_plural = u'妈妈收入记录列表'

    def __unicode__(self):
        return '%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num)
    
    def carry_num_display(self):
        return self.carry_num * 0.01


class OrderCarry(BaseModel):
    CARRY_TYPES = ((1, u'直接订单提成'),(2, u'粉丝订单提成'),(3, u'下属订单提成'),)
    STATUS_TYPES = ((0, u'待确定'),(1, u'已确定'),(2, u'取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    order_id = models.BigIntegerField(default=0, verbose_name=u'订单ID')
    order_value = models.IntegerField(default=0, verbose_name=u'订单金额')
    carry_num = models.IntegerField(default=0, verbose_name=u'提成金额')
    carry_type = models.IntegerField(default=0, choices=CARRY_TYPES, verbose_name=u'提成类型') #直接订单提成/粉丝订单提成/下属订单提成
    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'sku名称')
    sku_img  = models.CharField(max_length=256, blank=True, verbose_name=u'sku图片')
    contributor_nick = models.CharField(max_length=64, blank=True, verbose_name=u'贡献者昵称')
    contributor_img  = models.CharField(max_length=256, blank=True, verbose_name=u'贡献者头像')
    contributor_id  = models.BigIntegerField(default=0, verbose_name=u'贡献者ID')
    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_order_carry'
        verbose_name = u'订单提成'
        verbose_name_plural = u'订单提成列表'

    def __unicode__(self):
        return '%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num)

    def order_value_display(self):
        return self.order_value * 0.01

    def carry_num_display(self):
        return self.carry_num * 0.01


class AwardCarry(BaseModel):
    AWARD_TYPES = ((1, u'直接推荐奖励'),(2, u'/团队成员奖励'),)
    STATUS_TYPES = ((0, u'待确定'),(1, u'已确定'),(2, u'取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    award_num = models.IntegerField(default=0, verbose_name=u'奖励金额')
    award_type = models.IntegerField(default=0, choices=AWARD_TYPES, verbose_name=u'奖励类型') #直接推荐奖励/团队成员奖励
    contributor_nick = models.CharField(max_length=64, blank=True, verbose_name=u'贡献者昵称')
    contributor_img  = models.CharField(max_length=256, blank=True, verbose_name=u'贡献者头像')    
    contributor_id  = models.BigIntegerField(default=0, verbose_name=u'贡献者ID')
    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_award_carry'
        verbose_name = u'奖励'
        verbose_name_plural = u'奖励列表'

    def __unicode__(self):
        return '%s,%s,%s' % (self.mama_id, self.award_type, self.award_num)

    def award_num_display(self):
        return self.award_num * 0.01
    
    
class ClickCarry(BaseModel):
    STATUS_TYPES = ((0, u'待确定'),(1, u'已确定'),(2, u'取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    init_click_num = models.IntegerField(default=0, verbose_name=u'初始点击数')
    init_order_num = models.IntegerField(default=0, verbose_name=u'初始订单人数') 
    init_click_price = models.IntegerField(default=0, verbose_name=u'初始点击价')
    init_click_limit = models.IntegerField(default=0, verbose_name=u'初始点击上限')
    confirmed_click_num = models.IntegerField(default=0, verbose_name=u'确定点击数')
    confirmed_order_num = models.IntegerField(default=0, verbose_name=u'确定订单人数') 
    confirmed_click_price = models.IntegerField(default=0, verbose_name=u'确定点击价')
    confirmed_click_limit = models.IntegerField(default=0, verbose_name=u'确定点击上限')
    total_value = models.IntegerField(default=0, verbose_name=u'点击总价')
    mixed_contributor = models.CharField(max_length=64, blank=True, unique=True, verbose_name=u'贡献者') # date+mama_id
    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_click_carry'
        verbose_name = u'点击返现'
        verbose_name_plural = u'点击返现列表'

    def __unicode__(self):
        return '%s,%s' % (self.mama_id, self.total_value)


    def init_click_price_display(self):
        return self.init_click_price * 0.01

    def confirmed_click_price_display(self):
        return self.confirmed_click_price * 0.01

    def total_value_display(self):
        return self.total_value * 0.01


class ActiveValue(BaseModel):
    VALUE_TYPES = ((1, u'点击'),(2, u'订单'), (3, u'推荐'), (4, u'粉丝'),)
    STATUS_TYPES = ((0, u'待确定'),(1, u'已确定'),(2, u'取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    value_num = models.IntegerField(default=0, verbose_name=u'活跃值')
    value_type = models.IntegerField(default=0, choices=VALUE_TYPES, verbose_name=u'类型') #点击/订单/推荐/粉丝
    mixed_contributor = models.CharField(max_length=64, blank=True, unique=True, verbose_name=u'贡献者')
    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态') #待确定/已确定/取消
    
    class Meta:
        db_table = 'flashsale_xlmm_active_value_record'
        verbose_name = u'活跃值'
        verbose_name_plural = u'活跃值列表'

    def __unicode__(self):
        return '%s,%s,%s' % (self.mama_id, self.value_type, self.value_num)


    def value_num_display(self):
        return self.value_num * 0.01

