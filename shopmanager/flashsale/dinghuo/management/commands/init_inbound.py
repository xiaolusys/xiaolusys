# coding: utf-8

import datetime
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from flashsale.dinghuo.models import InBound, InBoundDetail, OrderList, OrderDetailInBoundDetail
from shopback.items.models import ProductSku

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--delete',  dest='is_del', action='store_true', default=False),
        make_option('-i', '--init', dest='is_init', action='store_true', default=False)
    )

    @classmethod
    def delete_all(cls):
        OrderDetailInBoundDetail.objects.all().delete()
        InBoundDetail.objects.all().delete()
        InBound.objects.all().delete()

    @classmethod
    def init(cls):
        for orderlist in OrderList.objects.exclude(status__in=[OrderList.COMPLETED, OrderList.ZUOFEI, OrderList.CLOSED]):
            inbound = InBound(
                supplier=orderlist.supplier,
                creator_id=1,
                express_no=orderlist.express_no,
                orderlist_ids=[orderlist.id]
            )
            inbound.save()

            for orderdetail in orderlist.order_list.all():
                sku = ProductSku.objects.get(id=orderdetail.chichu_id)
                inbounddetail = InBoundDetail(
                    inbound=inbound,
                    product=sku.product,
                    sku=sku,
                    product_name=sku.product.name,
                    outer_id=sku.product.outer_id,
                    properties_name=sku.properties_name or sku.properties_alias,
                    arrival_quantity=orderdetail.arrival_quantity,
                    inferior_quantity=orderdetail.inferior_quantity,
                    status=InBoundDetail.NORMAL
                )
                inbounddetail.save()

                record = OrderDetailInBoundDetail(
                    orderdetail=orderdetail,
                    inbounddetail=inbounddetail,
                    arrival_quantity=orderdetail.arrival_quantity,
                    inferior_quantity=orderdetail.inferior_quantity
                )
                record.save()


    def handle(self, *args, **kwargs):
        is_del = kwargs['is_del']
        is_init = kwargs['is_init']
        print is_init
        print is_del
        if is_del:
            self.delete_all()
        if is_init:
            self.init()
