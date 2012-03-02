from django.db import models


class Hotkey(models.Model):
    word = models.CharField(max_length=64,db_index=True)
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
    num_iid = models.CharField(max_length=64,db_index=True)
    score = models.IntegerField()
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subway_keyscore'
