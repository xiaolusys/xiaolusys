# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

import datetime
from collections import defaultdict

from django.db.models import Max
from flashsale.xiaolumm.models import XiaoluMama, ReferalRelationship, MamaReferalTree, ActiveValue


class Command(BaseCommand):

    def handle(self, *args, **options):

        agg_mama_ids = list(MamaReferalTree.objects.values_list('referal_to_mama_id', flat=True))

        referal_values_list = XiaoluMama.objects.filter(id__in=agg_mama_ids)\
            .values_list('id','last_renew_type')
        referal_type_maps = dict(referal_values_list)

        active_values_list = ActiveValue.objects.filter(mama_id__in=agg_mama_ids) \
            .values('mama_id').annotate(max_date_field=Max('date_field'))
        active_values_maps = dict([(av['mama_id'], av['max_date_field']) for av in active_values_list])

        print 'prepare data ok:', datetime.datetime.now()

        mamareferals = MamaReferalTree.objects.all().only(
            'id', 'referal_to_mama_id', 'is_elite', 'is_vip', 'last_active_time')

        count = 0
        for mf in mamareferals.iterator():
            mf.is_elite = referal_type_maps.get(mf.referal_to_mama_id) == XiaoluMama.ELITE
            mf.is_vip   = referal_type_maps.get(mf.referal_to_mama_id) > XiaoluMama.ELITE
            mf.last_active_time = active_values_maps.get(mf.referal_to_mama_id)
            mf.save(update_fields=['is_elite', 'is_vip', 'last_active_time'])
            count += 1
            if count % 500 == 0:
                print 'count:', count




