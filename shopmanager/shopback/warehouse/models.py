# -*- coding:utf8 -*-
import logging
from django.utils.encoding import smart_unicode
from django.db import models
from core.models import AdminModel
from shopback.warehouse import constants
from shopback.logistics.models import LogisticsCompany

logger = logging.getLogger(__name__)


class WareHouse(models.Model):
    """ 仓库 """

    ware_name = models.CharField(max_length=32, blank=True, verbose_name='仓库名')
    city = models.CharField(max_length=32, blank=True, verbose_name='所在城市')
    address = models.TextField(max_length=256, blank=True, verbose_name='详细地址')

    in_active = models.BooleanField(default=True, verbose_name='有效')
    extra_info = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'shop_ware_house'
        app_label = 'warehouse'
        verbose_name = u'仓库'
        verbose_name_plural = u'仓库列表'

    def __unicode__(self):
        return smart_unicode(self.ware_name)


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