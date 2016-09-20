# coding=utf-8
from django.core.management.base import BaseCommand

from flashsale.xiaolumm.models import MamaMissionRecord, MamaMission


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('start_week', nargs='+', type=str)


    def handle(self, *args, **options):
        """
        达标妈妈活跃度, 一个达标过的妈妈与未达标妈妈的数据对比
        需求待分析
        """
        start_week = options.get('start_week')[0]

        start_week_missions = MamaMissionRecord.objects.filter(
            year_week=start_week,
            mission__cat_type=MamaMission.CAT_SALE_MAMA
        )
        # TODO@MERON