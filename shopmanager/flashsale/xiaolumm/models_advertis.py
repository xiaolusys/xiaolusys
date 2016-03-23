# coding=utf-8
"""
代理广告处理
"""
from django.db import models
from shopback.base.models import JSONCharMyField
from django.db.models.signals import post_save
import datetime


class XlmmAdvertis(models.Model):
    INNER_LEVEL = 1
    VIP_LEVEL = 2
    A_LEVEL = 3

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
        verbose_name = u'代理广告表'
        verbose_name_plural = u'代理广告表列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)


class TweetAdvertorial(models.Model):
    title = models.CharField(max_length=128, db_index=True, verbose_name=u'推文标题')
    content = models.TextField(max_length=6400, verbose_name=u'推文文字内容')
    pic_arry = JSONCharMyField(max_length=6400, null=True, blank=True, verbose_name=u'推文图片')
    release_date = models.DateField(blank=True, null=True, verbose_name=u"投放日期")

    class Meta:
        db_table = 'flashsale_xlmm_tweet'
        verbose_name = u'分享推文表'
        verbose_name_plural = u'分享推文列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)


class NinePicAdver(models.Model):
    """ 9张图 """
    Nine_PIC = 9
    CATEGORY_CHOICE = ((Nine_PIC, u"九张图类型"),)
    auther = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'作者')
    title = models.CharField(max_length=512, db_index=True, verbose_name=u'标题')
    description = models.TextField(max_length=1024, blank=True, null=True, verbose_name=u'文案描述')
    cate_gory = models.IntegerField(choices=CATEGORY_CHOICE, default=Nine_PIC, verbose_name=u"类型")
    pic_arry = JSONCharMyField(max_length=2048, blank=True, null=True, verbose_name=u'图片链接')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name=u'开始时间')
    turns_num = models.IntegerField(verbose_name=u'轮数(第几轮)')

    class Meta:
        db_table = 'flashsale_xlmm_nine_pic'
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

    def description_title(self):
        return self.description.replace('\r\n', '\r')



from flashsale.xiaolumm import util_emoji

def gen_emoji(sender, instance, created, **kwargs):
    desc = util_emoji.gen_emoji(instance.description)
    NinePicAdver.objects.filter(id=instance.id).update(description=desc)
        

post_save.connect(gen_emoji,
                  sender=NinePicAdver, dispatch_uid='post_save_ninpicadver_gen_emoji')
