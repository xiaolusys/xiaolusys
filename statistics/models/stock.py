# coding=utf-8
from copy import copy
from django.db import models
from django.db.models import Sum, F
from core.fields import JSONCharMyField
from shopback.items.models import SkuStock, ProductSku, Product
from shopback.trades.models import PackageSkuItem, PSI_TYPE, PSI_STATUS


class StockDailyReport(models.Model):
    stat_time = models.DateTimeField(auto_now=True)
    stat_sku_cnt = models.IntegerField(default=0)
    err_skus = JSONCharMyField(default=[], max_length=10000, verbose_name=u'出错sku列表', help_text=u"")

    class Meta:
        db_table = 'stat_stockdailyreport'

    @staticmethod
    def create():
        sdr = StockDailyReport()
        sdr.save()
        queryset = SkuStock.objects.filter(status=0).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0, return_quantity=0, rg_quantity=0, post_num=0)
        sdr.stat_sku_cnt = queryset.count()
        check_ids = StockDailyReport.check_all()
        for stock in SkuStock.objects.filter(sku_id__in=check_ids):
            ori_dict = copy(stock.to_dict())
            stat = stock.restat()
            stat_dict = stock.to_dict()
            if stat:
                sdr.err_skus.append(stock.sku_id)
                StockDailyReportItem(report=sdr, sku_id=stock.sku_id, sys_data=ori_dict, stat_data=stat_dict).save()
        sdr.save()
        return sdr

    def screenshot(self, ids):
        check_ids = StockDailyReport
        queryset = SkuStock.objects.filter(status=0).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0, return_quantity=0, rg_quantity=0, post_num=0)
        self.stat_sku_cnt = queryset.count()
        for stock in queryset.all():
            ori_dict = copy(stock.to_dict())
            stat = stock.restat()
            stat_dict = stock.to_dict()
            if stat:
                self.err_skus.append(stock.sku_id)
                StockDailyReportItem(report=self, sku_id=stock.sku_id, sys_data=ori_dict, stat_data=stat_dict).save()
        self.save()

    @staticmethod
    def check_all():
        res = StockDailyReport.check_assign_num()
        res.extend(StockDailyReport.check_inbound_quantity())
        res.extend(StockDailyReport.check_sold_num())
        res.extend(StockDailyReport.check_post_num())
        res.extend(StockDailyReport.check_adjust_quantity())
        res.extend(StockDailyReport.check_rg_quantity())
        res.extend(StockDailyReport.check_shoppingcart_num())
        res.extend(StockDailyReport.check_waitingpay_num())
        res.extend(StockDailyReport.check_paid_num())
        res.extend(StockDailyReport.check_return_quantity())
        for status in ('paid', 'prepare_book', 'booked', 'third_send', 'assigned', 'merged', 'waitscan', 'waitpost', 'sent', 'finish'):
            res.extend(StockDailyReport.check_psi_status_num(status))
        return list(set(res))

    @staticmethod
    def check_assign_num(sku_ids=[]):
        err_skus = set([])
        condition = {
            'status': 0,
            'product__type': 0
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0,
                                                             return_quantity=0, rg_quantity=0, post_num=0, sold_num=0)
        sku_ids_dict = {p.sku_id: p.assign_num for p in queryset.all()}
        condition2 = {
            'type__in': [PSI_TYPE.NORMAL, PSI_TYPE.BYHAND,
                         PSI_TYPE.RETURN_GOODS, PSI_TYPE.TIANMAO],
            'pay_time__gt': SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
            'assign_status': 2
        }
        if sku_ids:
            condition2['sku_id__in'] = sku_ids
        res = PackageSkuItem.objects.filter(pay_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME, assign_status=1).values(
            'sku_id').annotate(total=Sum('num'))
        res = {int(k['sku_id']): k['total'] for k in res}
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)

    @staticmethod
    def check_inbound_quantity(sku_ids=[]):
        from shopback.dinghuo.models import OrderDetail
        err_skus = set([])
        condition = {
            'status': 0,
            'product__type': 0
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0,
                                                                return_quantity=0, rg_quantity=0, post_num=0, sold_num=0)
        sku_ids_dict = {p.sku_id: p.inbound_quantity for p in queryset.all()}
        res = OrderDetail.objects.filter(arrival_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME).values(
            'chichu_id').annotate(total=Sum('arrival_quantity'))
        OrderDetail.objects.filter(arrival_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME).aggregate(total=Sum('arrival_quantity'))
        res = {int(k['chichu_id']): k['total'] for k in res}
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)

    @staticmethod
    def check_sold_num(sku_ids=[]):
        from flashsale.pay.models import SaleOrder
        err_skus = set([])
        condition = {
            'status': 0,
            'product__type__in': [0, 1]
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0,
                                                                inbound_quantity=0,
                                                                return_quantity=0, rg_quantity=0, post_num=0,
                                                                sold_num=0)
        sku_ids_dict = {p.sku_id: p.sold_num for p in queryset.all()}
        res = PackageSkuItem.objects.filter(type=PSI_TYPE.NORMAL,
                                            pay_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
                                            assign_status__in=[2, 0, 1, 4]).values('sku_id').annotate(total=Sum('num'))
        res = {int(k['sku_id']): k['total'] for k in res}
        virtual_sku_ids = list(
            ProductSku.objects.filter(id__in=sku_ids_dict.keys(), product__type=1).values_list('id', flat=True))
        res2 = SaleOrder.objects.filter(sku_id__in=virtual_sku_ids, status__in=[2, 3, 4, 5],
                                        pay_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME).values('sku_id').annotate(
            total=Sum('num'))
        res2 = {int(k['sku_id']): k['total'] for k in res2}
        res.update(res2)
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)

    @staticmethod
    def check_post_num(sku_ids=[]):
        err_skus = set([])
        condition = {
            'status': 0,
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0,
                                                             return_quantity=0, rg_quantity=0, post_num=0, sold_num=0)
        sku_ids_dict = {p.sku_id: p.post_num for p in queryset.all()}
        condition2 = {
            'type__in': [PSI_TYPE.NORMAL, PSI_TYPE.TIANMAO,
                         PSI_TYPE.BYHAND, PSI_TYPE.RETURN_GOODS],
            'pay_time__gt': SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
            'assign_status': 2
        }
        if sku_ids:
            condition2['sku_id__in'] = sku_ids
        res = PackageSkuItem.objects.filter(**condition2).values('sku_id').annotate(total=Sum('num'))
        res = {int(k['sku_id']): k['total'] for k in res}
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)

    @staticmethod
    def check_adjust_quantity(sku_ids=[]):
        from shopback.warehouse.models import StockAdjust
        err_skus = set([])
        condition = {
            'status': 0,
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0,
                                                                return_quantity=0, rg_quantity=0, post_num=0, sold_num=0)
        sku_ids_dict = {p.sku_id: p.adjust_quantity for p in queryset.all()}
        res = StockAdjust.objects.filter(status=1).values('sku_id').annotate(total=Sum('num'))
        res = {int(k['sku_id']): k['total'] for k in res}
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)

    @staticmethod
    def check_rg_quantity(sku_ids=[]):
        from shopback.dinghuo.models import OrderDetail, RGDetail, ReturnGoods
        err_skus = set([])
        condition = {
            'status': 0,
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0,
                                                             return_quantity=0, rg_quantity=0, post_num=0, sold_num=0)
        sku_ids_dict = {p.sku_id: p.rg_quantity for p in queryset.all()}
        res = RGDetail.objects.filter(
            created__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
            return_goods__status__in=[ReturnGoods.DELIVER_RG,
                                      ReturnGoods.REFUND_RG,
                                      ReturnGoods.SUCCEED_RG],
            type=RGDetail.TYPE_REFUND).values('skuid').annotate(total=Sum('num'))
        res = {int(k['skuid']): k['total'] for k in res}
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)

    @staticmethod
    def check_shoppingcart_num(sku_ids=[]):
        from flashsale.pay.models import ShoppingCart
        err_skus = set([])
        condition = {
            'status': 0,
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0,
                                                             return_quantity=0, rg_quantity=0, post_num=0, sold_num=0)
        sku_ids_dict = {p.sku_id: p.shoppingcart_num for p in queryset.all()}
        res = ShoppingCart.objects.filter(status=ShoppingCart.NORMAL).values('sku_id').annotate(
                            total=Sum('num'))
        res = {int(k['sku_id']): k['total'] for k in res}
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)

    @staticmethod
    def check_waitingpay_num(sku_ids=[]):
        from flashsale.pay.models import SaleOrder
        err_skus = set([])
        condition = {
            'status': 0,
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0,
                                                             return_quantity=0, rg_quantity=0, post_num=0, sold_num=0, waitingpay_num=0)
        sku_ids_dict = {p.sku_id: p.waitingpay_num for p in queryset.all()}
        res = SaleOrder.objects.filter(status=SaleOrder.WAIT_BUYER_PAY).values('sku_id').annotate(
                            total=Sum('num'))
        res = {int(k['sku_id']): k['total'] for k in res}
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)

    @staticmethod
    def check_paid_num(sku_ids=[]):
        from flashsale.pay.models import SaleOrder
        err_skus = set([])
        condition = {
            'status': 0,
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0,
                                                             return_quantity=0, rg_quantity=0, post_num=0, sold_num=0, paid_num=0)
        sku_ids_dict = {p.sku_id: p.paid_num for p in queryset.all()}
        res = SaleOrder.objects.filter(status__in=[2, 3, 4, 5], created__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME).values('sku_id').annotate(
                            total=Sum('num'))
        SaleOrder.objects.filter(sku_id=296989, status__in=[2, 3, 4, 5], created__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME).values('sku_id').annotate(
                            total=Sum('num'))
        res = {int(k['sku_id']): k['total'] for k in res}
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)

    @staticmethod
    def check_return_quantity(sku_ids=[]):
        from shopback.refunds.models import RefundProduct
        err_skus = set([])
        condition = {
            'status': 0,
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0,
                                                             return_quantity=0, rg_quantity=0, post_num=0, sold_num=0)
        sku_ids_dict = {p.sku_id: p.return_quantity for p in queryset.all()}
        res = RefundProduct.objects.filter(created__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
                                           can_reuse=True).exclude(sku_id=None).values('sku_id').annotate(
            total=Sum('num'))
        res = {int(k['sku_id']): k['total'] for k in res}
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)

    @staticmethod
    def check_psi_status_num(status='paid', sku_ids=[]):
        err_skus = set([])
        psi_attr_status = [l[0] for l in PSI_STATUS.CHOICES]
        psi_attrs_dict = {s: 'psi_%s_num' % s for s in psi_attr_status}
        attr = psi_attrs_dict[status]
        condition = {
            'status': 0,
        }
        if sku_ids:
            condition['sku_id__in'] = sku_ids
        queryset = SkuStock.objects.filter(**condition).exclude(adjust_quantity=0, history_quantity=0, inbound_quantity=0,
                                                                return_quantity=0, rg_quantity=0, post_num=0, sold_num=0)
        sku_ids_dict = {p.sku_id: getattr(p, attr) for p in queryset.all()}
        res = PackageSkuItem.objects.filter(type=PSI_TYPE.NORMAL,
                                            pay_time__gt=SkuStock.PRODUCT_SKU_STATS_COMMIT_TIME,
                                            status=status). \
            exclude(status=PSI_STATUS.CANCEL).exclude(type__in=[PSI_TYPE.RETURN_INFERIOR, PSI_TYPE.RETURN_OUT_ORDER]).values('sku_id').annotate(
            total=Sum('num'))
        res = {int(k['sku_id']): k['total'] for k in res}
        for sku_id in res:
            if res[sku_id] != sku_ids_dict.get(sku_id, 0):
                print sku_id, res[sku_id], sku_ids_dict.get(sku_id, 0)
                err_skus.add(sku_id)
        for sku_id in sku_ids_dict:
            if sku_ids_dict[sku_id] != res.get(sku_id, 0):
                print sku_id, sku_ids_dict[sku_id], res.get(sku_id, 0)
                err_skus.add(sku_id)
        return list(err_skus)


class StockDailyReportItem(models.Model):
    report = models.ForeignKey(StockDailyReport)
    sku_id = models.IntegerField()
    sys_data = JSONCharMyField(max_length=5000, verbose_name=u'系统sku数据', help_text=u"")
    stat_data = JSONCharMyField(max_length=5000, verbose_name=u'统计sku数据', help_text=u"")

    class Meta:
        db_table = 'stat_stockdailyreportitem'


