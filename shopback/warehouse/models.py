# -*- coding:utf8 -*-
import logging
from django.utils.encoding import smart_unicode
from django.db import models
from django.db.models import Sum
from core.models import AdminModel
from shopback.warehouse import constants
from shopback.logistics.models import LogisticsCompany
from shopback.items.models import ProductSku
from django.db.models.signals import pre_save, post_save
logger = logging.getLogger(__name__)


class WareHouse(models.Model):
    """ 仓库 """

    ware_name = models.CharField(max_length=32, blank=True, verbose_name=u'仓库名')
    city = models.CharField(max_length=32, blank=True, verbose_name=u'所在城市')
    address = models.TextField(max_length=256, blank=True, verbose_name=u'详细地址')

    in_active = models.BooleanField(default=True, verbose_name=u'有效')
    extra_info = models.TextField(blank=True, verbose_name=u'备注')

    class Meta:
        db_table = 'shop_ware_house'
        app_label = 'warehouse'
        verbose_name = u'仓库'
        verbose_name_plural = u'仓库列表'

    def __unicode__(self):
        return smart_unicode(self.ware_name)


class StockAdjust(AdminModel):
    """库存调整"""
    ware_by = models.IntegerField(default=constants.WARE_NONE, db_index=True, choices=constants.WARE_CHOICES,
                                  verbose_name=u'所属仓库', blank=True)
    sku = models.ForeignKey(ProductSku, null=True, verbose_name=u'SKU')
    # sku_id = models.IntegerField(null=True, verbose_name=u'SKU')
    num = models.IntegerField(default=0, verbose_name=u'调整数')
    inferior = models.BooleanField(default=False, verbose_name=u'次品')
    status = models.IntegerField(choices=((0, u'初始'), (1, u'已处理'), (-1, u'已作废')), default=0, blank=True)
    note = models.CharField(max_length=1000, verbose_name=u'备注', default='', blank=True)

    class Meta:
        db_table = 'shop_ware_stock_adjust'
        app_label = 'warehouse'
        verbose_name = u'库存调整'
        verbose_name_plural = u'库存调整列表'

    @staticmethod
    def create(creator, sku_id, num, ware_by=constants.WARE_NONE, inferior=False):
        StockAdjust(
            creator=creator,
            sku_id=sku_id,
            num=num,
            ware_by=ware_by,
            inferior=inferior
        ).save()


def update_productskustats_adjust_num(sender, instance, created, **kwargs):
    if instance.status == 0:
        from shopback.items.models import SkuStock, InferiorSkuStats
        from shopback.items.models import ProductSku
        if not instance.inferior:
            #　adjust_quantity = StockAdjust.objects.filter(sku_id=instance.sku_id, inferior=False)\
            #                  .aggregate(n=Sum('num')).get('n') or 0
            # SkuStock.update_adjust_num(instance.sku_id, adjust_quantity)
            SkuStock.add_adjust_num(instance.sku_id, instance.num)
        else:
            adjust_quantity = StockAdjust.objects.filter(sku_id=instance.sku_id, inferior=True)\
                              .aggregate(n=Sum('num')).get('n') or 0
            InferiorSkuStats.update_adjust_num(instance.sku_id, adjust_quantity)
        StockAdjust.objects.filter(id=instance.id).update(status=1)
        ProductSku.objects.filter(id=instance.sku_id).update(quantity=instance.sku.stat.realtime_quantity)
        if instance.num > 0:
            SkuStock.get_by_sku(instance.sku_id).assign()
        else:
            SkuStock.get_by_sku(instance.sku_id).relase_assign()


post_save.connect(update_productskustats_adjust_num, sender=StockAdjust,
                  dispatch_uid='post_save_update_warehouse_receipt_status')


class ReceiptGoods(AdminModel):
    """ 记录仓库接收到的货物信息 """
    receipt_type = models.IntegerField(db_index=True, default=constants.RECEIPT_BUYER,
                                       choices=constants.receipt_type_choice(), verbose_name=u'记录类型')
    weight = models.FloatField(default=0.0, verbose_name=u'重量')
    weight_time = models.DateTimeField(null=True, blank=True, verbose_name=u'称重时间')
    express_no = models.CharField(db_index=True, max_length=64, verbose_name=u'快递号')
    express_company = models.IntegerField(db_index=True, verbose_name=u'快递公司')
    status = models.BooleanField(default=False, db_index=True, verbose_name=u'是否拆包')
    memo = models.TextField(max_length=256, null=True, blank=True, verbose_name=u'备注')

    class Meta:
        unique_together = ('express_no', "express_company")
        db_table = 'shop_ware_house_receipt'
        app_label = 'warehouse'
        verbose_name = u'仓库收货'
        verbose_name_plural = u'仓库收货列表'

    def __unicode__(self):
        return u'%s-%s' % (self.receipt_type, self.express_no)

    def logistic_company(self):
        """ 物流公司 """
        return LogisticsCompany.objects.filter(id=self.express_company).first()

    @classmethod
    def update_status_by_open(cls, express_no):
        """ 拆包裹更新拆包状态 """
        receipts = cls.objects.filter(express_no=express_no)
        if receipts.count() > 1:
            logger.error(u'update_status_by_open :%s express has more than one' % express_no)
            return False
        receipt = receipts.first()
        if receipt and (receipt.status is False):
            receipt.status = True
            receipt.save(update_fields=['status'])
            return True
        return False