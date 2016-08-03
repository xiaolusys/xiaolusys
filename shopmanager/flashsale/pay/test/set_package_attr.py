# coding=utf-8

from flashsale.pay.models import SaleOrder, SaleTrade
from shopback.trades.models import MergeTrade, PackageOrder, PackageSkuItem


# ADD COLUMN `pid` bigint(20) auto_increment NOT NULL PRIMARY KEY,
# ADD COLUMN `is_picking_print`  tinyint(1) NOT NULL DEFAULT 0 AFTER `is_charged`,
# ADD COLUMN `is_express_print`  tinyint(1) NOT NULL DEFAULT 0 AFTER `is_picking_print`,
# ADD COLUMN `is_send_sms`  tinyint(1) NOT NULL DEFAULT 0 AFTER `is_express_print`,
# ADD COLUMN `has_refund`  tinyint(1) NOT NULL DEFAULT 0 AFTER `is_send_sms`,
# ADD COLUMN `seller_id`  bigint NULL DEFAULT 12 AFTER `sys_status`,
# ADD COLUMN `buyer_nick`  varchar(64) NULL AFTER `buyer_id`,
# ADD COLUMN `type`  varchar(32) NOT NULL  DEFAULT 'sale' AFTER `ware_by`;
# ADD COLUMN `gift_type`  int(11) NOT NULL DEFAULT 0 AFTER `lg_aging_type`,
# ADD COLUMN `consign_time`  datetime NULL AFTER `remind_time`,
# ADD COLUMN `buyer_message`  text NULL AFTER `post_cost`,
# ADD COLUMN `seller_memo`  text NULL AFTER `buyer_message`,
# ADD COLUMN `sys_memo`  text NULL AFTER `seller_memo`,
# ADD COLUMN `seller_flag`  int NULL AFTER `sys_memo`;

def set_package_attr(package, sale_trade, merge_trade):
    package.tid = merge_trade.tid
    package.buyer_nick = sale_trade.buyer_nick
    package.seller_id = merge_trade.user_id
    package.seller_nick = merge_trade.user.nick
    package.is_picking_print = merge_trade.is_picking_print
    package.is_express_print = merge_trade.is_express_print
    package.is_send_sms = merge_trade.is_send_sms
    package.has_refund = merge_trade.has_refund
    package.buyer_message = merge_trade.buyer_message
    package.seller_memo = merge_trade.seller_memo
    package.sys_memo = merge_trade.sys_memo
    package.seller_flag = merge_trade.seller_flag
    package.logistics_company_id = merge_trade.logistics_company_id
    package.save()
    return


def set_package_sku_item():
    for s in SaleOrder.objects.filter(refund_status=0).exclude(
        status__in=[SaleOrder.TRADE_NO_CREATE_PAY, SaleOrder.WAIT_BUYER_PAY, SaleOrder.TRADE_FINISHED,
                    SaleOrder.TRADE_CLOSED, SaleOrder.TRADE_CLOSED_BY_SYS]):
        s.save()
    # for sale_order in SaleOrder.objects.exclude(status__in=[SaleOrder.TRADE_NO_CREATE_PAY,
    #                                                         SaleOrder.WAIT_BUYER_PAY, SaleOrder.TRADE_FINISHED,
    #                                                         SaleOrder.TRADE_CLOSED,
    #                                                         SaleOrder.TRADE_CLOSED_BY_SYS], refund_status=0):
    #     sale_order.save()


def task_saleorder_update_package_sku_item(sale_order):
    from shopback.trades.models import PackageSkuItem
    from shopback.items.models import ProductSku
    items = PackageSkuItem.objects.filter(sale_order_id=sale_order.id)
    if items.count() <= 0:
        if not sale_order.is_pending():
            # we create PackageSkuItem only if sale_order is 'pending'.
            return
        ware_by = ProductSku.objects.get(id=sale_order.sku_id).ware_by
        sku_item = PackageSkuItem(sale_order_id=sale_order.id, ware_by=ware_by)
    else:
        sku_item = items[0]
        if sku_item.is_finished():
            # if it's finished, that means the package is sent out,
            # then we dont do further updates, simply return.
            return

    # Now the package has not been sent out yet.

    if sale_order.is_canceled() or sale_order.is_confirmed():
        # If saleorder is canceled or confirmed before we send out package, we
        # then dont want to send out the package, simply cancel. Note: if the
        # order is confirmed, we assume the customer does not want the package
        # to be sent to him (most likely because it's not necessary, maybe she/he
        # bought a virtual product).
        sku_item.assign_status = PackageSkuItem.CANCELED

    attrs = ['num', 'package_order_id', 'title', 'price', 'sku_id', 'num', 'total_fee',
             'payment', 'discount_fee', 'refund_status', 'pay_time', 'status']
    for attr in attrs:
        if hasattr(sale_order, attr):
            val = getattr(sale_order, attr)
            setattr(sku_item, attr, val)

    sku_item.save()


# sku_order = SaleOrder.objects.filter(package_order_id=package.id)[0]
# sale_trade = SaleTrade.objects.get(id=sku_order.sale_trade_id)
def set_pacakges_attr():
    for package in PackageOrder.objects.all():
        sale_trade = SaleTrade.objects.filter(buyer_id=package.buyer_id, user_address_id=package.user_address_id)[0]
        merge_trades = sale_trade.get_merge_trades()
        if merge_trades:
            merge_trade = merge_trades[0]
            set_package_attr(package, sale_trade, merge_trade)
            print str(package.id) + '|successs'
        else:
            print str(package.id) + '|no merge_trades'


# def set_package_order():
#     for merge_trade in MergeTrade.objects.filter(status=):
#
#     return
from django.utils.datastructures import SortedDict
# def set_package_merge_order_id():
#     for package in PackageOrder.objects.filter(merge_trade_id=None):
#         trades = set([])
#         for sale_order in SaleOrder.objects.filter(package_order_id=package.id):
#             trades.add(sale_order.sale_trade)
#
#         for item in package.sku_items:PackageOrder.gen_new_package_id
#             tid = item.sale_order.sale_trade.tid
#             MergeTrade.objects()
import datetime
from shopback.trades.models import PackageOrder, PackageSkuItem

oid_dict = {}
# 注意防重  运单号相同情况的处理。
for item in PackageSkuItem.objects.filter(oids__in=oid_dict.keys()):
    if not item.package_order:
        item.assign_status = 2
        trade = item.sale_trade
        package_order_id = PackageOrder.gen_new_package_id(trade.buyer_id, trade.user_address_id, item.productsku.ware_by)
        package = PackageOrder.objects.filter(id=package_order_id).first()
        if not package:
            package = PackageOrder.create(package_order_id, trade, PackageOrder.WAIT_PREPARE_SEND_STATUS,
                                    item)
        else:
            package.sys_status = PackageOrder.WAIT_CUSTOMER_RECEIVE
            package.save()
    elif item.package_order and item.package_order.package_sku_item.count()==1:
        if item.package_order.is_sent():
            item.package_order.out_sid = oid_dict.get(item.id)
            item.package_order.save()
    elif item.package_order and item.package_order.package_sku_item.count()>1:
        if item.package_order.is_sent():
            package = PackageOrder.objects.filter(id__startswith=item.package_order_id[:item.package_order_id.rindex('-')]).exclude(sys_status__in=[PackageOrder.WAIT_CUSTOMER_RECEIVE, PackageOrder.FINISHED_STATUS]).first()
            if package:
                if package.package_sku_items.exclude(id=item.id).exists():
                    next_package_id = package.id[:package.id.rindex('-')+1] + str(int(package.id[package.id.rindex('-')+1:]) + 1)
                    new_package = PackageOrder.create(id, item.sale_trade)
                    package.package_sku_items.exclude(id=item.id).update(package_order_id=next_package_id)
                item.package_order_id = package.id
                package.sys_status = PackageOrder.WAIT_CUSTOMER_RECEIVE
                package.status = 'WAIT_BUYER_CONFIRM_GOODS'
                package.out_sid = oid_dict.get(item.oid)
                package.weight_time = datetime.datetime.now()
                package.save()
            else:
                package = item.package_order
                trade = item.sale_trade
                now_package_id = PackageOrder.gen_new_package_id(trade.buyer_id, trade.user_address_id, item.productsku.ware_by)
                now_package = PackageOrder.create(now_package_id, item.sale_trade)
                item.package_order_id = now_package.id
                now_package.sys_status = PackageOrder.WAIT_CUSTOMER_RECEIVE
                now_package.status = 'WAIT_BUYER_CONFIRM_GOODS'
                now_package.out_sid = oid_dict.get(item.oid)
                now_package.weight_time = datetime.datetime.now()
                now_package.save()
                item.save()
    else:
        item.clear_order_info()


if __name__=='__main__':
    p = PackageOrder.objects.filter(sys_status=PackageOrder.WAIT_PREPARE_SEND_STATUS).first()
    print p.pid
    p.reset_to_new_create()
    print p.__dict__