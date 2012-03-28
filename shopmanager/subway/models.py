from django.db import models
from django.db import connection

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
    updated = models.CharField(max_length=10,db_index=True)
    
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

    @classmethod
    def getRecommendNewKey(cls,base_dt,cat_id,limit):
        cursor = connection.cursor()
        cursor.execute("select sh.word, sh.num_people, sh.num_search,sh.num_click, sh.num_trade, sh.ads_price_cent,"+\
            "(ROUND(num_trade/num_search,4)) AS search_ratio,st.lift_val FROM subway_hotkey sh RIGHT JOIN "+\
            "subway_tckeylift st ON sh.word = st.word WHERE sh.updated=%s AND sh.category_id=%s "+\
            "AND st.updated=%s AND st.category_id=%s ORDER BY search_ratio DESC LIMIT %s"
                       ,(base_dt,cat_id,base_dt,cat_id,limit))

        return cursor.fetchall()


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
    effect_rank = models.CharField(max_length=8,blank=True,default='')
    inner_ipv   = models.IntegerField(null=True)
    coll_num    = models.IntegerField(null=True)
    adgroup_id  = models.IntegerField(null=True)
    efficiency  = models.CharField(max_length=8,blank=True,default='')
    originalword   = models.CharField(max_length=24,blank=True,db_index=True,default='')
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

    updated = models.CharField(max_length=10,db_index=True)

    class Meta:
        db_table = 'subway_lzkeyitem'

    @classmethod
    def getGroupAttrsByIdAndWord(cls,num_iid,key_str,lz_f_dt,lz_t_dt):

        cursor = connection.cursor()
        cursor.execute('select originalword ,SUM(coll_num) collnums,SUM(finclick) finclicks '+
            ',SUM(finprice) finprices,SUM(alipay_amt) alipay_amts,SUM(alipay_num) alipay_nums from subway_lzkeyitem '+
            'where auction_id=%s and originalword in (%s) and updated >=%s and updated <=%s group by originalword '
            , (num_iid,key_str,lz_f_dt,lz_t_dt))
        return cursor.fetchall()



class TcKeyLift(models.Model):
    word        = models.CharField(max_length=64,db_index=True)
    category_id = models.CharField(max_length=64,blank=True)
    lift_val    = models.CharField(max_length=8,blank=True)

    updated     = models.CharField(max_length=10,db_index=True)

    class Meta:
        db_table = 'subway_tckeylift'


