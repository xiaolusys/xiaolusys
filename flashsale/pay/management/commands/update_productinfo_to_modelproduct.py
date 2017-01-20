# coding=utf-8
__author__ = 'meron'

from django.core.management.base import BaseCommand

import datetime
from django.db.models import Min
from shopback.items.models import Product
from flashsale.pay.models import ProductSku
from flashsale.pay.models import ModelProduct
from supplychain.supplier.models import SaleCategory, SaleProduct

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **options):

        dt = datetime.datetime.now() - datetime.timedelta(days=2)
        model_ids = Product.objects.filter(status=Product.NORMAL,sale_time__gte=dt).values_list('model_id',flat=True).distinct()
        modelproducts = ModelProduct.objects.filter(id__in=model_ids)
        print 'total count=', modelproducts.count()
        cnt = 0
        for mp in modelproducts:
            products = Product.objects.filter(model_id=mp.id,status=Product.NORMAL).order_by('outer_id')
            first_product = products.first()
            if not first_product:
                continue
            saleproduct = SaleProduct.objects.filter(id=first_product.sale_product).first()
            productskus = ProductSku.objects.filter(product__model_id=mp.id, status=ProductSku.NORMAL,
                                                    product__status=Product.NORMAL)
            aggregate_data = productskus.aggregate(min_agent_price=Min('agent_price'),
                                           min_std_sale_price=Min('std_sale_price'))
            mp.lowest_agent_price = aggregate_data.get('min_agent_price')
            mp.lowest_std_sale_price = aggregate_data.get('min_std_sale_price')
            mp.salecategory = saleproduct and saleproduct.sale_category
            mp.saleproduct  = saleproduct
            pdetail = first_product.detail
            mp.is_topic = pdetail and pdetail.is_sale
            mp.rebeta_scheme_id = pdetail and pdetail.rebeta_scheme_id
            mp.order_weight = pdetail and pdetail.order_weight
            mp.shelf_status = first_product and first_product.shelf_status==1 and ModelProduct.ON_SHELF or ModelProduct.OFF_SHELF
            mp.onshelf_time = first_product and first_product.upshelf_time or \
                              first_product.sale_time and datetime.datetime.combine(first_product.sale_time, datetime.time(10, 0,0))
            mp.offshelf_time = first_product and first_product.offshelf_time

            if mp.salecategory_id in (73, ):
                if 'properties' in mp.extras:
                    mp.extras['properties'].pop('wash_instroduce', None)
            mp.save()
            cnt += 1
            if cnt % 500 ==0:
                print 'count=', cnt

    def update_all(self):

        modelproducts = ModelProduct.objects.all()
        print 'total count=', modelproducts.count()
        cnt = 0
        for mp in modelproducts:
            products = Product.objects.filter(model_id=mp.id, status=Product.NORMAL).order_by('outer_id')
            first_product = products.first()
            if not first_product:
                continue
            saleproduct = SaleProduct.objects.filter(id=first_product.sale_product).first()
            productskus = ProductSku.objects.filter(product__model_id=mp.id, status=ProductSku.NORMAL,
                                                    product__status=Product.NORMAL)
            aggregate_data = productskus.aggregate(min_agent_price=Min('agent_price'),
                                                   min_std_sale_price=Min('std_sale_price'))
            mp.lowest_agent_price = aggregate_data.get('min_agent_price')
            mp.lowest_std_sale_price = aggregate_data.get('min_std_sale_price')
            mp.salecategory = saleproduct and saleproduct.sale_category
            mp.saleproduct = saleproduct
            pdetail = first_product.detail
            mp.is_topic = pdetail and pdetail.is_sale
            mp.rebeta_scheme_id = pdetail and pdetail.rebeta_scheme_id
            mp.order_weight = pdetail and pdetail.order_weight
            mp.shelf_status = first_product and first_product.shelf_status == 1 and ModelProduct.ON_SHELF or ModelProduct.OFF_SHELF
            mp.onshelf_time = first_product and first_product.upshelf_time or \
                              first_product.sale_time and datetime.datetime.combine(first_product.sale_time, datetime.time(10, 0,0))
            mp.offshelf_time = first_product and first_product.offshelf_time

            if mp.salecategory_id in (73,):
                if 'properties' in mp.extras:
                    mp.extras['properties'].pop('wash_instroduce', None)
            mp.save()
            cnt += 1
            if cnt % 500 == 0:
                print 'count=', cnt


