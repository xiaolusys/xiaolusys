# coding=utf-8
import datetime
from django.core.management.base import BaseCommand
from common.utils import update_model_fields
from statistics.models import SaleOrderStatsRecord


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        更新（不能使用保存） 交易统计明细列表 中的选品字段
        """
        from statistics.tasks import get_product

        records = SaleOrderStatsRecord.objects.all()
        print "records count is %s:" % records.count()
        for record in records:
            product = get_product(record.outer_id)
            if product:
                record.sale_product = product.sale_product
                update_model_fields(record, update_fields=['sale_product'])
            else:
                print "record %s product not found" % record.id
