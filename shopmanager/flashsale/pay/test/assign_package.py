# coding=utf-8
from flashsale.pay.models import SaleOrder, SaleTrade
from shopback.items.models import ProductSku
from flashsale.pay.models_addr import UserAddress
from shopback.trades.models import PackageOrder

def assign_reset(sku_id):
    p = ProductSku.objects.get(id=sku_id)
    p.assign_num = 0
    p.save()

def assign_reset():
    ProductSku.objects.update(assign_num=0)
    SaleOrder.objects.update(assign_status=0,package_order_id=None)
    PackageOrder.objects.all().delete()

def assign_all():
    for sku_dict in SaleOrder.objects.values('sku_id').filter(status=SaleOrder.WAIT_SELLER_SEND_GOODS).distinct():
        sku_id = sku_dict.values()[0]
        if sku_id:
            print '===================================' + sku_id + '============================'
            p = ProductSku.objects.get(id=sku_id)
            p.assign_packages()

def print_out_res():
    # 输出一个地址的所有订单
    # 输出一个人的所有包裹
    # 核对
    #for SaleOrder.objects.values('sku_id').filter(status=SaleOrder.WAIT_SELLER_SEND_GOODS)
    for buyer_id in SaleTrade.objects.values('buyer_id').filter(status=SaleTrade.WAIT_SELLER_SEND_GOODS).distinct():
        buyer_id = buyer_id.values()[0]
        trade = SaleTrade.objects.filter(status=SaleTrade.WAIT_SELLER_SEND_GOODS, buyer_id=buyer_id)[0]
        print '================================================================='
        if trade.user_address_id:
            print str(trade.buyer_id) + ':' + str(trade.user_address_id) + ' ' + str(UserAddress.objects.get(id=trade.user_address_id))
        else:
            print str(trade.buyer_id) + ':'
        print '----------------------------------'
        for trade in SaleTrade.objects.filter(status=SaleTrade.WAIT_SELLER_SEND_GOODS, buyer_id=buyer_id):
            for order in trade.sale_orders.all():
                if order.sku_id:
                    print str(order.id) + '|'+ str(order.sku_id) + '|' + str(order.num) + '|' + str(order.assign_status) +'|' + str(order.package_order_id)
                else:
                    print order.id
        print '-              -              -'
        for p in PackageOrder.objects.filter(buyer_id=trade.buyer_id):
            print 'package_order:' + str(p.id)
            for order in SaleOrder.objects.filter(package_order_id=p.id):
                print str(order.id) + '|'+ str(order.sku_id) + '|' + str(order.num) + '|' + str(order.assign_status)
                psku = ProductSku.objects.get(id=order.sku_id)
                print 'stock: quantity ' + str(psku.quantity) +'| assign_num:' + str(psku.assign_num)


def print_out_package(buyer_id):
    # 输出一个人的所有包裹
    # 核对
    trade = SaleTrade.objects.filter(status=SaleTrade.WAIT_SELLER_SEND_GOODS, buyer_id=buyer_id)[0]
    print '================================================================='
    if trade.user_address_id:
        print str(trade.buyer_id) + ':' + str(trade.user_address_id) + ' ' + str(UserAddress.objects.get(id=trade.user_address_id))
    else:
        print str(trade.buyer_id) + ':'
    print '----------------------------------'
    res1 = {}
    for trade in SaleTrade.objects.filter(status=SaleTrade.WAIT_SELLER_SEND_GOODS, buyer_id=buyer_id):
        for order in trade.sale_orders.all():
            if order.sku_id:
                if order.assign_status:
                    print str(order.id) + '|'+ str(order.sku_id) + '|' + str(order.num) + '|' + str(order.assign_status) +'|' + str(order.package_order_id)
                    res1[order.sku_id] = res1.get(order.sku_id,0) + order.num
            else:
                print order.id
    print '-              -              -'
    res2 = {}
    for p in PackageOrder.objects.filter(buyer_id=trade.buyer_id):
        print 'package_order:' + str(p.id)
        for order in SaleOrder.objects.filter(package_order_id=p.id):
            if order.assign_status:
                print str(order.id) + '|'+ str(order.sku_id) + '|' + str(order.num) + '|' + str(order.assign_status)
                res2[order.sku_id] = res2.get(order.sku_id,0) + order.num
            psku = ProductSku.objects.get(id=order.sku_id)
            #print 'stock: '+ str(order.sku_id)+ '| quantity ' + str(psku.quantity) +'| assign_num:' + str(psku.assign_num)
    if res1!=res2:
        print 'error'

def get_all_buyer():
    res = []
    for buyer_id in SaleTrade.objects.values('buyer_id').filter(status=SaleTrade.WAIT_SELLER_SEND_GOODS).distinct():
        buyer_id = buyer_id.values()[0]
        print buyer_id
        res.append(buyer_id)
    return res

if __name__=='__main__':#
    # print_out_res()
    #assign_reset()
    print_out_package(42)
    # #print_out_res()
    # for buyer_id in get_all_buyer():
    #     print_out_package(buyer_id)
    #assign_all()
    # print_out_res()
    ProductSku.objects.get(id=3737).assign_packages()