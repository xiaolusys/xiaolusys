# coding=utf-8
from django.core.management.base import BaseCommand

import json
from flashsale.xiaolumm.models import MamaMissionRecord, MamaMission


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('start_week', nargs='+', type=str)

        parser.add_argument('end_week', nargs='+', type=str)


    def handle(self, *args, **options):

        # 妈妈周目标上调，下降，持平数量，及比例
        start_week = options.get('start_week')[0]
        end_week   = options.get('end_week')[0]
        print 'check_mission_trends:', start_week, end_week
        start_week_missions = MamaMissionRecord.objects.filter(
            year_week=start_week,
            mission__cat_type=MamaMission.CAT_SALE_MAMA
        )

        end_week_missions = MamaMissionRecord.objects.filter(
            year_week=end_week,
            mission__cat_type=MamaMission.CAT_SALE_MAMA
        )

        start_week_maps = dict(start_week_missions.values_list('mama_id', 'target_value'))

        params = {
            'start_week_total': start_week_missions.count(),
            'end_week_total': end_week_missions.count(),
            'start_week_finish': start_week_missions.filter(status=MamaMissionRecord.FINISHED).count(),
            'end_week_finish': end_week_missions.filter(status=MamaMissionRecord.FINISHED).count(),
            'target_new_num': 0,
            'target_rise_num': 0,
            'target_eq_num': 0,
            'target_down_num': 0,
        }

        target_down_mama_list = []
        for mama_id, target_value in end_week_missions.values_list('mama_id', 'target_value').order_by('mama_id'):
            start_target_value = start_week_maps.get(mama_id)
            if start_target_value is None:
                params['target_new_num'] += 1
            elif start_target_value < target_value:
                params['target_rise_num'] += 1
            elif start_target_value > target_value:
                params['target_down_num'] += 1
                target_down_mama_list.append(mama_id)
            else:
                params['target_eq_num'] += 1

        print 'mama mission trends:\n', json.dumps(params, indent=2)

        print 'target down mamas:'
        tmp_list = []
        for index, mama_id in enumerate(target_down_mama_list):
            tmp_list.append(str(mama_id))
            if index and index % 10 == 0:
                print ', '.join(tmp_list)
                tmp_list = []
