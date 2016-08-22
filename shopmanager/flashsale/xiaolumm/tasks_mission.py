# -*- encoding:utf-8 -*-
import logging

from celery.task import task
from django.db import IntegrityError

from flashsale.xiaolumm.models import XiaoluMama, GroupRelationship, MamaMission, MamaMissionRecord


@task
def task_push_award_mission_to_mama(mama_id, mission_id, year_week):

    xiaolumm = XiaoluMama.objects.filter(id=mama_id).first()
    referal_mama = XiaoluMama.objects.filter(mobile=xiaolumm.referal_from).first()
    mama_group = GroupRelationship.objects.filter(member_mama_id=mama_id).first()
    mama_mission = MamaMissionRecord(
        mission_id=mission_id,
        mama_id = mama_id,
        referal_from_mama_id = referal_mama and referal_mama.id or 0,
        group_leader_mama_id = mama_group and mama_group.leader_mama_id or 0 ,
        year_week = year_week, # 2016-32
        finish_value = 0,
        status = MamaMissionRecord.STAGING
    )
    mama_mission.save()

