# coding=utf-8
from django.db import models
from core.models import BaseModel
from django.db.models.signals import post_save
from statistics import constants


def stat_status_choices():  # 订单状态选择
    return constants.STATUS


def return_goods_choices():  # 是否退货选择
    return constants.RETURN_CHOICES


def record_type_choices():  # 统计记录类型选择
    return constants.RECORD_TYPES


def timely_type_choices():  # 统计时间 维度类型
    return constants.TIMELY_TYPES


class SaleOrderStatsRecord(BaseModel):
    oid = models.CharField(max_length=40, unique=True, verbose_name=u'sale_order_oid')
    outer_id = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'外部编码')
    sku_id = models.CharField(max_length=32, blank=True, verbose_name=u'规格外部编码')  # 实际保存的是 outer_id + '/'+outer_sku_id
    name = models.CharField(max_length=64, verbose_name=u'商品SKU描述')  # title + sku_name
    pic_path = models.CharField(max_length=256, verbose_name=u'图片')
    num = models.IntegerField(default=0, verbose_name=u'数量')
    payment = models.FloatField(default=0, verbose_name=u'实付款')
    pay_time = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name=u'付款时间')
    date_field = models.DateField(db_index=True, null=True, blank=True, verbose_name=u'日期')
    status = models.IntegerField(choices=stat_status_choices(), db_index=True, verbose_name=u'状态')
    return_goods = models.IntegerField(default=constants.NO_RETURN, choices=return_goods_choices(),
                                       verbose_name=u'退货标记')

    class Meta:
        db_table = 'statistics_sale_order_stats_record'
        app_label = 'statistics'
        verbose_name = '交易统计明细'
        verbose_name_plural = '交易统计明细列表'


def update_salestats(sender, instance, created, **kwargs):
    from statistics.tasks import task_statsrecord_update_salestats

    task_statsrecord_update_salestats.delay(instance)


post_save.connect(update_salestats, sender=SaleOrderStatsRecord, dispatch_uid='post_save_update_salestats')


class SaleStats(BaseModel):
    parent_id = models.CharField(max_length=32, db_index=True, blank=True, null=True, verbose_name=u'上一级id')
    current_id = models.CharField(max_length=32, db_index=True, blank=True, null=True, verbose_name=u'级别对应instance_id')
    date_field = models.DateField(db_index=True, verbose_name=u'付款日期')
    name = models.CharField(max_length=64, null=True, verbose_name=u'商品描述')  # title + sku_name
    pic_path = models.CharField(max_length=256, null=True, verbose_name=u'图片')
    num = models.IntegerField(default=0, verbose_name=u'销售数量')
    payment = models.FloatField(default=0, verbose_name=u'销售金额')
    uni_key = models.CharField(max_length=64, unique=True, verbose_name=u'唯一标识')
    timely_type = models.IntegerField(default=constants.TIMELY_TYPE_DATE_DETAIL,
                                      choices=timely_type_choices(), db_index=True, verbose_name=u'时间维度类型')
    record_type = models.IntegerField(choices=record_type_choices(), db_index=True, verbose_name=u'记录类型')
    status = models.IntegerField(choices=stat_status_choices(), db_index=True, verbose_name=u'状态')

    # uni_key = date_field + current_id + record_type + status
    def __unicode__(self):
        return u'<%s-%s>' % (self.id, self.uni_key)

    class Meta:
        db_table = 'statistics_sale_stats'
        app_label = 'statistics'
        verbose_name = u'销量统计表'
        verbose_name_plural = u'销量统计列表'


def update_parent_sale_stats(sender, instance, created, **kwargs):
    from statistics.tasks import task_update_parent_sale_stats, \
        task_update_agg_stats_record, task_update_daily_agg_sale_stats, task_update_detail_agg_sale_stats

    if instance.record_type <= constants.TYPE_BD and instance.timely_type < constants.TIMELY_TYPE_YEAR_DETAIL:
        # 小于买手级别的 日报细分 都要更新 周\月\季度\年度细分
        print "细分 %s" % instance.get_timely_type_display()
        task_update_detail_agg_sale_stats.delay(instance)

    if instance.timely_type == constants.TIMELY_TYPE_DATE_DETAIL:  # 日报细分类型 才更新 父级别 和 日报告
        task_update_parent_sale_stats.delay(instance)  # 更新 父级别
        if instance.record_type == constants.TYPE_BD:  # 更新 BD 的时候才去更新每天的聚合
            task_update_daily_agg_sale_stats.delay(instance)
            # 更新  记录类型 -> 周细分->月细分->季度细分->年度细分
    else:
        if instance.record_type == constants.TYPE_AGG:
            # 日期聚合-> 周聚合->月聚合->季度聚合->年度聚合
            task_update_agg_stats_record.delay(instance)
            return


post_save.connect(update_parent_sale_stats, sender=SaleStats, dispatch_uid='post_save_update_parent_sale_stats')


class ProductStockStat(BaseModel):
    parent_id = models.CharField(max_length=32, db_index=True, blank=True, null=True, verbose_name=u'上一级id')
    current_id = models.CharField(max_length=32, db_index=True, blank=True, null=True, verbose_name=u'级别对应instance_id')
    date_field = models.DateField(db_index=True, verbose_name=u'日期')
    name = models.CharField(max_length=64, null=True, verbose_name=u'描述')
    pic_path = models.CharField(max_length=256, null=True, verbose_name=u'图片')
    quantity = models.IntegerField(default=0, verbose_name=u'库存数量')
    sku_inferior_num = models.IntegerField(default=0, verbose_name=U'次品数量')
    amount = models.FloatField(default=0, verbose_name=u'库存金额')
    uni_key = models.CharField(max_length=64, unique=True, verbose_name=u'唯一标识')
    record_type = models.IntegerField(choices=record_type_choices(), db_index=True, verbose_name=u'记录类型')

    # uni_key = date_field + current_id + record_type
    class Meta:
        db_table = 'statistics_product_stock_stat'
        app_label = 'statistics'
        verbose_name = u'库存统计表'
        verbose_name_plural = u'库存统计列表'

    def __unicode__(self):
        return u'<%s-%s>' % (self.id, self.uni_key)
