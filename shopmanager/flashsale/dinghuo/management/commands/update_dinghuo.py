# coding: utf-8
import datetime
from operator import itemgetter
from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from flashsale.dinghuo.models import OrderDetail, OrderList
from shopback.items.models import Product
from supplychain.supplier.models import SaleProduct


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (make_option('-u',
                                                         '--user',
                                                         dest='is_user',
                                                         action='store_true',
                                                         default=False),
                                             make_option('-s',
                                                         '--supplier',
                                                         dest='is_supplier',
                                                         action='store_true',
                                                         default=False))

    def handle(self, *args, **kwargs):
        is_user = kwargs['is_user']
        is_supplier = kwargs['is_supplier']

        if is_user:
            self.update_user()
        else:
            self.update_supplier()

    @classmethod
    def update_user(cls):
        user_mapping = {}
        for user in User.objects.filter(is_staff=True):
            user_mapping[user.username] = user.id
        for orderlist in OrderList.objects.filter():
            user_id = user_mapping.get(orderlist.buyer_name)
            if not user_id:
                continue
            orderlist.buyer_id = user_id
            orderlist.save()

    @classmethod
    def update_supplier(cls):
        orderlist_ids = []
        for orderlist in OrderList.objects.exclude(status__in=[OrderList.ZUOFEI]):
            orderlist_ids.append(orderlist.id)

        orderlists = {}
        product_ids = set()
        for orderdetail in OrderDetail.objects.filter(orderlist_id__in=orderlist_ids):
            product_id = orderdetail.product_id
            product_ids.add(product_id)
            if not (product_id and product_id.isdigit()):
                continue
            product_id = int(product_id)
            product_dict = orderlists.setdefault(orderdetail.orderlist_id, {})
            product_dict[product_id] = product_dict.get(product_id, 0) + 1

        product_to_saleproduct = {}
        saleproduct_ids = set()
        for product in Product.objects.filter(id__in=list(product_ids)):
            saleproduct_ids.add(product.sale_product)
            product_to_saleproduct[product.id] = product.sale_product

        saleproduct_to_supplier = {}
        for saleproduct in SaleProduct.objects.filter(id__in=list(saleproduct_ids)):
            saleproduct_to_supplier[saleproduct.id] = saleproduct.sale_supplier_id

        new_orderlists = {}
        for orderlist_id, product_dict in orderlists.iteritems():
            for product_id, n in product_dict.iteritems():
                saleproduct_id = product_to_saleproduct.get(product_id)
                if not saleproduct_id:
                    continue
                supplier_id = saleproduct_to_supplier.get(saleproduct_id)
                if not supplier_id:
                    continue
                tmp = new_orderlists.setdefault(orderlist_id, {})
                tmp[supplier_id] = tmp.get(supplier_id, 0) + n

        for orderlist_id, supplier_dict in new_orderlists.iteritems():
            supplier_id, _ = max(supplier_dict.items(), key=itemgetter(1))
            OrderList.objects.filter(id=orderlist_id).update(supplier=supplier_id)
            print orderlist_id, supplier_id
