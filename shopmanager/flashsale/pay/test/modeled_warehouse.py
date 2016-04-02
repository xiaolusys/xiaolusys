# coding=utf-8
from flashsale.pay.models import TradeCharge, SaleTrade
from flashsale.pay.tasks import confirmTradeChargeTask
from shopback.trades.models import PackageOrder, MergeTrade, MergeOrder
from datetime import datetime
from shopback import paramconfig as pcfg
from flashsale.pay.models import SaleOrder


def put_order(trade):
    """打单"""
    # 注意打单时录入物流信息等多种信息
    trade.sys_status = pcfg.WAIT_CHECK_BARCODE_STATUS
    trade.status = pcfg.WAIT_SELLER_SEND_GOODS
    trade.reason_code = ''
    trade.operator_id = 42
    trade.out_sid = datetime.now().strftime('lx%Y%m%d%H%M%S')
    trade.logistics_company_id = 200734
    trade.save()
    package = trade.get_package()
    package.sys_status = trade.sys_status
    package.save()
    return


def scan_check(trade):
    """扫描验货"""
    trade.sys_status = pcfg.WAIT_SCAN_WEIGHT_STATUS
    trade.scanner_id = 42
    trade.save()
    package = trade.get_package()
    package.sys_status = trade.sys_status
    package.set_out_sid(trade.out_sid, trade.logistics_company_id)
    package.copy_order_info_from_merge_trade(trade)
    package.save()
    return

# MergeTrade.objects.updateProductStockByTrade(mt)
#
# mt.weight = package_weight
# mt.sys_status = pcfg.FINISHED_STATUS
# mt.weight_time = datetime.datetime.now()
# mt.weighter = request.user.username
# mt.save()
# if mt.type == pcfg.SALE_TYPE:
#     package = mt.get_pacakge()
#     mt.get_sale_orders().update(status=SaleOrder.WAIT_BUYER_CONFIRM_GOODS)
#     package.finish(mt)
#     package.sync_merge_order(mt)

def scan_weight(trade):
    """称重"""
    trade.sys_status = pcfg.FINISHED_STATUS
    trade.weighter_id = 42
    trade.save()
    MergeTrade.objects.updateProductStockByTrade(trade)
    package = trade.get_package()
    package.sys_status = trade.sys_status
    package.status = PackageOrder.PKG_CONFIRM
    trade.get_sale_orders().update(status=SaleOrder.WAIT_BUYER_CONFIRM_GOODS)
    package.finish(trade)
    package.sync_merge_trade(trade)
    package.save()
    return


if __name__ == '__main__':
    s = SaleTrade.objects.get(id=314049)
    m = MergeTrade.objects.get(tid=s.tid)#1199799
    #put_order(m)
    #scan_check(m)
    scan_weight(m)