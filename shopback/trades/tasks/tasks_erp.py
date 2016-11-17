# encoding=utf8
"""
同步订单到外部ERP系统

应用场景：
每小时优禾订单自动同步到优禾的旺店通系统
"""
from __future__ import absolute_import, unicode_literals
from celery import shared_task as task

import re
import simplejson
from datetime import datetime
from shopback.trades.models import PackageSkuItem, PackageOrder
from shopback.logistics.models import LogisticsCompany
from shopback.trades.models_erp import ErpOrder
from flashsale.pay.models.trade import SaleOrder
from flashsale.dinghuo.models.purchase_order import OrderList
from common.wdt import WangDianTong

SUPPLIER_YOUHE_ID = 29463


def parse_sku_code(supplier_sku_code):
    # SKUCODE,NUM;SKUCODE2,NUM; => [(SKUCODE, NUM),(SKU_CODE, NUM)]
    return [filter(None, re.split(',|，', x)) for x in re.split(';|；', supplier_sku_code) if x]


def task_sync_order_to_erp():
    # 获取订货单
    order_list = OrderList.objects.filter(
        created_by=OrderList.CREATED_BY_MACHINE,
        stage=OrderList.STAGE_DRAFT,
        supplier_id=SUPPLIER_YOUHE_ID
    ).first()

    if not order_list:
        return

    print '==> order_list:', order_list.id

    # 获取优禾订单 PackageSkuItem
    package_sku_items = order_list.package_sku_items
    # now = datetime.now()
    # today = datetime(now.year, now.month, now.day)
    # package_sku_items = PackageSkuItem.objects.filter(
    #     assign_status__in=[PackageSkuItem.NOT_ASSIGNED, PackageSkuItem.ASSIGNED],
    #     created__gte=today
    # )

    wdt_orders = []
    for item in package_sku_items:
        supplier_product = item.get_supplier_product_info()
        supplier = supplier_product['supplier']
        supplier_sku_sale_price = supplier_product['supplier_sku_sale_price']
        supplier_sku_code = supplier_product['supplier_sku_code']
        sale_product = supplier_product['sale_product']

        # 如果供应商不是"优禾""
        if supplier.id != SUPPLIER_YOUHE_ID:
            raise Exception(u'该订单%s:供应商不是优禾 sale_product:%s' % (item.sale_order_id, sale_product))

        if supplier_sku_code.strip() == '':
            raise Exception(u'该订单%s:SKU没有外部编码 sale_product:%s' % (item.sale_order_id, sale_product))

        sale_order = SaleOrder.objects.get(id=item.sale_order_id)
        sale_trade = sale_order.sale_trade

        wdt_order = {
            'OutInFlag': 3,
            'IF_OrderCode': sale_order.oid,  # 外部单据编号
            'WarehouseNO': '001',  # 优禾主仓库
            'Remark': sale_trade.buyer_message,  # 备注
            'GoodsTotal': supplier_sku_sale_price * item.num,  # 货款合计(销售出库时非空)
            'OrderPay': supplier_sku_sale_price * item.num,  # 订单付款金额（含运费）
            'LogisticsPay': sale_trade.post_fee,  # 运费
            'ShopName': '优禾生活小鹿美美店',  # 订单所属店铺名称（出库时非空）
            'BuyerName': sale_trade.receiver_name,  # 收货人姓名
            'BuyerPostCode': sale_trade.receiver_zip,  # 收货人邮编
            'BuyerTel': sale_trade.receiver_mobile,
            'BuyerProvince': sale_trade.receiver_state,
            'BuyerCity': sale_trade.receiver_city,
            'BuyerDistrict': sale_trade.receiver_district,
            'BuyerAdr': sale_trade.receiver_address,
            'PayTime': sale_trade.pay_time.strftime('%Y-%m-%d %H:%M:%S'),
            'TradeTime': sale_trade.created.strftime('%Y-%m-%d %H:%M:%S'),
            'ItemList': {
                'Item': []
            }
        }
        for sku in parse_sku_code(supplier_sku_code):
            if len(sku) == 1:
                sku_code = sku[0]
                sku_num = 1
            elif len(sku) == 2:
                sku_code, sku_num = sku
            else:
                raise Exception(u'该订单%s:SKU外部编码错误 sale_product:%s' % (item.sale_order_id, sale_product))

            wdt_order['ItemList']['Item'].append({
                'Sku_Code': sku_code,
                'Sku_Name': sale_order.title,
                'Sku_Price': supplier_sku_sale_price,
                'Qty': item.num * sku_num,
                'Total': supplier_sku_sale_price * item.num,
                'Item_Remark': '',
            })
        wdt_orders.append({
            'wdt_order': wdt_order,
            'package_sku_item_id': item.id,
            'supplier': supplier
        })

    # 审核订货单
    order_list.verify_order()

    # 同步到优禾
    print '='*20, len(wdt_orders)
    wdt = WangDianTong()
    for item in wdt_orders:
        wdt_order = item['wdt_order']

        is_exists = ErpOrder.objects.filter(sale_order_oid=wdt_order['IF_OrderCode']).first()
        if is_exists:
            print 'order has exist:', wdt_order['IF_OrderCode']
            continue

        erp_order = ErpOrder()
        # wdt_order['Remark'] = '小鹿美美测试不要发货'
        try:
            result = wdt.create_order(wdt_order)
            if result['ResultCode'] == 0:
                status = ErpOrder.SUCCESS
                erp_order_id = result.get('ErpOrderCode')
            else:
                status = ErpOrder.FAIL
                erp_order_id = ''
            result = simplejson.dumps(result)
        except Exception, e:
            result = e
            erp_order_id = ''
            status = ErpOrder.FAIL

        print result, status, erp_order_id

        erp_order.sale_order_oid = wdt_order['IF_OrderCode']
        erp_order.erp_order_id = erp_order_id
        erp_order.package_sku_item_id = item['package_sku_item_id']
        erp_order.supplier_id = item['supplier'].id
        erp_order.supplier_name = item['supplier'].supplier_code
        erp_order.sync_status = status
        erp_order.sync_result = result
        erp_order.save()


def task_sync_erp_deliver():
    """
    定时查询旺店通是否发货
    """

    # 获取未发货订单
    erp_orders = ErpOrder.objects.filter(
        order_status=ErpOrder.CHECK_TRADE,
        sync_status=ErpOrder.SUCCESS
    )

    wdt = WangDianTong()
    for erp_order in erp_orders:
        try:
            result = wdt.query_logistics(erp_order.erp_order_id)
            sale_order_oids = result.get('sale_order_oids', [])
        except Exception:
            continue

        if not result['is_send']:
            continue

        logistics_name = result['logistics_name']
        logistics_code = result['logistics_code']
        post_id = result['post_id']
        delivery_time = datetime.strptime(result['snd_time'], '%Y-%m-%d %H:%M:%S')
        logistics_company = LogisticsCompany.objects.filter(code=logistics_code).first()

        # 发货
        for sale_order_oid in sale_order_oids:
            eo = ErpOrder.objects.filter(sale_order_oid=sale_order_oid).first()
            if not eo:
                continue

            package_sku_item = PackageSkuItem.objects.get(id=eo.package_sku_item_id)
            package_order = PackageOrder.objects.get(id=package_sku_item.package_order_id)
            package_order.finish_third_package(post_id, logistics_company)

            eo.update_logistics(logistics_code, logistics_name, post_id, delivery_time)
