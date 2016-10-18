# coding=utf-8
"""
代理广告处理
"""
import datetime
from django.db import models
from core.models import BaseModel

from core.fields import JSONCharMyField
from django.db.models.signals import post_save


class XlmmAdvertis(models.Model):
    INNER_LEVEL = 1
    VIP_LEVEL = 2
    A_LEVEL = 3
    VIP2_LEVEL = 12
    VIP4_LEVEL = 14
    VIP6_LEVEL = 16
    VIP8_LEVEL = 18

    PEOPLE_CHOICE = ((INNER_LEVEL, u'内部级别'), (VIP_LEVEL, u'VIP代理'), (A_LEVEL, u'A类代理'))

    title = models.CharField(max_length=64, db_index=True, verbose_name=u'广告标题')
    cntnt = models.TextField(max_length=512, verbose_name=u'广告内容')
    show_people = models.IntegerField(choices=PEOPLE_CHOICE, verbose_name=u"展示对象")
    start_time = models.DateTimeField(blank=True, null=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')
    is_valid = models.BooleanField(default=False, verbose_name=u"是否投放")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成时间')
    modify = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = 'flashsale_xlmm_advertis'
        app_label = 'xiaolumm'
        verbose_name = u'代理广告表'
        verbose_name_plural = u'代理广告表列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)


class TweetAdvertorial(models.Model):
    title = models.CharField(max_length=128, db_index=True, verbose_name=u'推文标题')
    content = models.TextField(max_length=6400, verbose_name=u'推文文字内容')
    pic_arry = JSONCharMyField(max_length=6400, default={}, null=True, blank=True, verbose_name=u'推文图片')
    release_date = models.DateField(blank=True, null=True, verbose_name=u"投放日期")

    class Meta:
        db_table = 'flashsale_xlmm_tweet'
        app_label = 'xiaolumm'
        verbose_name = u'分享推文表'
        verbose_name_plural = u'分享推文列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)


class NinePicAdver(models.Model):
    """ 9张图 """
    Nine_PIC = 9
    EIGHT_PIC = 8
    SEVEN_PIC = 7
    SIX_PIC = 6
    FIVE_PIC = 5
    FOUR_PIC = 4
    THIRE_PIC = 3
    TWO_PIC = 2
    ONE_PIC = 1

    CATEGORY_CHOICE = (
        (Nine_PIC, u"9张图类型"), (EIGHT_PIC, u"8张图类型"), (SEVEN_PIC, u"7张图类型"), (SIX_PIC, u"6张图类型"),
        (FIVE_PIC, u"5张图类型"),
        (FOUR_PIC, u"4张图类型"), (THIRE_PIC, u"3张图类型"), (TWO_PIC, u"2张图类型"), (ONE_PIC, u"1张图类型"))

    auther = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'作者')
    title = models.CharField(max_length=512, db_index=True, verbose_name=u'标题')
    description = models.TextField(max_length=1024, blank=True, null=True, verbose_name=u'文案描述')
    cate_gory = models.IntegerField(choices=CATEGORY_CHOICE, default=Nine_PIC, verbose_name=u"类型")
    sale_category = models.ForeignKey('supplier.SaleCategory', null=True, verbose_name=u'类别')
    pic_arry = JSONCharMyField(max_length=2048, default=[], blank=True, null=True, verbose_name=u'图片链接')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name=u'开始时间')
    turns_num = models.IntegerField(verbose_name=u'轮数(第几轮)')
    is_pushed = models.BooleanField(default=False, verbose_name=u'是否已经推送')
    detail_modelids = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'详情页款式id')
    save_times = models.IntegerField(default=0, verbose_name=u'保存次数')
    share_times = models.IntegerField(default=0, verbose_name=u'分享次数')

    class Meta:
        db_table = 'flashsale_xlmm_nine_pic'
        app_label = 'xiaolumm'
        verbose_name = u'图片推广表'
        verbose_name_plural = u'图片推广列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)

    def is_share(self):
        """ 是否可以分享 """
        now = datetime.datetime.now()  # 现在时间
        end_clock = datetime.datetime(now.year, now.month, now.day, 14, 0, 0, 0)  # 下架时间
        yestoday = datetime.date.today() - datetime.timedelta(days=1)  # 昨天
        if self.start_time.date() == yestoday and now > end_clock:  # 开始时间是昨天　并且是现在是下架以后则不能分享
            return 0
        return 1  # 否则可以分享

    def title_display(self):
        today = datetime.date.today()
        month = today.month
        day = today.day
        share_time = self.start_time.strftime("%H:%M")
        return "%02d月%02d日｜第%d轮 分享时间：%s" (month, day, self.turns_num, share_time)
    
    def description_title(self):
        return self.description.replace('\r\n', '\r')


from flashsale.xiaolumm import util_emoji


def gen_emoji(sender, instance, created, **kwargs):
    desc = util_emoji.gen_emoji(instance.description)
    NinePicAdver.objects.filter(id=instance.id).update(description=desc)


post_save.connect(gen_emoji,
                  sender=NinePicAdver, dispatch_uid='post_save_ninpicadver_gen_emoji')


class MamaVebViewConf(BaseModel):
    version = models.CharField(max_length=32, db_index=True, verbose_name=u'版本号')
    is_valid = models.BooleanField(db_index=True, default=False, verbose_name=u'是否有效')
    extra = JSONCharMyField(max_length=2048, default={}, blank=True, null=True, verbose_name=u'配置内容')

    class Meta:
        db_table = 'flashsale_xlmm_webview_config'
        app_label = 'xiaolumm'
        verbose_name = u'客户端妈妈页面配置表'
        verbose_name_plural = u'客户端妈妈页面配置列表'
