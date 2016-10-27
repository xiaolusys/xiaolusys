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
    redirect_url = models.CharField(max_length=512, blank=True, null=True, verbose_name=u'跳转地址')
    save_times = models.IntegerField(default=0, verbose_name=u'保存次数')
    share_times = models.IntegerField(default=0, verbose_name=u'分享次数')
    memo = models.CharField(max_length=512, blank=True, verbose_name=u'备注')

    class Meta:
        db_table = 'flashsale_xlmm_nine_pic'
        app_label = 'xiaolumm'
        verbose_name = u'图片推广表'
        verbose_name_plural = u'图片推广列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)

    @classmethod
    def init_time(cls, assign_date=None):
        # type: (Optional[datetime.date]) -> datetime.datetime
        now = datetime.datetime.now() if assign_date is None else datetime.datetime(assign_date.year,
                                                                                    assign_date.month,
                                                                                    assign_date.day, 0, 0)
        return datetime.datetime(now.year, now.month, now.day, 0, 0, 0)

    @classmethod
    def calculate_create_assign_turns_num(cls, assign_datetime=None):
        # type: (Optional[datetime.datetime]) -> int
        init_time = cls.init_time(assign_datetime.date())
        end_time = datetime.datetime(init_time.year, init_time.month, init_time.day, 23, 59, 59)
        return cls.objects.filter(start_time__gte=init_time, start_time__lte=end_time).count()

    @classmethod
    def resort_turns_num(cls, date):
        # type: (datetime.date) -> None
        init_time = cls.init_time(date)
        end_time = datetime.datetime(init_time.year, init_time.month, init_time.day, 23, 59, 59)
        count = 1
        for ninepic in cls.objects.filter(start_time__gte=init_time, start_time__lte=end_time).order_by('start_time'):
            ninepic.turns_num = count
            ninepic.save(update_fields=['turns_num'])
            count += 1
        return

    @classmethod
    def create(cls, auther, title, start_time,
               pic_arry=None, description='', advertisement_type=9,
               category_id=None, is_pushed=False, redirect_url='',
               detail_modelids='', memo=''):
        # type: (text_type, text_type, datetime.datetime,
        # Optional[List[text_type]], text_type, int, Optional[int], bool, text_type) -> NinePicAdver
        turns_num = cls.calculate_create_assign_turns_num(start_time)  # 轮数
        verify_turns_num = cls.objects.filter(start_time__gte=cls.init_time(start_time.date()),
                                              start_time__lt=start_time).count()

        if turns_num != verify_turns_num:
            raise Exception(u'请设置 **开始时间** 在当前最后一轮以后!')
        n = cls(auther=auther,
                title=title,
                description=description,
                cate_gory=advertisement_type,
                sale_category=category_id,
                pic_arry=pic_arry,
                start_time=start_time,
                turns_num=turns_num + 1,
                is_pushed=is_pushed,
                detail_modelids=detail_modelids,
                memo=memo,
                redirect_url=redirect_url)
        n.save()
        return n

    def destroy(self):
        # type: () -> bool
        """删除记录
        1. 删除记录
        2. 重新排轮数
        """
        date = self.start_time.date()
        self.delete()
        NinePicAdver.resort_turns_num(date)
        return True

    def update(self, **kwargs):
        # type: (**Any) -> NinePivAdver
        """更新记录
        １. 如果有时间变化，则重新排轮数
        """
        if kwargs.has_key('turns_num'):  # 不更新传入的turns_num
            kwargs.pop('turns_num')
        if kwargs.has_key('sale_category'):
            kwargs.update({'sale_category_id': kwargs.pop('sale_category')})
        if not kwargs.has_key('start_time'):  # 没有重新设置时间则不去更新时间和　turns_num
            kwargs.update({'turns_num': self.turns_num})
        else:
            start_time = datetime.datetime.strptime(kwargs.get('start_time'), '%Y-%m-%d %H:%M:%S')
            old_start_time_date = self.start_time.date()
            if old_start_time_date != start_time.date():  # 不相等则都重新排序修改　轮数
                NinePicAdver.resort_turns_num(old_start_time_date)
            NinePicAdver.resort_turns_num(start_time.date())
        for k, v in kwargs.iteritems():
            if hasattr(self, k) and getattr(self, k) != v:
                setattr(self, k, v)
        self.save()
        return self

    def is_share(self):
        """ 是否可以分享 """
        now = datetime.datetime.now()  # 现在时间
        end_clock = datetime.datetime(now.year, now.month, now.day, 14, 0, 0, 0)  # 下架时间
        yestoday = datetime.date.today() - datetime.timedelta(days=1)  # 昨天
        if self.start_time.date() == yestoday and now > end_clock:  # 开始时间是昨天　并且是现在是下架以后则不能分享
            return 0
        return 1  # 否则可以分享

    def title_display(self):
        today = self.start_time
        month = today.month
        day = today.day
        share_time = self.start_time.strftime("%H:%M")
        return "%02d月%02d日｜第%d轮 分享时间：%s" % (month, day, self.turns_num, share_time)

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
