# coding=utf-8
from django.core.management.base import BaseCommand

import json
from flashsale.xiaolumm.models import XiaoluMama, MamaMissionRecord, MamaMission
from flashsale.xiaolumm.tasks import task_create_or_update_mama_mission_state

class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('end_mama', nargs='+', type=str)


    def handle(self, *args, **options):

        end_mama = int(options.get('end_mama')[0])
        mamas = XiaoluMama.objects.filter(id__lte=end_mama,
                                  status=XiaoluMama.EFFECT,
                                  charge_status=XiaoluMama.CHARGED)

        for mama_id in mamas.values_list('id', flat=True):
            task_create_or_update_mama_mission_state.delay(mama_id)
