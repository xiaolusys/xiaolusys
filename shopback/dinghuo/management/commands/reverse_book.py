# coding=utf-8

from django.core.management.base import BaseCommand

from shopback.dinghuo.models.purchase_order import OrderList
from django.conf import settings
from django.contrib.auth.models import User
from shopback.dinghuo.models_purchase import *

def reverse_book(self, third_package=False):
    from shopback.trades.models import PackageSkuItem
    self.status = PurchaseOrder.OPEN
    self.save()
    self.details.update(status=PurchaseOrder.OPEN)
    self.arrangements.filter(status=PurchaseArrangement.EFFECT).update(purchase_order_status=PurchaseOrder.OPEN,
                                                                       initial_book=False)
    oids = [pa.oid for pa in self.arrangements.filter(status=PurchaseArrangement.EFFECT)]
    if not third_package:
        for p in PackageSkuItem.objects.filter(oid__in=oids):
            p.status = PSI_STATUS.PREPARE_BOOK
            p.booked_time = None
            p.purchase_order_unikey = None
            p.save()
            stock = SkuStock._objects.get(sku_id=p.sku_id)
            stock.psi_booked_num -= p.num
            stock.psi_prepare_book_num += p.num
            change_fields = ['psi_booked_num', 'psi_prepare_book_num']
            stock.stat_save(change_fields, stat=True, warning=True)
    else:
        for p in PackageSkuItem.objects.filter(oid__in=oids):
            p.status = PSI_STATUS.PREPARE_BOOK
            p.booked_time = None
            p.assign_status = PackageSkuItem.VIRTUAL_ASSIGNED
            p.purchase_order_unikey = None
            p.save()
            stock = SkuStock._objects.get(sku_id=p.sku_id)
            stock.psi_booked_num -= p.num
            stock.psi_prepare_book_num += p.num
            change_fields = ['psi_booked_num', 'psi_prepare_book_num']
            stock.stat_save(change_fields, stat=True, warning=True)
    from shopback.dinghuo.models import OrderList
    ol = OrderList.objects.filter(purchase_order_unikey=self.uni_key).exclude(stage=OrderList.STAGE_DELETED).first()
    print ol
    ol.stage = 0
    ol.save()
    self.sync_order_list()

####这样处理之后,仓库那边要求改仓库地址,这样的话,我还需要不仅把packageorder的地址改了,还要把packageskuitem的地址改了.并且还要把packageskuitem的packageorderpid给设置为空,然后重新merge下分配包裹号.防止
####合单跑到已经发的包裹里面去了

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-id', '--purchase_order_id', action='store', dest='purchase_order_id',
            type=int,
        )

    def handle(self, *args, **options):
        id = options.get('purchase_order_id')
        po = PurchaseOrder.objects.filter(id=id).first()
        reverse_book(po)