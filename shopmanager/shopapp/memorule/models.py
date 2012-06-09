__author__ = 'meixqhi'
from django.db import models

RULE_STATUS = (
    ('US',u'\u4f7f\u7528'),
    ('SX',u'\u5931\u6548'),
)
SCOPE_CHOICE = (
    ('trade',u'\u4ea4\u6613\u57df'),
    ('product',u'\u5546\u54c1\u57df'),
)
class TradeRule(models.Model):

    formula     = models.CharField(max_length=64,blank=True)
    match_tpl_memo = models.CharField(max_length=64,blank=True)

    unmatch_tpl_memo = models.CharField(max_length=64,blank=True)
    memo        = models.CharField(max_length=64,blank=True)

    priority    = models.IntegerField()
    opposite_ids  = models.CharField(max_length=32,blank=True)

    scope       = models.CharField(max_length=10,choices=SCOPE_CHOICE)
    status      = models.CharField(max_length=2,choices=RULE_STATUS)

    class Meta:
        db_table = 'shop_app_traderule'
