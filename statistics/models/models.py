# coding=utf-8
import logging
import datetime
from django.db import models
from django.db.models import Sum
from core.models import BaseModel
from django.db.models.signals import post_save
from statistics import constants
from shopback import paramconfig as pcfg

logger = logging.getLogger(__name__)


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
    sale_product = models.BigIntegerField(default=0, db_index=True, verbose_name=u'选品id')

    class Meta:
        db_table = 'statistics_sale_order_stats_record'
        app_label = 'statistics'
        verbose_name = '交易统计明细'
        verbose_name_plural = '交易统计明细列表'


def update_salestats(sender, instance, created, **kwargs):
    from statistics.tasks import task_statsrecord_update_salestats

    task_statsrecord_update_salestats.delay(instance)


post_save.connect(update_salestats, sender=SaleOrderStatsRecord, dispatch_uid='post_save_update_salestats')


def update_model_salestats(sender, instance, created, **kwargs):
    from statistics.tasks import task_statsrecord_update_model_stats

    task_statsrecord_update_model_stats.delay(instance)


post_save.connect(update_model_salestats, sender=SaleOrderStatsRecord, dispatch_uid='post_save_update_model_salestats')


class ModelStats(BaseModel):
    """
    某个款式　在某个上下架时间　的　各个状态的　数量
    """
    model_id = models.BigIntegerField(db_index=True, verbose_name=u'款式id')
    sale_product = models.BigIntegerField(db_index=True, verbose_name=u'选品id')
    schedule_manage_id = models.IntegerField(db_index=True, default=0, verbose_name=u'排期管理id')
    upshelf_time = models.DateTimeField(db_index=True, verbose_name=u'上架时间')
    offshelf_time = models.DateTimeField(db_index=True, verbose_name=u'下架时间')
    category = models.CharField(max_length=64, db_index=True, verbose_name=u'产品类别')
    supplier = models.IntegerField(db_index=True, verbose_name=u'供应商')

    model_name = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'标题')
    category_name = models.CharField(max_length=64, db_index=True, verbose_name=u'产品类别名称')
    pic_url = models.CharField(max_length=512, blank=True, verbose_name=u'商品图片')
    supplier_name = models.CharField(max_length=128, blank=True, db_index=True, verbose_name=u'供应商名称')

    pay_num = models.IntegerField(default=0, verbose_name=u'付款数量')
    no_pay_num = models.IntegerField(default=0, verbose_name=u'未付款数量')
    cancel_num = models.IntegerField(default=0, verbose_name=u'发货前退款数量')
    out_stock_num = models.IntegerField(default=0, verbose_name=u'缺货退款数量')
    return_good_num = models.IntegerField(default=0, verbose_name=u'退货退款数量')

    payment = models.FloatField(default=0, verbose_name=u'销售额')
    agent_price = models.FloatField(default=0, verbose_name=u'出售价(件)')
    cost = models.FloatField(default=0, verbose_name=u'成本价')
    uni_key = models.CharField(max_length=64, unique=True, db_index=True, blank=True, verbose_name=u'uni_key')

    class Meta:
        db_table = 'statistics_model_stats'
        app_label = 'statistics'
        verbose_name = u'款式统计表'
        verbose_name_plural = u'款式统计列表'


class SaleStats(BaseModel):
    parent_id = models.CharField(max_length=32, db_index=True, blank=True, null=True, verbose_name=u'上一级id')
    current_id = models.CharField(max_length=32, db_index=True, blank=True, null=True, verbose_name=u'级别对应instance_id')
    date_field = models.DateField(db_index=True, verbose_name=u'付款日期')
    name = models.CharField(max_length=64, null=True, verbose_name=u'商品描述')  # title + sku_name
    pic_path = models.CharField(max_length=256, null=True, verbose_name=u'图片')
    num = models.IntegerField(default=0, verbose_name=u'销售数量')
    payment = models.FloatField(default=0, verbose_name=u'销售金额')
    uni_key = models.CharField(max_length=64, unique=True, verbose_name=u'唯一标识')
    timely_type = models.IntegerField(default=constants.TIMELY_TYPE_DATE,
                                      choices=timely_type_choices(), db_index=True, verbose_name=u'时间维度类型')
    record_type = models.IntegerField(choices=record_type_choices(), db_index=True, verbose_name=u'记录类型')
    status = models.IntegerField(choices=stat_status_choices(), db_index=True, verbose_name=u'状态')

    # uni_key = date_field + current_id + record_type + status
    def __unicode__(self):
        return u'<%s-%s>' % (self.id, self.uni_key)

    def get_status_queryset(self):
        return self.__class__.objects.filter(parent_id=self.parent_id, current_id=self.current_id,
                                             date_field=self.date_field, record_type=self.record_type,
                                             timely_type=self.timely_type)

    @property
    def no_pay_num(self):
        if self.status == constants.NOT_PAY:
            return self.num
        no_pay_stats = self.get_status_queryset().filter(status=constants.NOT_PAY).first()
        return no_pay_stats.num if no_pay_stats else 0

    @property
    def paid_num(self):
        if self.status == constants.PAID:
            return self.num
        paid_stats = self.get_status_queryset().filter(status=constants.PAID).first()
        return paid_stats.num if paid_stats else 0

    @property
    def cancel_num(self):
        if self.status == constants.CANCEL:
            return self.num
        cancel_stats = self.get_status_queryset().filter(status=constants.CANCEL).first()
        return cancel_stats.num if cancel_stats else 0

    @property
    def out_stock_num(self):
        if self.status == constants.OUT_STOCK:
            return self.num
        out_stock_stats = self.get_status_queryset().filter(status=constants.OUT_STOCK).first()
        return out_stock_stats.num if out_stock_stats else 0

    @property
    def return_goods_num(self):
        if self.status == constants.RETURN_GOODS:
            return self.num
        return_goods_stats = self.get_status_queryset().filter(status=constants.RETURN_GOODS).first()
        return return_goods_stats.num if return_goods_stats else 0

    @property
    def supplier(self):
        if self.record_type != constants.TYPE_SUPPLIER:  # 供应商类型记录
            return None
        if not hasattr(self, '_supplier_'):
            from supplychain.supplier.models import SaleSupplier

            self._supplier_ = SaleSupplier.objects.filter(id=self.current_id).first()
        return self._supplier_

    @property
    def is_obsolete_supplier(self):
        """　判断淘汰的供应商 """
        if self.record_type != constants.TYPE_SUPPLIER:  # 供应商类型记录
            return False
        return True if self.supplier and self.supplier.progress == 'rejected' else False

    class Meta:
        db_table = 'statistics_sale_stats'
        app_label = 'statistics'
        verbose_name = u'销量统计表'
        verbose_name_plural = u'销量统计列表'


def update_parent_sale_stats(sender, instance, created, **kwargs):
    from statistics.tasks import task_update_parent_sale_stats, task_update_agg_sale_stats, gen_date_ftt_info, find_upper_timely_type

    if instance.record_type <= constants.TYPE_AGG:  #
        # 小于买手级别的  都要更新 周\月\季度\年度细分
        if instance.timely_type == constants.TIMELY_TYPE_DATE:  # 每天的总计更新 触发 周 和 月的更新
            time_from_1, time_to_1, tag_1 = gen_date_ftt_info(instance.date_field, constants.TIMELY_TYPE_WEEK)
            task_update_agg_sale_stats.delay(instance, time_from_1, time_to_1, constants.TIMELY_TYPE_WEEK, tag_1)
            time_from_2, time_to_2, tag_2 = gen_date_ftt_info(instance.date_field, constants.TIMELY_TYPE_MONTH)
            task_update_agg_sale_stats.delay(instance, time_from_2, time_to_2, constants.TIMELY_TYPE_MONTH, tag_2)

        elif instance.timely_type >= constants.TIMELY_TYPE_MONTH:  # 月更新触发 上级的所有更新
            upper_timely_type = find_upper_timely_type(instance.timely_type)  # 上级的时间维度 例如 周记录 更新的上一个时间维度 是 月份
            time_from, time_to, tag = gen_date_ftt_info(instance.date_field, upper_timely_type)
            task_update_agg_sale_stats.delay(instance, time_from, time_to, upper_timely_type, tag)

    if instance.timely_type == constants.TIMELY_TYPE_DATE:  # 日报细分类型 才更新 父级别 和 日报告
        task_update_parent_sale_stats.delay(instance)  # 更新 父级别


post_save.connect(update_parent_sale_stats, sender=SaleStats, dispatch_uid='post_save_update_parent_sale_stats')


def update_supplier_figure(sender, instance, created, **kwargs):
    # 日报　供应商类型　
    if instance.record_type != constants.TYPE_SUPPLIER:
        return
    if instance.timely_type != constants.TIMELY_TYPE_DATE:
        return
    from supplychain.supplier.tasks import task_calculate_supplier_stats_data

    task_calculate_supplier_stats_data.delay(instance)


post_save.connect(update_supplier_figure, sender=SaleStats, dispatch_uid='post_save_update_supplier_figure')


class ProductStockStat(BaseModel):
    parent_id = models.CharField(max_length=32, db_index=True, blank=True, null=True, verbose_name=u'上一级id')
    current_id = models.CharField(max_length=32, db_index=True, blank=True, null=True, verbose_name=u'级别对应instance_id')
    date_field = models.DateField(db_index=True, verbose_name=u'日期')
    name = models.CharField(max_length=64, null=True, verbose_name=u'描述')
    pic_path = models.CharField(max_length=256, null=True, verbose_name=u'图片')
    quantity = models.IntegerField(default=0, verbose_name=u'库存数量')
    inferior_num = models.IntegerField(default=0, verbose_name=U'次品数量')
    amount = models.FloatField(default=0, verbose_name=u'库存金额')
    uni_key = models.CharField(max_length=64, unique=True, verbose_name=u'唯一标识')
    record_type = models.IntegerField(choices=record_type_choices(), db_index=True, verbose_name=u'记录类型')
    timely_type = models.IntegerField(default=constants.TIMELY_TYPE_DATE,
                                      choices=timely_type_choices(), db_index=True, verbose_name=u'时间维度类型')

    # uni_key = date_field + current_id + record_type + timely_type
    class Meta:
        db_table = 'statistics_product_stock_stat'
        app_label = 'statistics'
        verbose_name = u'库存统计表'
        verbose_name_plural = u'库存统计列表'

    def __unicode__(self):
        return u'<%s-%s>' % (self.id, self.uni_key)


def update_parent_stock_stats(sender, instance, created, **kwargs):
    from statistics.tasks import task_update_parent_stock_stats, task_update_agg_stock_stats, gen_date_ftt_info, find_upper_timely_type

    if instance.record_type <= constants.TYPE_AGG:  #
        # 小于买手级别的  都要更新 周\月\季度\年度细分
        if instance.timely_type == constants.TIMELY_TYPE_DATE:  # 每天的总计更新 触发 周 和 月的更新
            time_from_1, time_to_1, tag_1 = gen_date_ftt_info(instance.date_field, constants.TIMELY_TYPE_WEEK)
            task_update_agg_stock_stats.delay(instance, time_from_1, time_to_1, constants.TIMELY_TYPE_WEEK, tag_1)
            time_from_2, time_to_2, tag_2 = gen_date_ftt_info(instance.date_field, constants.TIMELY_TYPE_MONTH)
            task_update_agg_stock_stats.delay(instance, time_from_2, time_to_2, constants.TIMELY_TYPE_MONTH, tag_2)

        elif instance.timely_type >= constants.TIMELY_TYPE_MONTH:  # 月更新触发 上级的所有更新
            upper_timely_type = find_upper_timely_type(instance.timely_type)  # 上级的时间维度 例如 周记录 更新的上一个时间维度 是 月份
            time_from, time_to, tag = gen_date_ftt_info(instance.date_field, upper_timely_type)
            task_update_agg_stock_stats.delay(instance, time_from, time_to, upper_timely_type, tag)

    if instance.timely_type == constants.TIMELY_TYPE_DATE:  # 日报细分类型 才更新 父级别 和 日报告
        task_update_parent_stock_stats.delay(instance)  # 更新 父级别


post_save.connect(update_parent_stock_stats, sender=ProductStockStat,
                  dispatch_uid='post_save_update_parent_stock_stats')


class DailyStat(BaseModel):
    """
        日统计　没有考虑错误数据
    """
    total_stock = models.FloatField(default=0, verbose_name=u'总库存')
    total_amount = models.FloatField(default=0, verbose_name=u'总金额')
    total_youni_stock = models.FloatField(default=0, verbose_name=u'总优尼库存')
    total_youni_amount = models.FloatField(default=0, verbose_name=u'总优尼金额')
    total_noyouni_stock = models.FloatField(default=0, verbose_name=u'非优尼库存')
    total_noyouni_amount = models.FloatField(default=0, verbose_name=u'非优尼金额')
    # total_xiaolu_stock = models.FloatField(default=0, verbose_name=u'小鹿标准库存')
    # total_xiaolu_amount = models.FloatField(default=0, verbose_name=u'小鹿标准金额')
    total_order = models.FloatField(default=0, verbose_name=u'月订单总营收')
    total_purchase = models.FloatField(default=0, verbose_name=u'月采购总支出')
    daytime = models.DateTimeField(verbose_name=u'统计日')
    note = models.CharField(max_length=1000, verbose_name=u'备注')

    class Meta:
        db_table = 'statistics_daily_stat'
        app_label = 'statistics'
        verbose_name = u'小鹿资产日统计表'
        verbose_name_plural = u'小鹿资产日统计表'

    @staticmethod
    def create(daytime):
        """
            celery每天执行一次
        """
        daytime = datetime.datetime(daytime.year, daytime.month, daytime.day)
        total_stock = DailyStat.get_total_stock()
        total_amount = DailyStat.get_total_amount()
        time_begin = datetime.datetime(daytime.year, daytime.month, 1)
        total_order = DailyStat.get_total_order_amount(time_begin, daytime)
        total_purchase = DailyStat.get_total_purchase(time_begin, daytime)
        DailyStat(
            total_stock=total_stock,
            total_amount=total_amount,
            total_order=total_order,
            total_purchase=total_purchase,
            total_youni_stock=DailyStat.get_youni_stock(),
            total_youni_amount=DailyStat.get_youni_total_amount(),
            total_noyouni_stock=DailyStat.get_noyouni_stock(),
            total_noyouni_amount=DailyStat.get_noyouni_total_amount(),
            daytime=daytime
        ).save()
        return

    def set_note(self, note):
        self.note = note
        self.save()
        return

    @staticmethod
    def get_total_stock():
        from shopback.items.models import SkuStock
        from shopback.items.models import Product

        return SkuStock.objects.exclude(product__type=Product.NORMAL_SALE,
                                               product__status=Product.NORMAL).aggregate(
            n=Sum("history_quantity") + Sum('adjust_quantity') + Sum('inbound_quantity') + Sum('return_quantity') - Sum(
                'rg_quantity') - Sum('post_num')).get('n') or 0

    @staticmethod
    def get_total_amount():
        from django.db import connection

        sql = """SELECT SUM(p.cost * (s.history_quantity + s.adjust_quantity + s.inbound_quantity + s.return_quantity - s.post_num - s.rg_quantity)) AS money
FROM shop_items_product AS p LEFT JOIN shop_items_productskustats AS s ON p.id = s.product_id
WHERE p.status = 'normal' and not p.outer_id like 'RMB%';"""
        cursor = connection.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()[0][0]
        cursor.close()
        return res

    @staticmethod
    def get_noyouni_stock():
        from shopback.items.models import SkuStock
        from shopback.items.models import Product
        return SkuStock.objects.filter(product__status=Product.NORMAL, product__type=Product.NORMAL_SALE).exclude(product__category_id=1).aggregate(
            n=Sum("history_quantity") + Sum('adjust_quantity') + Sum('inbound_quantity') + Sum('return_quantity') - Sum(
                'rg_quantity') - Sum('post_num')).get('n') or 0

    @staticmethod
    def get_noyouni_total_amount():
        from django.db import connection

        sql = """SELECT SUM(p.cost * (s.history_quantity + s.adjust_quantity + s.inbound_quantity + s.return_quantity - s.post_num - s.rg_quantity)) AS money
FROM shop_items_product AS p LEFT JOIN shop_items_productskustats AS s ON p.id = s.product_id
WHERE p.status = 'normal' and not p.outer_id like 'RMB%' and not p.category_id=1;"""
        cursor = connection.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()[0][0]
        cursor.close()
        return res


    @staticmethod
    def get_youni_stock():
        from shopback.items.models import SkuStock
        from shopback.items.models import Product
        return SkuStock.objects.filter(product__status=Product.NORMAL, product__category_id=1, product__type=Product.NORMAL_SALE).aggregate(
            n=Sum("history_quantity") + Sum('adjust_quantity') + Sum('inbound_quantity') + Sum('return_quantity') - Sum(
                'rg_quantity') - Sum('post_num')).get('n') or 0

    @staticmethod
    def get_youni_total_amount():
        from django.db import connection

        sql = """SELECT SUM(p.cost * (s.history_quantity + s.adjust_quantity + s.inbound_quantity + s.return_quantity - s.post_num - s.rg_quantity)) AS money
FROM shop_items_product AS p LEFT JOIN shop_items_productskustats AS s ON p.id = s.product_id
WHERE p.status = 'normal' and not p.outer_id like 'RMB%' and p.category_id=1;"""
        cursor = connection.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()[0][0]
        cursor.close()
        return res


    @staticmethod
    def get_total_order_amount(time_begin, time_end):
        from flashsale.pay.models import SaleOrder, SaleTrade

        return SaleOrder.objects.filter(pay_time__range=(time_begin, time_end),
                                        status__in=[2, 3, 4, 5, 6], refund_status=0,
                                        sale_trade__order_type=SaleTrade.SALE_ORDER).aggregate(n=Sum('payment')).get(
            'n') or 0

    @staticmethod
    def get_total_purchase(time_begin, time_end):
        from flashsale.finance.models import Bill
        r = Bill.objects.filter(status=Bill.STATUS_COMPLETED, created__range=(time_begin, time_end),
                                type=Bill.RECEIVE).aggregate(
            n=Sum('amount')).get('n') or 0
        p = Bill.objects.filter(status=Bill.STATUS_COMPLETED, created__range=(time_begin, time_end),
                                type=Bill.PAY).aggregate(
            n=Sum('amount')).get('n') or 0
        return p - r
