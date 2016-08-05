# coding=utf-8
import datetime
from core.models import BaseModel
from django.db import models
from flashsale.xiaolumm.models import XiaoluMama, CarryRecord


class XlmmDailyStat(BaseModel):
    total = models.IntegerField(default=0, verbose_name=u'妈妈总数')
    new_join = models.IntegerField(default=0, verbose_name=u'新加入妈妈总数')
    new_pay = models.IntegerField(default=0, verbose_name=u'新付款妈妈总数')
    new_activite = models.IntegerField(default=0, verbose_name=u'新激活妈妈总数')
    new_hasale = models.IntegerField(default=0, verbose_name=u'新出货妈妈总数')

    new_trial = models.IntegerField(default=0, verbose_name=u'新加入一元妈妈总数')
    new_trial_activite = models.IntegerField(default=0, verbose_name=u'新激活一元妈妈总数')
    new_trial_hasale = models.IntegerField(default=0, verbose_name=u'新出货一元妈妈总数')

    new_task = models.IntegerField(default=0, verbose_name=u'新做任务一总数')
    new_lesson = models.IntegerField(default=0, verbose_name=u'新上课总数')
    new_award = models.IntegerField(default=0, verbose_name=u'新奖励总数')
    date_field = models.DateField(unique=True, verbose_name=u'日期')

    class Meta:
        db_table = 'statistics_xlmm_daily_stat'
        app_label = 'statistics'
        verbose_name = u'小鹿妈妈日统计表'
        verbose_name_plural = u'小鹿妈妈日统计表'

    @staticmethod
    def create(daytime):
        """
            celery每天执行一次
        """
        daytime = datetime.datetime(daytime.year, daytime.month, daytime.day)
        daytime -= datetime.timedelta(days=1)
        daytime = daytime.date()
        x = XlmmDailyStat(
            total=XlmmDailyStat.get_total(),
            date_field=daytime
        )

        x.new_join = x.get_new_join()
        x.new_pay = x.get_new_pay()
        x.new_activite = x.get_new_activite()
        x.new_hasale = 0

        x.new_trial = x.get_new_trial()
        x.new_trial_activite = x.get_new_trial_activite()
        x.new_trial_hasale = x.get_new_trial_hasale()

        x.new_task = 0
        x.new_lesson = 0
        x.new_award = x.get_new_award()
        x.save()
        return x

    @staticmethod
    def get_total():
        return XiaoluMama.objects.filter(status='effect').count()

    def get_new_join(self):
        return XiaoluMama.objects.filter(status='effect', created__range=(
            self.date_field, self.date_field + datetime.timedelta(days=1))).count()

    def get_new_pay(self):
        from flashsale.pay.models import SaleTrade, SaleOrder
        return SaleTrade.objects.filter(order_type=2, pay_time__range=(
            self.date_field, self.date_field + datetime.timedelta(days=1))).count()

    def get_new_activite(self):
        return XiaoluMama.objects.filter(active_time__range=(
            self.date_field, self.date_field + datetime.timedelta(days=1))).count()

    def get_new_award(self):
        return CarryRecord.objects.filter(carry_type=3, created__range=(
            self.date_field, self.date_field + datetime.timedelta(days=1))).count()

    def get_new_trial(self):
        return XiaoluMama.objects.filter(last_renew_type=XiaoluMama.TRIAL, created__range=(
            self.date_field, self.date_field + datetime.timedelta(days=1))).count()

    def get_new_trial_activite(self):
        return XiaoluMama.objects.filter(last_renew_type=XiaoluMama.TRIAL, active_time__range=(
            self.date_field, self.date_field + datetime.timedelta(days=1))).count()

    def get_new_trial_hasale(self):
        return XiaoluMama.objects.filter(last_renew_type=XiaoluMama.TRIAL, hasale_time__range=(
            self.date_field, self.date_field + datetime.timedelta(days=1))).count()
