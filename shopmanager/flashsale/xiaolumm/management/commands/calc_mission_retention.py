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
        start_date = datetime.datetime.strptime('%s-0' % start_week, '%Y-%W-%w').date()
        now_week = datetime.datetime.now().strftime('%Y-%W')
        week_list = []
        while start_week <= now_week:
            week_list.append(start_week)
            start_date += datetime.timedelta(days=7)
            start_week = start_date.strftime('%Y-%W')


        return week_list

    def handle(self, *args, **options):
        """
        达标妈妈活跃度, 一个达标过的妈妈与未达标妈妈的数据对比
        需求待分析
        """
        start_week = options.get('start_week')[0]

        earliest_finish_valuelist = MamaMissionRecord.objects.filter(
            mission__cat_type=MamaMission.CAT_SALE_MAMA,
            # status= MamaMissionRecord.FINISHED,
            finish_time__isnull=False,
            # mama_id=44
        ).values('mama_id').annotate(Min('finish_time')).values_list('mama_id', 'finish_time__min')
        earliest_map = dict(earliest_finish_valuelist)

        week_list = self.get_start_weeklist(start_week)
        mama_data = {}
        base_qs = MamaMissionRecord.objects.filter(
            mission__cat_type=MamaMission.CAT_SALE_MAMA,
            # mama_id=44,
        )
        for year_week in week_list:
            week_start, week_end = week_range(datetime.datetime.strptime('%s-0' % year_week, '%Y-%W-%w'))
            base_week_qs = base_qs.filter(year_week=year_week,
                                          created__range=(week_start, week_end),
                                          finish_value__gt=0)

            mama_week_data = base_week_qs.values_list('mama_id', 'target_value', 'finish_value', 'finish_time')
            for mama_id, target_value, finish_value, finish_time in mama_week_data:
                first_finish_time = earliest_map.get(mama_id) or finish_time
                if not first_finish_time: continue
                if mama_data.has_key(mama_id):
                    mama_data[mama_id].setdefault(
                        year_week, {'mama_id': mama_id,
                                    'target_value':target_value,
                                    'finish_value':finish_value,
                                    'first_finish_time':first_finish_time})
                else:
                    mama_data.setdefault(
                        mama_id,
                        {year_week:{'mama_id': mama_id,
                                    'target_value': target_value,
                                    'finish_value': finish_value,
                                    'first_finish_time':first_finish_time}})

        week_dd= []
        week_len = len(week_list)
        for week in week_list:
            week_dl = map(lambda x: [], range(week_len))
            week_dd.append(week_dl)

        for mama_id, data_dict in mama_data.iteritems():
            for inn_year_week, mm_data in data_dict.iteritems():
                earliest_year_week = mm_data['first_finish_time'].strftime('%Y-%W')
                week_dd[week_list.index(earliest_year_week)][week_list.index(inn_year_week)].append(mm_data)


        def _calc_value(group_data):
            num_a = len(group_data)
            num_b = len([d['finish_value'] for d in group_data if d['finish_value'] >= d['target_value']])
            unfinish_ll = [(d['finish_value'] * 1.0) / d['target_value'] for d in group_data if d['finish_value'] < d['target_value']]
            rate_a = unfinish_ll and sum(unfinish_ll) / len(unfinish_ll) or 0
            return  '/'.join([str(num_a), str(num_b), '%.4f'%rate_a])

        print '\t'.join(['week'] + week_list)

        for index, ddx in enumerate(week_dd):
            ddx_ll = [week_list[index]]+[_calc_value(ddl) for ddl in ddx]
            print '\t'.join(ddx_ll)

        # TODO 根据用户，周标识，组装数据(每周第一次购买的用户)

        # TODO 根据时间坐标算出序列值




