# coding=utf-8
from django.core.management.base import BaseCommand

import datetime
from django.db.models import Min
from core.utils import week_range
from flashsale.xiaolumm.models import MamaMissionRecord, MamaMission


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('start_week', nargs='+', type=str)

    def get_start_weeklist(self, start_week):
        start_date = datetime.datetime.strptime('%s-0' % start_week, '%Y-%W-%w')
        now_dt = datetime.date.today()
        week_list = []
        while start_date < now_dt:
            week_list.append(start_date.strftime('%Y-%W'))
            start_date += datetime.timedelta(days=7)

        return week_list

    def handle(self, *args, **options):
        """
        达标妈妈活跃度, 一个达标过的妈妈与未达标妈妈的数据对比
        需求待分析
        """
        start_week = options.get('start_week')[0]

        earliest_finish_valuelist = MamaMissionRecord.objects.filter(
            mission__cat_type=MamaMission.CAT_SALE_MAMA,
            status= MamaMissionRecord.FINISHED
        ).aggregate(earliest_finish_time=Min('finish_time')).values_list('mama_id', 'min_finish_time')
        earliest_map = dict(earliest_finish_valuelist)

        week_list = self.get_start_weeklist(start_week)
        mama_data = {}

        base_qs = MamaMissionRecord.objects.filter(
            mission__cat_type=MamaMission.CAT_SALE_MAMA
        )
        for year_week in week_list:
            week_start, week_end = week_range(datetime.datetime.strptime('%s-0' % start_week, '%Y-%W-%w'))
            base_week_qs = base_qs.filter(year_week=year_week, finish_time__range=(week_start, week_end))

            mama_week_data = base_week_qs.values_list('mama_id', 'target_value', 'finish_value')
            for mama_id, target_value, finish_value in mama_week_data:
                if mama_data.has_key(mama_id):
                    mama_data[mama_id].set_default(
                        year_week, {'target_value':target_value, 'finish_value':finish_value, 'is_cancel':True})
                else:
                    mama_data.set_default(
                        mama_id, {year_week:{'target_value': target_value, 'finish_value': finish_value}})


        # TODO 根据用户，周标识，组装数据(每周第一次购买的用户)

        # TODO 根据时间坐标算出序列值




