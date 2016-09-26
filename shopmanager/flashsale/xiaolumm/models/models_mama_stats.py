# coding=utf-8
from core.models import BaseModel
from flashsale.xiaolumm.models import MamaDailyAppVisit
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.pay.models import Customer

from core.fields import JSONCharMyField

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
    TAB_WX_APP_DOWNLOAD = 15
    TAB_WX_REFERAL_QRCODE = 16
    TAB_WX_MANAGER_QRCODE = 17
    TAB_WX_KEFU = 18
    TAB_WX_PERSONAL = 19
    TAB_WX_CASHOUT_APP_DOWNLOAD = 20
    
    STATS_TABS = ((TAB_UNKNOWN, 'Unknown'), (TAB_MAMA_FORTUNE, u'妈妈主页'), (TAB_DAILY_NINEPIC, u'每日推送'),
                  (TAB_NOTIFICATION, u'消息通知'), (TAB_MAMA_SHOP, u'店铺精选'), (TAB_INVITE_MAMA, u'邀请妈妈'),
                  (TAB_CARRY_LIST, u'选品佣金'), (TAB_VIP_EXAM, u'VIP考试'), (TAB_MAMA_TEAM, u'妈妈团队'),
                  (TAB_INCOME_RANK, u'收益排名'), (TAB_ORDER_CARRY, u'订单记录'), (TAB_CARRY_RECORD, u'收益记录'),
                  (TAB_FANS_LIST, u'粉丝列表'), (TAB_VISITOR_LIST, u'访客列表'), (TAB_WX_MAMA_ACTIVATE, u'WX/店铺激活'),
                  (TAB_WX_APP_DOWNLOAD, u'WX/APP下载'), (TAB_WX_REFERAL_QRCODE, u'WX/开店二维码'), (TAB_WX_MANAGER_QRCODE, u'WX/管理员二维码'),
                  (TAB_WX_KEFU, u'WX/客服菜单'), (TAB_WX_PERSONAL, u'WX/个人帐户'), (TAB_WX_CASHOUT_APP_DOWNLOAD, u'WX/提现页APP下载'))

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


class WeixinPushEvent(BaseModel):
    INVITE_LIMIT_WARN = 0
    INVITE_FANS_NOTIFY = 1
    INVITE_AWARD_INIT = 2
    INVITE_AWARD_FINAL = 3
    ORDER_CARRY_INIT = 4
    FANS_SUBSCRIBE_NOTIFY = 5
    SUB_ORDER_CARRY_INIT = 6
    
    EVENT_TYPES = ((INVITE_FANS_NOTIFY, u'粉丝增加'), (INVITE_AWARD_INIT, u'邀请奖励生成'), (INVITE_AWARD_FINAL, u'邀请奖励确定'),
                   (FANS_SUBSCRIBE_NOTIFY, u'关注公众号'), (ORDER_CARRY_INIT, u'订单佣金生成'), (SUB_ORDER_CARRY_INIT, u'下属订单佣金生成'))

    TEMPLATE_ORDER_CARRY_ID = 2
    TEMPLATE_INVITE_FANS_ID = 7
    TEMPLATE_SUBSCRIBE_ID = 8
    TEMPLATE_IDS = ((TEMPLATE_INVITE_FANS_ID, '模版/粉丝增加'),(TEMPLATE_SUBSCRIBE_ID, '模版/关注公众号'),(TEMPLATE_ORDER_CARRY_ID, '模版/订单佣金'))
    
    customer_id = models.IntegerField(default=0, db_index=True, verbose_name=u'接收者用户id')
    mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'接收者妈妈id')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    tid = models.IntegerField(default=0, choices=TEMPLATE_IDS, verbose_name=u'消息模版ID')
    event_type = models.IntegerField(default=0, choices=EVENT_TYPES, db_index=True, verbose_name=u'事件类型')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    params = JSONCharMyField(max_length=512, default={}, blank=True, null=True, verbose_name=u"参数信息")
    to_url = models.CharField(max_length=128, blank=True, verbose_name=u'跳转链接')
    
    class Meta:
        db_table = 'flashsale_xlmm_weixinpushevent'
        app_label = 'xiaolumm'
        verbose_name = u'V2/微信推送事件'
        verbose_name_plural = u'V2/微信推送事件列表'

        
    @staticmethod
    def gen_uni_key(customer_id, event_type, date_field):
        return '%s-%s|%s' % (customer_id, event_type, date_field)

    @classmethod
    def send_push(cls, customer_id, template_id, ):
        pass

    def get_effect_customer(self):
        c = Customer.objects.filter(id=self.customer_id, status=Customer.NORMAL).first()
        return c

    @staticmethod
    def gen_invite_fans_notify_unikey(event_type, customer_id, today_invites, date_field):
        return "%s-%s-%s|%s" % (event_type, customer_id, today_invites, date_field)

    @staticmethod
    def gen_subscribe_notify_unikey(event_type, customer_id):
        return "%s-%s" % (event_type, customer_id)

    @staticmethod
    def gen_ordercarry_unikey(event_type, sale_trade_id):
        return "%s-%s" % (event_type, sale_trade_id)
    
def send_weixin_push(sender, instance, created, **kwargs):
    if not created:
        return

    from shopapp.weixin.weixin_push import WeixinPush
    wxpush = WeixinPush()
    wxpush.push_event(instance)
        
post_save.connect(send_weixin_push, sender=WeixinPushEvent, dispatch_uid='post_save_weixinpushevent_send_weixin_push')

