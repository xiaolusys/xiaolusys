from django.db import models


class Hotkey(models.Model):
    word = models.CharField(max_length=64,db_index=True)
    category_id = models.CharField(max_length=64,blank=True)
    num_people = models.IntegerField()
    num_search = models.IntegerField()
    num_click = models.IntegerField()
    num_tmall_click = models.IntegerField()
    num_cmall_click = models.IntegerField()
    num_trade = models.IntegerField()

    ads_price_cent = models.IntegerField() # price in cents
    updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.word.encode('utf8')

    @property
    def tmall_click_ratio(self):
        return round(self.num_tmall_click*1.0 / self.num_click,2)

    @property
    def cmall_click_ratio(self):
        return round(self.num_cmall_click*1.0 / self.num_click,2)

    @property
    def click_ratio(self):
        return round(self.num_click*1.0 / self.num_search,2)

    @property
    def trade_search_ratio(self):
        return round(self.num_trade*1.0 / self.num_search,2)

    @property
    def trade_click_ratio(self):
        return round(self.num_trade*1.0 / self.num_click,2)

    @property
    def ads_price(self):
        return self.ads_price_cent * 0.01

    class Meta:
        db_table = 'subway_hotkey'



class KeyScore(models.Model):
    hotkey = models.ForeignKey(Hotkey)

    bid_price = models.CharField(max_length=10,blank=True)
    num_iid = models.CharField(max_length=64,db_index=True)
    num_view  = models.IntegerField(null=True)
    num_click = models.IntegerField(null=True)
    avg_cost = models.IntegerField(null=True)
    score = models.IntegerField(null=True)
    updated = models.DateTimeField(auto_now=True)

    bid_rank = models.CharField(max_length=10,blank=True)
    modify = models.IntegerField(default=0)
    status = models.IntegerField(default=0)

    class Meta:
        db_table = 'subway_keyscore'


class ZtcItem(models.Model):
    owner = models.CharField(max_length=64,db_index=True)
    num_iid = models.CharField(max_length=64,db_index=True)
    cat_id = models.CharField(max_length=64,db_index=True)
    cat_name = models.CharField(max_length=128)

    class Meta:
        db_table = 'subway_ztcitem'
    

class LzKeyItem(models.Model):
    owner       = models.CharField(max_length=64,db_index=True)
    effect_rank = models.IntegerField(null=True)
    inner_ipv   = models.IntegerField(null=True)
    coll_num    = models.IntegerField(null=True)
    adgroup_id  = models.IntegerField(null=True)
    efficiency  = models.CharField(max_length=8,blank=True,default='')
    originalword   = models.CharField(max_length=16,blank=True,db_index=True,default='')
    shop_coll_num  = models.IntegerField(null=True)
    is_shop     = models.IntegerField(null=True)
    roc         = models.IntegerField(null=True)
    alipay_indirect_amt  = models.IntegerField(null=True)
    unit_id     = models.IntegerField(null=True)
    bidword_id  = models.BigIntegerField(null=True)
    finclick    = models.IntegerField(null=True)
    campaign_id = models.IntegerField(null=True)
    alipay_amt  = models.IntegerField(null=True)
    alipay_direct_amt    =models.IntegerField(null=True)
    alipay_num  = models.IntegerField(null=True)
    imgurl      = models.CharField(max_length=64,blank=True,default='')
    item_coll_num  = models.IntegerField(null=True)
    finprice    = models.IntegerField(null=True)
    auction_id  = models.BigIntegerField(null=True,db_index=True)
    avg_finprice  = models.IntegerField(null=True)

    update = models.CharField(max_length=10,db_index=True)

    class Meta:
        db_table = 'subway_lzkeyitem'


