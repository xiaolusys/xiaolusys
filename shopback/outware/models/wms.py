# coding: utf8
from __future__ import absolute_import, unicode_literals

# TODO@MERON 库存调整记录，商品库存信息
import datetime
import json
from core.utils.timeutils import CJsonEncoder
from django.db import models, transaction
from .base import BaseWareModel


class OutwareSkuStock(BaseWareModel):
    """ 外仓商品库存 """

    sku_code = models.CharField(max_length=64, unique=True, verbose_name=u'内部SKU编号')

    push_sku_good_qty  = models.IntegerField(default=0, verbose_name=u'发给外仓SKU良品数', help_text=u'根据入仓实际收货良品数量累加')
    push_sku_bad_qty = models.IntegerField(default=0, verbose_name=u'发给外仓SKU次品数', help_text=u'根据入仓实际收货次品数量累加')

    pull_good_available_qty = models.IntegerField(default=0, verbose_name=u'外仓可分配良品总数')
    pull_good_lock_qty = models.IntegerField(default=0, verbose_name=u'外仓已锁定良品总数')
    pull_bad_qty = models.IntegerField(default=0, verbose_name=u'外仓次品总数')

    paid_num    = models.IntegerField(default=0, verbose_name=u'付款数量')
    package_num = models.IntegerField(default=0, verbose_name=u'发货数量')
    refund_num  = models.IntegerField(default=0, verbose_name=u'退货数量')
    adjust_num  = models.IntegerField(default=0, verbose_name=u'调整数量', help_text=u'跟库存调整值关联')

    last_pull_time = models.DateTimeField(null=False, default=datetime.datetime.now, db_index=True, verbose_name=u'库存最后更新日期')

    class Meta:
        db_table = 'outware_skustock'
        app_label = 'outware'
        verbose_name = u'外仓/对接商品SKU库存'
        verbose_name_plural = u'外仓/对接商品SKU库存'

    @property
    def now_quantity(self):
        return self.pull_good_available_qty

    @property
    def now_bad_quantity(self):
        return self.pull_bad_qty

    def set_good_available_qty(self, good_qty):
        self.pull_good_available_qty = good_qty

    def minus_good_available_qty(self, good_qty):
        self.pull_good_available_qty -= good_qty

    def plus_good_available_qty(self, good_qty):
        self.pull_good_available_qty += good_qty

    def minus_bad_qty(self, bad_qty):
        self.pull_bad_qty -= bad_qty

    def plus_bad_qty(self, bad_qty):
        self.pull_bad_qty += bad_qty

    def to_dict(self):
        attrs = ['sku_code', 'push_sku_good_qty', 'push_sku_bad_qty', 'pull_good_available_qty', 'pull_good_lock_qty',
                 'pull_bad_qty', 'paid_num', 'package_num', 'refund_num', 'adjust_num', 'last_pull_time']
        res = {}
        for attr in attrs:
            res[attr] = getattr(self, attr)
        return res

    def sync_stock_by_adjust(self, data):
        """
            更新实时库存数据，如果数据不与skustock的数据一致，则将原记录/新记录／skustock数据都保存到stockadjust当中。
        :param data:
        :return:
        """
        from shopback.warehouse.models import StockAdjust, constants
        from shopback.items.models import SkuStock, ProductSku, InferiorSkuStats
        ori_dict = self.to_dict()
        self.pull_bad_qty = data['bad_qty']
        self.pull_good_available_qty = data['good_available_qty']
        self.pull_good_lock_qty = data['good_lock_qty']
        self.last_pull_time = datetime.datetime.now()
        self.save()
        now_dict = self.to_dict()
        sku = ProductSku.get_by_outer_id(self.sku_code)
        stock = SkuStock.get_by_sku(sku.id)
        inferior_sku_stats = InferiorSkuStats.get_by_sku(sku.id)
        # 正品数不同
        if self.now_quantity != stock.realtime_quantity:
            note = '%s实时库存不同，我方%d,对方%d。本次新数据%s～我仓数据%s~原数据%s' %\
                   (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.now_quantity, stock.realtime_quantity, json.dumps(ori_dict, cls=CJsonEncoder),
                    json.dumps(stock.to_dict(), cls=CJsonEncoder), json.dumps(now_dict, cls=CJsonEncoder))
            delta = self.now_quantity - stock.realtime_quantity
            StockAdjust.create(None, sku.id, delta, constants.WARE_NONE, inferior=False, note=note)
        # 次品数不同
        elif self.now_bad_quantity != inferior_sku_stats.realtime_quantity:
            note = '%s次品库存不同，我方%d,对方%d。本次对方数据%s～我方数据%s~上次对方数据%s' %\
                   (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.now_quantity, inferior_sku_stats.realtime_quantity, json.dumps(ori_dict, cls=CJsonEncoder),
                    json.dumps(now_dict, cls=CJsonEncoder), json.dumps(inferior_sku_stats.to_dict(), cls=CJsonEncoder))
            delta = self.now_bad_quantity - inferior_sku_stats.realtime_quantity
            StockAdjust.create(None, sku.id, delta, constants.WARE_NONE, inferior=True, note=note)

    @staticmethod
    def sync_outsys(sku_codes):
        """
        [{u'bad_qty': 0,
          u'good_actl_qty': 0,
          u'good_available_qty': 0,
          u'good_lock_qty': 0,
          u'sku_id': u'4692976300211'}]
        """
        from shopback.outware.fengchao.sdks import get_skustock_by_qureyparams, FENGCHAO_SLYC_VENDOR_CODE
        res = get_skustock_by_qureyparams(sku_codes, FENGCHAO_SLYC_VENDOR_CODE)
        for line in res:
            outware_stock = OutwareSkuStock.objects.get(sku_code=line['sku_id'])
            outware_stock.sync_stock_by_adjust(line)

