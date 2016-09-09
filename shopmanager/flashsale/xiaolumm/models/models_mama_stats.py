# coding=utf-8
from core.models import BaseModel
from flashsale.xiaolumm.models import MamaDailyAppVisit
from flashsale.xiaolumm.models import XiaoluMama

from django.db import models
from django.db.models import Sum

from django.db.models.signals import post_save
import datetime


class MamaTabVisitStats(BaseModel):
    TAB_UNKNOWN = 0       #unknown
    TAB_MAMA_FORTUNE = 1  #妈妈主页
    TAB_DAILY_NINEPIC = 2 #每日推送
    TAB_NOTIFICATION = 3  #消息通知
    TAB_MAMA_SHOP = 4     #店铺精选
    TAB_INVITE_MAMA = 5   #邀请妈妈
    TAB_CARRY_LIST = 6    #选品佣金
    TAB_VIP_EXAM = 7      #VIP考试
    TAB_MAMA_TEAM = 8     #妈妈团队
    TAB_INCOME_RANK = 9   #收益排名
    TAB_ORDER_CARRY = 10  #订单记录
    TAB_CARRY_RECORD = 11 #收益记录
    TAB_FANS_LIST = 12    #粉丝列表
    TAB_VISITOR_LIST = 13 #访客列表
    TAB_WX_MAMA_ACTIVATE = 14 #公众号我的店铺
    
    STATS_TABS = ((TAB_UNKNOWN, 'Unknown'), (TAB_MAMA_FORTUNE, u'妈妈主页'), (TAB_DAILY_NINEPIC, u'每日推送'),
                  (TAB_NOTIFICATION, u'消息通知'), (TAB_MAMA_SHOP, u'店铺精选'), (TAB_INVITE_MAMA, u'邀请妈妈'),
                  (TAB_CARRY_LIST, u'选品佣金'), (TAB_VIP_EXAM, u'VIP考试'), (TAB_MAMA_TEAM, u'妈妈团队'),
                  (TAB_INCOME_RANK, u'收益排名'), (TAB_ORDER_CARRY, u'订单记录'), (TAB_CARRY_RECORD, u'收益记录'),
                  (TAB_FANS_LIST, u'粉丝列表'), (TAB_VISITOR_LIST, u'访客列表'), (TAB_WX_MAMA_ACTIVATE, u'店铺激活'))

    stats_tab = models.IntegerField(default=0, choices=STATS_TABS, db_index=True, verbose_name=u'功能TAB')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  # stats_tab+date
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    visit_total = models.IntegerField(default=0, verbose_name=u'访问次数')

    class Meta:
        db_table = 'flashsale_xlmm_mamatabvisitstats'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈tab访问统计'
        verbose_name_plural = u'V2/妈妈tab访问统计表'


class MamaDeviceStats(BaseModel):
    device_type = models.IntegerField(default=0, choices=MamaDailyAppVisit.DEVICE_TYPES, db_index=True, verbose_name=u'设备')
    renew_type = models.IntegerField(default=0, choices=XiaoluMama.RENEW_TYPE, db_index=True, verbose_name=u'妈妈类型')
    
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  # device_type+date
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    num_latest = models.IntegerField(default=0, verbose_name=u'最新版本数')
    num_outdated = models.IntegerField(default=0, verbose_name=u'旧版本数')
    num_visits = models.IntegerField(default=0, verbose_name=u'访问次数')

    class Meta:
        db_table = 'flashsale_xlmm_mamadevicestats'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈device统计'
        verbose_name_plural = u'V2/妈妈device统计表'

    @staticmethod
    def gen_uni_key(device_type, date_field, renew_type):
        return "%s-%s-%s" % (device_type, date_field, renew_type)
    
    @property
    def outdated_percentage(self):
        total = self.num_outdated + self.num_latest
        if total == 0:
            return "0.00%"
        percentage = self.num_outdated * 100.0 / total
        return "%.2f%%" % percentage

    @property
    def total_visitor(self):
        return self.num_latest + self.num_outdated

    @property
    def total_device_visitor(self):
        s = MamaDeviceStats.objects.filter(date_field=self.date_field,device_type=self.device_type).aggregate(a=Sum('num_latest'),b=Sum('num_outdated'))
        num_latest = s['a'] or 0
        num_outdated = s['b'] or 0
        return num_latest + num_outdated

class MamaDailyTabVisit(BaseModel):
    mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  # mama_id+stats_tab+date
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    stats_tab = models.IntegerField(default=0, choices=MamaTabVisitStats.STATS_TABS, db_index=True, verbose_name=u'功能TAB')

    class Meta:
        db_table = 'flashsale_xlmm_mamadailytabvisit'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈tab访问记录'
        verbose_name_plural = u'V2/妈妈tab访问记录列表'


def mama_daily_tab_visit_stats(sender, instance, created, **kwargs):
    if not created:
        return

    uni_key = "%s-%s" % (instance.stats_tab, instance.date_field)
    mt = MamaTabVisitStats.objects.filter(uni_key=uni_key).first()
    if not mt:
        mt = MamaTabVisitStats(stats_tab=instance.stats_tab, uni_key=uni_key, date_field=instance.date_field, visit_total=1)
        mt.save()
    else:
        mt.visit_total += 1
        mt.save(update_fields=['visit_total', 'modified'])

post_save.connect(mama_daily_tab_visit_stats,
                  sender=MamaDailyTabVisit, dispatch_uid='post_save_mama_daily_tab_visit_stats')
