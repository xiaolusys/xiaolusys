# -*- coding:utf-8 -*-
from django.db import models
from django.db.models.signals import post_save


# class ClickPrice(models.Model):
#     
#     order_num  = models.IntegerField(default=0,verbose_name=u'订单数量')
#     start_time = models.DateTimeField(verbose_name=u'开始时间')
#     end_time   = models.DateTimeField(verbose_name=u'结束时间')
#     click_price = models.IntegerField(default=0,verbose_name=u'点击价格')
# 
#     class Meta:
#         db_table = 'xiaolumm_click_price'
#         verbose_name=u'点击价格'
#         verbose_name_plural = u'点击价格列表'
# 
#     def __unicode__(self):
#         return '%s'%self.id


class Clicks(models.Model):
    CLICK_DAY_LIMIT = 1  # MM_CLICK_DAY_LIMIT

    linkid = models.IntegerField(default=0, db_index=True, verbose_name=u"链接ID")
    openid = models.CharField(max_length=28, blank=True, db_index=True, verbose_name=u"OpenId")
    app_key = models.CharField(max_length=20, blank=True, verbose_name=u"APP KEY")
    isvalid = models.BooleanField(default=False, verbose_name='是否有效')
    click_time = models.DateTimeField(db_index=True, verbose_name=u'点击时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'xiaolumm_clicks'
        app_label = 'clickcount'
        verbose_name = u'用户点击记录'
        verbose_name_plural = u'用户点击记录列表'

    def __unicode__(self):
        return '%s' % self.id


def update_unique_visitor(sender, instance, created, **kwargs):
    if created and instance.isvalid:
        from flashsale.xiaolumm.tasks import task_update_unique_visitor
        mama_id = instance.linkid
        openid = instance.openid
        app_key = instance.app_key
        click_time = instance.click_time
        task_update_unique_visitor.delay(mama_id, openid, app_key, click_time)


post_save.connect(update_unique_visitor,
                  sender=Clicks, dispatch_uid='post_save_update_unique_visitor')


class UserClicks(models.Model):
    unionid = models.CharField(max_length=64, unique=True, verbose_name=u"UnionID")
    visit_days = models.IntegerField(db_index=True, default=0, verbose_name=u'活跃天数')
    click_start_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'首次点击时间')
    click_end_time = models.DateTimeField(db_index=True, null=True, verbose_name=u'最后点击时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')

    class Meta:
        db_table = 'flashsale_userclicks'
        app_label = 'clickcount'
        verbose_name = u'用户活跃记录'
        verbose_name_plural = u'用户活跃记录列表'

    def __unicode__(self):
        return '%s' % self.id


# from django.db.models.signals import post_save
# def Create_Or_Change_Clickcount(sender, instance, created, **kwargs):
#     from flashsale.clickcount.tasks import task_Count_ClickCount_Info
#     task_Count_ClickCount_Info.s(instance, created)()
# 
# post_save.connect(Create_Or_Change_Clickcount, sender=Clicks)


class ClickCount(models.Model):
    linkid = models.IntegerField(db_index=True, verbose_name=u'链接ID')
    weikefu = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'微客服')
    agencylevel = models.IntegerField(default=1, verbose_name=u"类别")
    mobile = models.CharField(max_length=11, verbose_name=u"手机")

    user_num = models.IntegerField(default=0, verbose_name=u'人数')
    valid_num = models.IntegerField(default=0, verbose_name=u'有效点击人数')
    click_num = models.IntegerField(default=0, verbose_name=u'次数')
    date = models.DateField(db_index=True, verbose_name=u'日期')
    write_time = models.DateTimeField(auto_now_add=True, verbose_name=u'写入时间')
    username = models.IntegerField(default=0, db_index=True, verbose_name=u'接管人')

    class Meta:
        db_table = 'flashsale_clickcount'
        unique_together = ('linkid', 'date')  # 联合索引
        app_label = 'clickcount'
        verbose_name = u'点击统计表'
        verbose_name_plural = u'点击统计表列表'
        ordering = ['-date']
        permissions = [('browser_xlmm_active', u'浏览代理活跃度')]

    def __unicode__(self):
        return self.weikefu


class WeekCount(models.Model):
    linkid = models.IntegerField(db_index=True, verbose_name=u'链接ID')
    weikefu = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'微客服')
    user_num = models.IntegerField(default=0, verbose_name=u'点击人数')
    valid_num = models.IntegerField(default=0, verbose_name=u'有效点击数')
    buyercount = models.IntegerField(default=0, verbose_name=u'购买人数')
    ordernumcount = models.IntegerField(default=0, verbose_name=u'订单总数')
    conversion_rate = models.FloatField(default=0, verbose_name=u'转化率')
    week_code = models.CharField(max_length=6, verbose_name=u'周编码')
    write_time = models.DateTimeField(auto_now_add=True, verbose_name=u'写入时间')

    class Meta:
        db_table = "flashsale_weekcount_table"
        unique_together = ('linkid', 'week_code')  # 联合索引
        app_label = 'clickcount'
        verbose_name = u"代理转化率周统计"
        verbose_name_plural = u"代理转化率周统计列表"
        ordering = ['write_time']

    def __unicode__(self):
        return self.weikefu
