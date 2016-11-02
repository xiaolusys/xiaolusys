# coding=utf-8
from flashsale.pay.models import SaleOrder, SaleTrade
from shopback.items.models import ProductSku
from flashsale.pay.models_addr import UserAddress
from shopback.trades.models import PackageOrder
TEST = True


def move_assign_to_package_sku_item():
    return


def repair_sku(sku_id):
    psku = ProductSku.objects.get(id=sku_id)
    num = 0
    for sale_order in SaleOrder.objects.filter(sku_id=sku_id, assign_status=1):
        num += sale_order.num
    if num != psku.assign_num:
        if TEST:
            print str(sku_id) + '|quantity:' + str(psku.quantity) + '|assign_num:' + str(psku.assign_num) + '|' + str(num)
        else:
            SaleOrder.objects.filter(sku_id=sku_id,assign_status=1).update(assign_status=0)
            psku.assign_num = 0
            psku.save()
    if not TEST:
        ProductSku.objects.get(id=sku_id).assign_packages()
    return


def get_all_sku_need_repair():
    skus = [s.values()[0] for s in SaleOrder.objects.values('sku_id').filter(assign_status=1).distinct()]
    for sku_id in skus:
        repair_sku(sku_id)
    return


def repair_package_delete():
    for p in PackageOrder.objects.filter(sys_status=PackageOrder.PKG_NEW_CREATED, ware_by=9):
        cnt = int(p.id.split('-')[-1:])
        num = PackageStat.get_package_num(p.stat_id)
        if cnt < num:
            p.sys_status=PackageOrder.DELETE
            print p.id, num
            # p.save()



