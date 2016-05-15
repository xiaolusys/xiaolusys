# coding=utf-8
import logging
import datetime
from core.managers import BaseManager
from shopback.items.models import ProductSku
from django.db.models import Sum

logger = logging.getLogger(__name__)


def find_sku_product(sku_id=None):
    """ 根据sku查找产品
    :param sku_id: product sku_id
    """
    psku = ProductSku.objects.filter(id=sku_id).first()
    if psku:
        return psku.product
    return None


def find_sku_model_id(sku_id=None):
    """ 根据sku查找款式id
    :param sku_id: product sku_id
    """
    product = find_sku_product(sku_id=sku_id)
    if product:
        return product.model_id
    return None


def find_sku_category_id(sku_id=None):
    """ 根据sku查找分类id
    :param sku_id: product sku_id
    """
    product = find_sku_product(sku_id=sku_id)
    if product and product.category:
        return product.category.cid
    return None


def find_sku_supplier_id(sku_id=None):
    """ 根据sku查找供应商id
    :param sku_id: product sku_id
    """
    product = find_sku_product(sku_id=sku_id)
    if product:
        sal_p, supplier = product.pro_sale_supplier()
        if supplier:
            return supplier.id
    return None


def calculate_sku_sale_stats(sku_id=None, pay_time=None):
    """ 计算sku的数量 信息 """
    from shopback.trades.models import PackageSkuItem
    pay_time_left = pay_time.date()
    pay_time_right = pay_time.date() + datetime.timedelta(days=1)
    packages = PackageSkuItem.objects.filter(sku_id=str(sku_id),
                                             pay_time__gte=pay_time_left, pay_time__lt=pay_time_right,
                                             assign_status__gte=PackageSkuItem.NOT_ASSIGNED,
                                             assign_status__lte=PackageSkuItem.FINISHED)
    packages_calculate = packages.values('sku_id').annotate(total_num=Sum('num'),
                                                            total_payment=Sum('payment'))
    if packages_calculate:
        sale_num = packages_calculate[0]['total_num']
        sale_value = packages_calculate[0]['total_payment']
        return sale_num, sale_value
    return 0, 0


class StatisticSaleNumManager(BaseManager):
    """ 先有总计的记录 在有供应商的记录 再有类别的记录 以此类推 """

    def get_or_create_total_sale_record(self, pay_time, *args, **kwargs):
        """ 创建某一天的总计记录 """
        if not pay_time:
            logger.warn(u"create_supplier_record: pay_time-%s" % pay_time)
            return
        total_sale_record, state = self.get_or_create(
            pay_date=pay_time.date(),
            uniq_id=''.join([pay_time.strftime('%Y-%m-%d')]),  # 总计只有日期并且是唯一的
            record_type=self.model.TYPE_TOTAL
        )
        return total_sale_record, state

    def get_or_create_supplier_sale_record(self, sku_id, pay_time, total_sale_record_id=None, *args, **kwargs):
        """ 创建供应商的销量条目 """
        if not (sku_id and pay_time):
            logger.warn(u"get_or_create_supplier_sale_record: sku_id-%s, pay_time-%s" % (sku_id, pay_time))
            return
        if not total_sale_record_id:
            total_sale_record, state = self.get_or_create_total_record(pay_time=pay_time)
            total_sale_record_id = total_sale_record.id if total_sale_record else None
        supplier_id = find_sku_supplier_id(sku_id=sku_id)  # 查找供应商
        if not (supplier_id and total_sale_record_id):
            logger.error(u'get_or_create_supplier_sale_record supplier_id is None')
            return
        supplier_sale_record, state = self.get_or_create(
            upper_grade=total_sale_record_id,  # 总计的id
            target_id=supplier_id,
            pay_date=pay_time.date(),
            uniq_id=''.join([pay_time.strftime('%Y-%m-%d'), str(supplier_id)]),
            record_type=self.model.TYPE_SUPPLIER
        )
        return supplier_sale_record, state

    def get_or_create_category_sale_record(self, sku_id, pay_time, supplier_sale_record_id=None, *args, **kwargs):
        """ 创建供应商的销量条目 """
        if not (sku_id and pay_time):
            logger.warn(u"get_or_create_category_sale_record: sku_id-%s, pay_time-%s" % (sku_id, pay_time))
            return
        if not supplier_sale_record_id:
            supplier_sale_record, state = self.get_or_create_supplier_sale_record(sku_id=sku_id, pay_time=pay_time)
            supplier_sale_record_id = supplier_sale_record.id if supplier_sale_record else None
        category_id = find_sku_category_id(sku_id=sku_id)  # 查找供应商
        if not (category_id and supplier_sale_record_id):
            logger.error(u'get_or_create_category_sale_record category is None')
            return
        category_sale_record, state = self.get_or_create(
            upper_grade=supplier_sale_record_id,  # 供应商上级的id
            target_id=category_id,
            pay_date=pay_time.date(),
            uniq_id=''.join([pay_time.strftime('%Y-%m-%d'), str(category_id)]),
            record_type=self.model.TYPE_CATEGORY
        )
        return category_sale_record, state

    def get_or_create_model_sale_record(self, sku_id, pay_time, category_sale_record_id=None, *args, **kwargs):
        """ 创建供应商的销量条目 """
        if not (sku_id and pay_time):
            logger.warn(u"get_or_create_model_sale_record: sku_id-%s, pay_time-%s" % (sku_id, pay_time))
            return
        if not category_sale_record_id:
            category_sale_record, state = self.get_or_create_category_sale_record(sku_id=sku_id, pay_time=pay_time)
            category_sale_record_id = category_sale_record.id if category_sale_record else None
        model_id = find_sku_model_id(sku_id=sku_id)  # 查找供应商
        if not (model_id and category_sale_record_id):
            logger.error(u'get_or_create_model_sale_record category is None')
            return
        model_sale_record, state = self.get_or_create(
            upper_grade=category_sale_record_id,  # 类别上级的id
            target_id=model_id,
            pay_date=pay_time.date(),
            uniq_id=''.join([pay_time.strftime('%Y-%m-%d'), str(model_id)]),
            record_type=self.model.TYPE_MODEL
        )
        return model_sale_record, state

    def get_or_create_product_sale_record(self, sku_id, pay_time, model_sale_record_id=None, *args, **kwargs):
        """ 创建供应商的销量条目 """
        if not (sku_id and pay_time):
            logger.warn(u"get_or_create_product_sale_record: sku_id-%s, pay_time-%s" % (sku_id, pay_time))
            return
        if not model_sale_record_id:
            model_sale_record, state = self.get_or_create_model_sale_record(sku_id=sku_id, pay_time=pay_time)
            model_sale_record_id = model_sale_record.id if model_sale_record else None
        product = find_sku_product(sku_id=sku_id)  # 查找供应商
        if not (product and model_sale_record_id):
            logger.error(u'get_or_create_product_sale_record product is None')
            return
        category_sale_record, state = self.get_or_create(
            upper_grade=model_sale_record_id,  # 款式上级的id
            target_id=product.id,
            pay_date=pay_time.date(),
            uniq_id=''.join([pay_time.strftime('%Y-%m-%d'), str(product.id)]),
            record_type=self.model.TYPE_COLOR
        )
        return category_sale_record, state

    def get_or_create_sku_sale_record(self, sku_id, pay_time, product_sale_record_id=None, *args, **kwargs):
        """ 创建sku的销量条目 """
        if not (sku_id and pay_time):
            logger.warn(u"get_or_create_sku_sale_record: sku_id-%s, pay_time-%s" % (sku_id, pay_time))
            return
        if not product_sale_record_id:
            product_sale_record, state = self.get_or_create_product_sale_record(sku_id=sku_id, pay_time=pay_time)
            product_sale_record_id = product_sale_record.id if product_sale_record else None
        category_sale_record, state = self.get_or_create(
            upper_grade=product_sale_record_id,  # 颜色上级(product级)记录的id
            target_id=sku_id,
            pay_date=pay_time.date(),
            uniq_id=''.join([pay_time.strftime('%Y-%m-%d'), str(sku_id)]),
            record_type=self.model.TYPE_SKU
        )
        return category_sale_record, state

    def aggregete_sale(self, queryset):
        """ 聚合计算销量等数据
        :param queryset: StatisticSaleNum 的记录
        """
        sale_num = queryset.values('sale_num').aggregate(t_num=Sum('sale_num')).get('t_num') or 0
        sale_value = queryset.values('sale_value').aggregate(t_value=Sum('sale_value')).get('t_value') or 0
        return sale_num, sale_value

    def calculate_update_sale_stat(self, product_rd, model_rd, category_rd, supplier_rd, total_rd):
        """ 更新销量等数据
        :param total_rd: StatisticSaleNum TYPE_TOTAL record
        :param supplier_rd: StatisticSaleNum TYPE_SUPPLIER record
        :param category_rd: StatisticSaleNum TYPE_CATEGORY record
        :param model_rd: StatisticSaleNum TYPE_MODEL record
        :param product_rd: StatisticSaleNum TYPE_COLOR record
        """
        # 过滤sku级别的上级id等于product_rd.id的记录 计算求和
        sku_rds = self.filter(upper_grade=product_rd.id, record_type=self.model.TYPE_SKU)
        product_rd.sale_num, product_rd.sale_value = self.aggregete_sale(sku_rds)
        product_rd.save(update_fields=['sale_num', 'sale_value'])  # 更新颜色级别(产品级别)

        product_rds = self.filter(upper_grade=model_rd.id, record_type=self.model.TYPE_COLOR)
        model_rd.sale_num, model_rd.sale_value = self.aggregete_sale(product_rds)
        model_rd.save(update_fields=['sale_num', 'sale_value'])  # 更新款式级别

        model_rds = self.filter(upper_grade=category_rd.id, record_type=self.model.TYPE_MODEL)
        category_rd.sale_num, category_rd.sale_value = self.aggregete_sale(model_rds)
        category_rd.save(update_fields=['sale_num', 'sale_value'])  # 更新分类级别

        category_rds = self.filter(upper_grade=supplier_rd.id, record_type=self.model.TYPE_CATEGORY)
        supplier_rd.sale_num, supplier_rd.sale_value = self.aggregete_sale(category_rds)
        supplier_rd.save(update_fields=['sale_num', 'sale_value'])  # 更新供应商级别

        supplier_rds = self.filter(upper_grade=total_rd.id, record_type=self.model.TYPE_SUPPLIER)
        total_rd.sale_num, total_rd.sale_value = self.aggregete_sale(supplier_rds)
        total_rd.save(update_fields=['sale_num', 'sale_value'])  # 更新日期综合统计

    def create_and_update_sale_stat(self, sku_id, pay_time):
        """
        创建一条sku销量统计记录
        1. 创建日期总记录
        2. 创建供应商记录
        3. 创建类别记录
        4. 创建款式记录
        5. 创建产品记录
        6. 创建sku记录
        """
        total, _ = self.get_or_create_total_sale_record(pay_time=pay_time)
        if not total:
            logger.warn(u"StatisticSaleNumManager: sku_id:%s no total record !" % sku_id)
            return
        supplier_rd, _ = self.get_or_create_supplier_sale_record(sku_id=sku_id, pay_time=pay_time,
                                                                 total_sale_record_id=total.id)
        if not supplier_rd:
            logger.warn(u"StatisticSaleNumManager: sku_id:%s no total supplier_rd !" % sku_id)
            return
        category_rd, _ = self.get_or_create_category_sale_record(sku_id=sku_id, pay_time=pay_time,
                                                                 supplier_sale_record_id=supplier_rd.id)
        if not category_rd:
            logger.warn(u"StatisticSaleNumManager:sku_id:%s no total category_rd !" % sku_id)
            return
        model_rd, _ = self.get_or_create_model_sale_record(sku_id=sku_id, pay_time=pay_time,
                                                           category_sale_record_id=category_rd.id)
        if not model_rd:
            logger.warn(u"StatisticSaleNumManager: sku_id:%s no total model_rd !" % sku_id)
            return
        product_rd, _ = self.get_or_create_product_sale_record(sku_id=sku_id, pay_time=pay_time,
                                                               model_sale_record_id=model_rd.id)
        if not product_rd:
            logger.warn(u"StatisticSaleNumManager: sku_id:%s no total product rd !" % sku_id)
            return
        sku_rd, _ = self.get_or_create_sku_sale_record(sku_id=sku_id, pay_time=pay_time,
                                                       product_sale_record_id=product_rd.id)
        if not sku_rd:
            logger.warn(u"StatisticSaleNumManager: sku_id:%s no total sku_rd !" % sku_id)
            return
        # 创建成功后计算 叠加各个层级的数量
        sku_rd.sale_num, sku_rd.sale_value = calculate_sku_sale_stats(sku_id=sku_id, pay_time=pay_time)
        sku_rd.save(update_fields=['sale_num', 'sale_value'])
        # 更新各个级别的数量信息
        self.calculate_update_sale_stat(product_rd, model_rd, category_rd, supplier_rd, total)
