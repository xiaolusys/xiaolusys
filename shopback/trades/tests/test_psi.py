# coding=utf-8
import json
from django.test import TestCase
from django.contrib.auth.models import User as DjUser
from flashsale.coupon.models import UserCoupon, OrderShareCoupon
from flashsale.dinghuo.models import *
from flashsale.pay.models import *
from flashsale.dinghuo.models_purchase import *
from flashsale.forecast.models.forecast import *
from flashsale.finance.models import Bill
from shopback.refunds.models import RefundProduct
from shopback.trades.models import *
from shopback.items.models import *


class TradeNormalTestCase(TestCase):
    """
       常规流程测试
        用户支付／订货／入库／分配／打单／扫描／称重
    """
    fixtures = [
        "test.trade.normal.shopbackuser.json",
        "test.trade.normal.salesupplier.json",
        "test.trade.normal.logisticscompany.json",
        "test.trade.normal.user.json",
        "test.trade.normal.customer.json",
        "test.trade.normal.productcategory.json",
        "test.trade.normal.salecategory.json",
        "test.trade.normal.product.json",
        "test.trade.normal.productsku.json",
        "test.trade.normal.saleorder.json",
        "test.trade.normal.saletrade.json",
        "test.trade.normal.skustock.json",
        "test.trade.normal.saleproduct.json",
    ]

    def setUp(self):
        self.username = '13739234188'
        self.password = '123456'
        self.client.login(username=self.username, password=self.password)
        self.sale_trade_id = 468659
        self.sale_order_id = 521465
        self.sku_id = 280052
        self.user_id = 923802

    def test_normal_process(self):
        """用户支付"""
        stock = SkuStock.get_by_sku(self.sku_id)
        print stock.__dict__
        stock.restat()
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        sale_trade = SaleTrade.objects.get(id=self.sale_trade_id)
        sale_trade.pay_confirm()
        sku = ProductSku.objects.get(id=self.sku_id)
        so = SaleOrder.objects.get(id=self.sale_order_id)
        self.assertEqual(so.status, SaleOrder.WAIT_SELLER_SEND_GOODS)
        self.assertEqual(so.package_sku.pay_time, so.pay_time)
        pa = so.package_sku.get_purchase_arrangement()
        self.assertEqual(pa.status, 1)
        stock = SkuStock.get_by_sku(self.sku_id)
        print stock.__dict__
        self.assertEqual(stock.restat(), [])
        """准备订货"""
        pa.generate_order()
        ol = OrderList.objects.get(purchase_order_unikey=pa.purchase_order_unikey)
        self.assertEqual(ol.check_by_package_skuitem(), [])
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        """订货　审核　付款"""
        ol.set_stage_verify()
        pa = PurchaseArrangement.objects.get(id=pa.id)
        self.assertEqual(pa.initial_book, True)
        self.assertEqual(ol.purchase_order.status, PurchaseOrder.BOOKED)
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        status = Bill.STATUS_DELAY
        pay_method = Bill.SELF_PAY
        plan_amount = ol.order_amount
        bill = Bill.create([ol], Bill.PAY, status, pay_method, plan_amount, 0, ol.supplier,
                               user_id=self.user_id, receive_account='', receive_name='',
                               pay_taobao_link='', transcation_no='', note='')
        ol.set_stage_receive(Bill.PC_COD_TYPE)
        """入库"""
        print 'now inbound_quantity: %d' % SkuStock.get_by_sku(self.sku_id).inbound_quantity
        supplier_id = ol.supplier_id
        inbound = InBound(supplier_id=supplier_id,
                          creator_id=self.user_id,
                          express_no='justtest',
                          forecast_inbound_id=None,
                          ori_orderlist_id=ol.id,
                          memo='')
        inbound.save()
        inbounddetail = InBoundDetail(inbound=inbound,
            product=sku.product,
            sku=sku,
            product_name=sku.product.name,
            outer_id=sku.product.outer_id,
            properties_name=sku.properties_name,
            arrival_quantity=so.num,
            inferior_quantity=0,
            memo='')
        inbounddetail.save()
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        """入库分配"""

        orderdetail = ol.order_list.filter(chichu_id=self.sku_id).first()
        print orderdetail.arrival_quantity
        OrderDetailInBoundDetail.create(orderdetail, inbound, so.num)
        inbound.status = InBound.WAIT_CHECK
        inbound.set_stat()
        inbound.save()
        """质检"""
        ibd = inbound.details.first()
        ibd.finish_check2()
        ibd.save()
        ibd.sync_order_detail()
        inbound.status = InBound.COMPLETED
        inbound.checked = True
        inbound.check_time = datetime.datetime.now()
        inbound.set_stat()
        inbound.save()
        inbound.update_orderlist_arrival_process()
        # InBoundDetail.objects.filter(inbound_id=inbound.id).first().save()
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        """分配"""
        orderdetail = ol.order_list.filter(chichu_id=self.sku_id).first()
        orderdetail.save()
        print orderdetail.arrival_quantity
        print 'now inbound_quantity: %d' % SkuStock.get_by_sku(self.sku_id).inbound_quantity
        """合单"""
        psi = PackageSkuItem.objects.get(oid=so.oid)
        psi.merge()
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        """设置操作员和物流单号"""
        psi = PackageSkuItem.objects.get(oid=so.oid)
        PackageOrder.batch_set_operator([psi.package_order_pid], 'yanhuang')
        po = psi.package_order
        out_sid = '123456789'
        po.set_out_sid(out_sid, False, 'test')
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        """打单扫描称重"""
        po.print_picking()
        user = DjUser.objects.get(id=self.user_id)
        po.scancheck(user)
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        po.scanweight(user)
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        po.finish()
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])


class TradeHasStockTestCase(TestCase):
    """
       常规流程测试
        用户支付／订货／入库／分配／打单／扫描／称重
    """
    fixtures = [
        "test.trade.hasstock.shopbackuser.json",
        "test.trade.hasstock.salesupplier.json",
        "test.trade.hasstock.logisticscompany.json",
        "test.trade.hasstock.user.json",
        "test.trade.hasstock.customer.json",
        "test.trade.hasstock.productcategory.json",
        "test.trade.hasstock.salecategory.json",
        "test.trade.hasstock.product.json",
        "test.trade.hasstock.productsku.json",
        "test.trade.hasstock.skustock.json",
        "test.trade.hasstock.saleorder.json",
        "test.trade.hasstock.saletrade.json",
        "test.trade.hasstock.saleproduct.json",
    ]

    def setUp(self):
        self.username = '13739234188'
        self.password = '123456'
        self.client.login(username=self.username, password=self.password)
        self.sale_trade_id = 468659
        self.sale_order_id = 521465
        self.sku_id = 280052
        self.user_id = 923802

    def test_hasstock_process(self):
        """用户支付"""
        stock = SkuStock.get_by_sku(self.sku_id)
        print stock.__dict__
        stock.restat()
        print stock.__dict__
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        sale_trade = SaleTrade.objects.get(id=self.sale_trade_id)
        sale_trade.pay_confirm()
        sku = ProductSku.objects.get(id=self.sku_id)
        so = SaleOrder.objects.get(id=self.sale_order_id)
        self.assertEqual(so.status, SaleOrder.WAIT_SELLER_SEND_GOODS)
        self.assertEqual(so.package_sku.pay_time, so.pay_time)
        pa = so.package_sku.get_purchase_arrangement()
        stock = SkuStock.get_by_sku(self.sku_id)
        self.assertEqual(stock.restat(), [])
        self.assertEqual(pa, None)
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        """合单"""
        psi = PackageSkuItem.objects.get(oid=so.oid)
        psi.merge()
        self.assertEqual(psi.assign_status, 1)
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        """打单"""
        psi = PackageSkuItem.objects.get(oid=so.oid)
        PackageOrder.batch_set_operator([psi.package_order_pid], 'yanhuang')
        po = psi.package_order
        out_sid = '123456789'
        po.set_out_sid(out_sid, False, 'test')
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        """打单称重"""
        po.print_picking()
        user = DjUser.objects.get(id=self.user_id)
        po.scancheck(user)
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        po.scanweight(user)
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        po.finish()
        self.assertEqual(SkuStock.get_by_sku(self.sku_id).restat(), [])
        print SkuStock.get_by_sku(self.sku_id).__dict__


class PSIThirdSendTestCase(TestCase):
    """
        第三方发货流程测试
        用户支付/订货/导入/
    """
    pass