# coding=utf-8

from flashsale.pay.models import SaleOrder, SaleTrade, refresh_package_sku_item
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
    for sale_order in SaleOrder.objects.exclude(status__in=[SaleOrder.TRADE_NO_CREATE_PAY,
        SaleOrder.WAIT_BUYER_PAY, SaleOrder.TRADE_FINISHED, SaleOrder.TRADE_CLOSED,
        SaleOrder.TRADE_CLOSED_BY_SYS]):
        refresh_package_sku_item(sale_order)

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
            print str(package.id)+'|no merge_trades'


# def set_package_order():
#     for merge_trade in MergeTrade.objects.filter(status=):
#
#     return

def set_package_merge_order_id():
    for package in PackageOrder.objects.filter(merge_trade_id=None):
        trades = set([])
        for sale_order in SaleOrder.objects.filter(package_order_id=package.id):
            trades.add(sale_order.sale_trade)

        for item in package.sku_items:
            tid = item.sale_order.sale_trade.tid
            MergeTrade.objects()

