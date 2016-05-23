# coding: utf-8

import datetime
import json
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand


from flashsale.dinghuo.models import InBound, InBoundDetail, OrderList, OrderDetail, OrderDetailInBoundDetail
from flashsale.dinghuo.views import InBoundViewSet
from shopback.items.models import ProductSku
from shopback.items.models_stats import ProductSkuStats

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--delete',  dest='is_del', action='store_true', default=False),
        make_option('-i', '--init', dest='is_init', action='store_true', default=False),
        make_option('-s', '--stats', dest='is_stats', action='store_true', default=False),
        make_option('-o', '--orderlistids', dest='orderlist_ids', action='store', default=''),
        make_option('-p', '--print', dest='is_print', action='store_true', default=False),
        make_option('-t', '--test', dest='is_test', action='store_true', default=False)
    )

    @classmethod
    def delete_all(cls):
        OrderDetailInBoundDetail.objects.all().delete()
        InBoundDetail.objects.all().delete()
        InBound.objects.all().delete()

    @classmethod
    def test(cls):
        status_mapping = dict(OrderList.ORDER_PRODUCT_STATUS)
        product_ids = set()
        sku_ids = set()
        orderlists_dict = {}
        orderlist_ids = (16713,16748,16831)

        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            buyer_name = '未知'
            if orderlist.buyer_id:
                buyer_name = '%s%s' % (orderlist.buyer.last_name,
                                       orderlist.buyer.first_name)
                buyer_name = buyer_name or orderlist.buyer.username

            orderlists_dict[orderlist.id] = {
                'id': orderlist.id,
                'buyer_name': buyer_name,
                'created': orderlist.created.strftime('%y年%m月%d'),
                'status': status_mapping.get(orderlist.status) or '未知',
                'products': {}
            }


        for orderdetail in OrderDetail.objects.filter(
                orderlist_id__in=orderlist_ids).order_by('id'):

            orderlist_dict = orderlists_dict[orderdetail.orderlist_id]
            product_id = int(orderdetail.product_id)
            sku_id = int(orderdetail.chichu_id)
            product_ids.add(product_id)
            sku_ids.add(sku_id)

            products_dict = orderlist_dict['products']
            skus_dict = products_dict.setdefault(product_id, {})

            skus_dict[sku_id] = {
                'buy_quantity': orderdetail.buy_quantity,
                'plan_quantity': orderdetail.buy_quantity - min(
                    orderdetail.arrival_quantity, orderdetail.buy_quantity),
                'orderdetail_id': orderdetail.id
            }
        print orderlists_dict[16748]['products'][40243].keys()

        inbound_skus_dict = {
            162255: {'arrival_quantity': 1},
            162258: {'arrival_quantity': 1},
            162262: {'arrival_quantity': 1},
            162263: {'arrival_quantity': 5},
            162264: {'arrival_quantity': 10}
        }
        allocate_dict =  InBoundViewSet._find_allocate_dict(inbound_skus_dict, orderlist_ids, 16831, '')
        for orderdetail in OrderDetail.objects.filter(id__in=allocate_dict.keys()):
            print orderdetail.chichu_id, orderdetail.id, allocate_dict[orderdetail.id]


    @classmethod
    def init(cls):
        for orderlist in OrderList.objects.exclude(status__in=[OrderList.COMPLETED, OrderList.ZUOFEI, OrderList.CLOSED]):
            orderdetail_dicts = []
            for orderdetail in orderlist.order_list.all().order_by('id'):
                if orderdetail.arrival_quantity == 0 and orderdetail.inferior_quantity == 0:
                    continue
                sku = ProductSku.objects.get(id=orderdetail.chichu_id)
                orderdetail_dicts.append({
                    'id': orderdetail.id,
                    'product_id': sku.product.id,
                    'sku_id': sku.id,
                    'product_name': sku.product.name,
                    'outer_id': sku.product.outer_id,
                    'properties_name': sku.properties_name or sku.properties_alias,
                    'arrival_quantity': orderdetail.arrival_quantity,
                    'inferior_quantity': orderdetail.inferior_quantity
                })
            if orderdetail_dicts:
                inbound = InBound(
                    supplier=orderlist.supplier,
                    creator_id=1,
                    express_no=orderlist.express_no,
                    orderlist_ids=[orderlist.id]
                )
                inbound.save()
                for orderdetail_dict in orderdetail_dicts:
                    inbounddetail = InBoundDetail(
                        inbound=inbound,
                        product_id=orderdetail_dict['product_id'],
                        sku_id=orderdetail_dict['sku_id'],
                        product_name=orderdetail_dict['product_name'],
                        properties_name=orderdetail_dict['properties_name'],
                        arrival_quantity=orderdetail_dict['arrival_quantity'],
                        inferior_quantity=orderdetail_dict['inferior_quantity'],
                        status=InBoundDetail.NORMAL
                    )
                    inbounddetail.save()

                    record = OrderDetailInBoundDetail(
                        orderdetail_id=orderdetail_dict['id'],
                        inbounddetail=inbounddetail,
                        arrival_quantity=orderdetail_dict['arrival_quantity'],
                        inferior_quantity=orderdetail_dict['inferior_quantity']
                    )
                    record.save()

    @classmethod
    def prepare_dumpdata_command(cls, orderlist_ids):
        fixture_dir = '~/workspace/xlmm/flashsale/dinghuo/fixtures/'
        tpl = 'python manage.py dumpdata %(model_name)s --pks %(pks)s --indent 4 > %(path)s\n'

        inbound_ids = set()
        inbounddetail_ids = set()
        sku_ids = set()
        orderdetail_ids = []
        record_ids = []
        user_ids = set()

        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            user_ids.add(orderlist.buyer_id)

        for orderdetail in OrderDetail.objects.filter(orderlist_id__in=orderlist_ids):
            sku_ids.add(int(orderdetail.chichu_id))
            orderdetail_ids.append(orderdetail.id)

            for record in orderdetail.records.filter(status=OrderDetailInBoundDetail.NORMAL):
                record_ids.append(record.id)
                inbounddetail_ids.add(record.inbounddetail.id)
                inbound_ids.add(record.inbounddetail.inbound_id)

        for inbound in InBound.objects.filter(id__in=list(inbound_ids)):
            user_ids.add(inbound.creator_id)

        product_ids = set()
        for sku in ProductSku.objects.filter(id__in=list(sku_ids)):
            sku.quantity = ProductSkuStats.objects.get(sku_id=sku.id).realtime_quantity
            sku.save()
            product_ids.add(sku.product.id)


        product_ids = [str(x) for x in product_ids]
        sku_ids = [str(x) for x in sku_ids]
        orderlist_ids = [str(x) for x in orderlist_ids]
        orderdetail_ids = [str(x) for x in orderdetail_ids]
        inbound_ids = [str(x) for x in inbound_ids]
        inbounddetail_ids = [str(x) for x in inbounddetail_ids]
        record_ids = [str(x) for x in record_ids]
        user_ids = [str(x) for x in user_ids] + ['684827']

        print 'python manage.py dumpdata categorys.ProductCategory --indent 4 > %s\n' % (fixture_dir + 'test.inbound.productcategory.json')
        print tpl % {'model_name': 'items.Product', 'pks': ','.join(sorted(product_ids)), 'path': fixture_dir + 'test.inbound.product.json'}
        print tpl % {'model_name': 'items.ProductSku', 'pks': ','.join(sorted(sku_ids)), 'path': fixture_dir + 'test.inbound.productsku.json'}
        print tpl % {'model_name': 'dinghuo.OrderList', 'pks': ','.join(sorted(orderlist_ids)), 'path': fixture_dir + 'test.inbound.orderlist.json'}
        print tpl % {'model_name': 'dinghuo.OrderDetail', 'pks': ','.join(sorted(orderdetail_ids)), 'path': fixture_dir + 'test.inbound.orderdetail.json'}
        if inbound_ids:
            print tpl % {'model_name': 'dinghuo.InBound', 'pks': ','.join(sorted(inbound_ids)), 'path': fixture_dir + 'test.inbound.inbound.json'}
        if inbounddetail_ids:
            print tpl % {'model_name': 'dinghuo.InBoundDetail', 'pks': ','.join(sorted(inbounddetail_ids)), 'path': fixture_dir + 'test.inbound.inbounddetail.json'}
        if record_ids:
            print tpl % {'model_name': 'dinghuo.OrderDetailInBoundDetail', 'pks': ','.join(sorted(record_ids)), 'path': fixture_dir + 'test.inbound.record.json'}
        print tpl % {'model_name': 'auth.User', 'pks': ','.join(sorted(user_ids)), 'path': fixture_dir + 'test.inbound.user.json'}

    @classmethod
    def dinghuo_stats(cls):
        suppliers_dict = {}
        for orderlist in OrderList.objects.exclude(status__in=[OrderList.COMPLETED, OrderList.ZUOFEI, OrderList.CLOSED, OrderList.TO_PAY]):
            if not orderlist.supplier:
                continue
            supplier_dict = suppliers_dict.setdefault(orderlist.supplier.id, {
                'id': orderlist.supplier.id,
                'name': orderlist.supplier.supplier_name,
                'orderlist_ids': []
            })
            supplier_dict['orderlist_ids'].append(orderlist.id)

        for supplier_id in sorted(suppliers_dict.keys()):
            cls.supplier_info(suppliers_dict[supplier_id])


    @classmethod
    def supplier_info(cls, supplier_dict):
        orderlist_ids = supplier_dict['orderlist_ids']
        skus_dict = {}
        unclosed_orderlist_ids = set()
        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            for orderdetail in orderlist.order_list.all():
                if orderdetail.arrival_quantity >= orderdetail.buy_quantity:
                    continue
                unclosed_orderlist_ids.add(orderdetail.orderlist_id)
                skus_dict.setdefault(orderdetail.chichu_id, {})[orderdetail.orderlist_id] = orderdetail.buy_quantity - orderdetail.arrival_quantity
        if not skus_dict:
            return False

        flag = all((len(x) == 1 for x in skus_dict.values()))
        if flag:
            return False
        print '%d %s %s' % (supplier_dict['id'], supplier_dict['name'], ','.join(map(str, sorted(supplier_dict['orderlist_ids']))))
        n = 0
        for v in skus_dict.values():
            if len(v) > 1:
                n += 1
        print '重复sku: %d' % n

    @classmethod
    def pretty_print(cls, orderlist_ids):
        skus_dict = {}
        for orderlist in OrderList.objects.filter(id__in=orderlist_ids):
            for orderdetail in orderlist.order_list.all():
                sku = ProductSku.objects.get(id=orderdetail.chichu_id)
                skus_dict.setdefault(orderdetail.chichu_id, []).append({
                    'product_id': sku.product.id,
                    'sku_id': sku.id,
                    'orderlist_id': orderdetail.orderlist_id,
                    'orderdetail_id': orderdetail.id,
                    'buy_quantity': orderdetail.buy_quantity,
                    'arrival_quantity': orderdetail.arrival_quantity,
                    'inferior_quantity': orderdetail.inferior_quantity,
                    'left_quantity': orderdetail.buy_quantity - min(orderdetail.buy_quantity, orderdetail.arrival_quantity)
                })
        print json.dumps(skus_dict)


    def handle(self, *args, **kwargs):
        is_del = kwargs['is_del']
        is_init = kwargs['is_init']
        is_stats = kwargs['is_stats']
        orderlist_ids = filter(lambda x: x.isdigit(), kwargs['orderlist_ids'].split(','))
        is_print = kwargs['is_print']
        is_test = kwargs['is_test']
        if is_del:
            self.delete_all()
        if is_init:
            self.init()
        if orderlist_ids:
            self.prepare_dumpdata_command([int(x) for x in orderlist_ids])
            if is_print:
                self.pretty_print([int(x) for x in orderlist_ids])
        if is_stats:
            self.dinghuo_stats()

        if is_test:
            self.test()
