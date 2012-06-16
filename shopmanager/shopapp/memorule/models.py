__author__ = 'meixqhi'
import json
from django.db import models
from shopback.items.models import Item

RULE_STATUS = (
    ('US',u'\u4f7f\u7528'),
    ('SX',u'\u5931\u6548'),
)
SCOPE_CHOICE = (
    ('trade',u'\u4ea4\u6613\u57df'),
    ('product',u'\u5546\u54c1\u57df'),
)
class TradeRule(models.Model):

    formula     = models.CharField(max_length=64,blank=True,verbose_name=u'\u89c4\u5219\u516c\u5f0f')
    memo        = models.CharField(max_length=64,blank=True,verbose_name=u'\u89c4\u5219\u7559\u8a00')

    formula_desc = models.TextField(max_length=256,blank=True,verbose_name=u'\u89c4\u5219\u63cf\u8ff0')

    scope       = models.CharField(max_length=10,choices=SCOPE_CHOICE,verbose_name=u'\u89c4\u5219\u8303\u56f4')
    status      = models.CharField(max_length=2,choices=RULE_STATUS,verbose_name=u'\u89c4\u5219\u72b6\u6001')

    items        = models.ManyToManyField(Item,related_name='rules',symmetrical=False,db_table='shop_app_itemrulemap')
    class Meta:
        db_table = 'shop_app_traderule'
        verbose_name = u'\u8ba2\u5355\u89c4\u5219'




FIELD_TYPE_CHOICE = (
    ('single',u'\u5355\u9009'),
    ('check',u'\u590d\u9009'),
    ('text',u'\u6587\u672c'),
)
class RuleFieldType(models.Model):

    field_name = models.CharField(max_length=64,primary_key=True)
    field_type = models.CharField(max_length=10,choices=FIELD_TYPE_CHOICE)

    alias      = models.CharField(max_length=64)
    default_value = models.TextField(max_length=256,blank=True)

    class Meta:
        db_table = 'shop_app_rulefieldtype'

    def __unicode__(self):
        return self.field_name+self.field_type




class ProductRuleField(models.Model):

    out_iid    = models.CharField(max_length=64,db_index=True)
    field      = models.ForeignKey(RuleFieldType)

    custom_alias   = models.CharField(max_length=256,blank=True)
    custom_default = models.TextField(max_length=256,blank=True)

    class Meta:
        db_table = 'shop_app_productrulefield'

    @property
    def alias(self):
        return self.custom_alias or self.field.alias

    @property
    def default(self):
        value = self.custom_default or self.field.default_value
        if self.field.field_type == 'check' or self.field.field_type == 'single':
            return value.split('(,|&)')
        return value

    def to_json(self):
        return [self.field.field_name,self.alias,self.field.field_type,self.default]