# coding: utf-8
import datetime
from operator import itemgetter
from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Max, Sum

from core.options import log_action, ADDITION, CHANGE
from flashsale.dinghuo.models import OrderDetail, OrderList
from shopback import paramconfig as pcfg
from shopback.items.models import Product, ProductSku
from shopback.trades.models import (MergeOrder, TRADE_TYPE, SYS_TRADE_STATUS)
from supplychain.supplier.models import SaleProduct, SupplierCharge, SaleSupplier


ADMIN_ID = 1

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--delete', dest='is_del', action='store_true', default=False),
    )

    @classmethod
    def delete_orderlist(cls):
        OrderList.objects.filter(created_by=OrderList.CREATED_BY_MACHINE).delete()

    def handle(self, *args, **kwargs):
        is_del = kwargs['is_del']

        if is_del:
            self.delete_orderlist()
        else:
            suppliers = self.get_suppliers()
            for supplier in suppliers:
                self.create_orderlist(supplier)

    @classmethod
    def create_orderlist(cls, supplier):
        now = datetime.datetime.now()
        min_datetime = datetime.datetime(1900, 1, 1)
        supplier_id = supplier['id']

        def _new(supplier, old_orderlist=None):
            orderlist = OrderList(created_by=OrderList.CREATED_BY_MACHINE,
                                  status=OrderList.SUBMITTING,
                                  note=u'-->%s:自动生成订货单' % now.strftime('%m月%d %H:%M'))
            if supplier_id:
                orderlist.supplier_id = supplier_id

            last_pay_time = supplier.get('last_pay_time')
            ware_by = supplier.get('ware_by')
            if last_pay_time and last_pay_time > min_datetime:
                orderlist.last_pay_date = last_pay_time.date()
            if ware_by:
                if ware_by == SaleSupplier.WARE_SH:
                    orderlist.p_district = OrderList.NEAR
                elif ware_by == SaleSupplier.WARE_GZ:
                    orderlist.p_district = OrderList.GUANGDONG
            if old_orderlist:
                if old_orderlist.buyer_id:
                    orderlist.buyer_id = old_orderlist.buyer_id
                if old_orderlist.p_district:
                    orderlist.p_district = old_orderlist.p_district
            orderlist.save()
            log_action(ADMIN_ID, orderlist, ADDITION, '自动生成订货单')

            amount = .0
            for product in supplier['products']:
                for sku in product['skus']:
                    orderdetail = OrderDetail(
                        orderlist_id=orderlist.id,
                        product_id=product['id'],
                        outer_id=product['outer_id'],
                        product_name=product['name'],
                        chichu_id=sku['id'],
                        product_chicun=sku['properties_name'],
                        buy_quantity=abs(sku['effect_quantity']),
                        buy_unitprice=sku['cost'],
                        total_price=abs(sku['effect_quantity'] * sku['cost']))
                    amount += float(orderdetail.buy_unitprice) * orderdetail.buy_quantity
                    orderdetail.save()
            orderlist.order_amount = amount
            orderlist.save()

        def _merge(supplier, old_orderlist):
            old_orderdetails = {}
            for old_orderdetail in old_orderlist.order_list.all():
                old_orderdetails[int(
                    old_orderdetail.chichu_id)] = old_orderdetail

            for product in supplier['products']:
                for sku in product['skus']:
                    if sku['id'] in old_orderdetails:
                        orderdetail = old_orderdetails[sku['id']]
                        orderdetail.buy_quantity += abs(sku['effect_quantity'])
                        orderdetail.total_price += (
                            orderdetail.buy_unitprice or
                            sku['cost']) * abs(sku['effect_quantity'])
                        orderdetail.save()
                    else:
                        orderdetail = OrderDetail(
                            orderlist_id=old_orderlist.id,
                            product_id=product['id'],
                            outer_id=product['outer_id'],
                            product_name=product['name'],
                            chichu_id=sku['id'],
                            product_chicun=sku['properties_name'],
                            buy_quantity=abs(sku['effect_quantity']),
                            buy_unitprice=sku['cost'],
                            total_price=abs(sku['effect_quantity'] * sku[
                                'cost']))
                        orderdetail.save()

            old_orderlist.note += '\n-->%s:自动合并订货单' % now.strftime('%m月%d %H:%M')
            old_orderlist.save()
            log_action(ADMIN_ID, old_orderlist, CHANGE, '自动生成订货单')

        old_orderlist = None
        rows = OrderList.objects.filter(
            supplier_id=supplier_id,
            created_by=OrderList.CREATED_BY_MACHINE) \
            .exclude(status=OrderList.ZUOFEI).order_by('-created')[:1]
        if rows:
            old_orderlist = rows[0]
        if not old_orderlist:
            _new(supplier)
        else:
            if old_orderlist.status != OrderList.SUBMITTING:
                _new(supplier, old_orderlist)
            else:
                _merge(supplier, old_orderlist)

    @classmethod
    def get_suppliers(cls):
        min_datetime = datetime.datetime(1900, 1, 1)
        sale_stats = MergeOrder.objects.select_related('merge_trade').filter(
            merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                                   pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
            merge_trade__sys_status__in=
            [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
             pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
             pcfg.REGULAR_REMAIN_STATUS],
            sys_status=pcfg.IN_EFFECT).values('outer_id',
                                              'outer_sku_id').annotate(
                                                  sale_num=Sum('num'),
                                                  last_pay_time=Max('pay_time'))

        order_products = {}
        for s in sale_stats:
            skus = order_products.setdefault(s['outer_id'], {})
            skus[s['outer_sku_id']] = {
                'sale_quantity': s['sale_num'],
                'last_pay_time': s['last_pay_time']
            }

        sku_ids = set()
        products = {}
        for sku in ProductSku.objects.select_related('product').filter(
                product__outer_id__in=order_products.keys()):
            order_skus = order_products[sku.product.outer_id]
            if sku.outer_id in order_skus:
                sku_ids.add(sku.id)
                skus = products.setdefault(sku.product.id, {})
                sku_dict = {
                    'cost': sku.cost or 0,
                    'sale_quantity': 0,
                    'last_pay_time': min_datetime,
                    'buy_quantity': 0,
                    'arrival_quantity': 0,
                    'inferior_quantity': 0
                }
                sku_dict.update(order_skus.get(sku.outer_id) or {})
                skus[sku.id] = sku_dict

        dinghuo_stats = OrderDetail.objects \
          .exclude(orderlist__status__in=[OrderList.COMPLETED, OrderList.ZUOFEI]) \
          .values('product_id', 'chichu_id') \
          .annotate(buy_quantity=Sum('buy_quantity'), arrival_quantity=Sum('arrival_quantity'),
                        inferior_quantity=Sum('inferior_quantity'))

        for s in dinghuo_stats:
            product_id, sku_id = map(int, (s['product_id'], s['chichu_id']))
            sku_ids.add(sku_id)
            skus = products.setdefault(product_id, {})
            sku = skus.setdefault(sku_id, {'sale_quantity': 0,
                                           'last_pay_time': min_datetime})
            sku.update({
                'buy_quantity': s['buy_quantity'],
                'arrival_quantity': s['arrival_quantity'],
                'inferior_quantity': s['inferior_quantity']
            })

        for sku in ProductSku.objects.filter(pk__in=list(sku_ids)):
            sku_dict = products[sku.product_id][sku.id]
            sku_dict.update({
                'id': sku.id,
                'quantity': sku.quantity,
                'properties_name': sku.properties_name or sku.properties_alias,
                'outer_id': sku.outer_id,
                'cost': sku.cost or 0
            })

        saleproduct_ids = set()
        product_mapping = {}
        for product in Product.objects.filter(pk__in=products.keys()):
            saleproduct_ids.add(product.sale_product)
            product_mapping[product.id] = {
                'id': product.id,
                'name': product.name,
                'pic_path': '%s?imageView2/0/w/120' % product.pic_path.strip(),
                'outer_id': product.outer_id,
                'sale_product_id': product.sale_product
            }

        supplier_mapping = {}
        saleproduct2supplier_mapping = {}
        for saleproduct in SaleProduct.objects.select_related(
                'sale_supplier').filter(pk__in=list(saleproduct_ids)):
            saleproduct2supplier_mapping[
                saleproduct.id] = saleproduct.sale_supplier.id
            if saleproduct.sale_supplier.id not in supplier_mapping:
                supplier_mapping[saleproduct.sale_supplier.id] = {
                    'id': saleproduct.sale_supplier.id,
                    'supplier_name': saleproduct.sale_supplier.supplier_name,
                    'ware_by': saleproduct.sale_supplier.ware_by or 0,
                    'buyer_id': 0,
                    'products': []
                }

        for supplier_charge in SupplierCharge.objects.filter(
                pk__in=supplier_mapping.keys(),
                status=SupplierCharge.EFFECT).order_by('-created'):
            supplier_id = supplier_charge.supplier_id
            buyer_id = supplier_mapping[supplier_id]['buyer_id']
            if not buyer_id:
                supplier_mapping[supplier_id][
                    'buyer_id'] = supplier_charge.employee_id

        suppliers = {}
        for product_id in sorted(products.keys(), reverse=True):
            if product_id not in product_mapping:
                continue
            skus = products[product_id]
            new_product = product_mapping[product_id]
            new_skus = []
            for sku in [skus[k] for k in sorted(skus.keys())]:
                effect_quantity = sku['quantity'] + sku[
                    'buy_quantity'] - min(sku['arrival_quantity'], sku['buy_quantity']) - sku[
                        'sale_quantity']
                if effect_quantity >= 0:
                    continue
                sku['effect_quantity'] = effect_quantity
                new_skus.append(sku)
            if not new_skus:
                continue
            new_product.update({
                'last_pay_time': max(filter(None, map(
                    lambda x: x['last_pay_time'], new_skus)) or [min_datetime]),
                'skus': new_skus
            })
            sale_product_id = new_product['sale_product_id']
            supplier_id = saleproduct2supplier_mapping.get(sale_product_id) or 0
            if supplier_id not in suppliers:
                supplier = supplier_mapping.get(supplier_id) or {
                    'id': supplier_id,
                    'supplier_name': '未知',
                    'ware_by': SaleSupplier.WARE_SH,
                    'buyer_id': 0,
                    'products': []
                }
                suppliers[supplier_id] = supplier
            else:
                supplier = suppliers[supplier_id]
            supplier['products'].append(new_product)

        new_suppliers = []
        for k in sorted(suppliers.keys()):
            supplier = suppliers[k]
            if not supplier.get('products'):
                continue
            last_pay_time = max(map(lambda x: x['last_pay_time'], supplier[
                'products']))
            if last_pay_time == min_datetime:
                last_pay_date = '暂无销售'
            else:
                last_pay_date = last_pay_time.strftime('%Y-%m-%d')
            supplier['last_pay_time'] = last_pay_time
            supplier['last_pay_date'] = last_pay_date
            new_suppliers.append(supplier)
        return new_suppliers
