# -*- encoding:utf-8 -*-
from celery.task import task
from common.taskutils import single_instance_task
from flashsale.xiaolumm.models.carry_total import MamaCarryTotal, MamaTeamCarryTotal
from django.conf import settings

TIMEOUT = 15 * 60 if not settings.DEBUG else 15

@task()
def task_carryrecord_update_carrytotal(mama_id):
    MamaCarryTotal.update_ranking(mama_id)


@single_instance_task(timeout=TIMEOUT, prefix='flashsale.xiaolumm.tasks_mama_carry_total.')
def task_update_carry_total_ranking():
    return
    MamaCarryTotal.reset_rank()


@single_instance_task(timeout=TIMEOUT, prefix='flashsale.xiaolumm.tasks_mama_carry_total.')
def task_update_carry_duration_total_ranking():
    return
    MamaCarryTotal.reset_rank_duration()


@single_instance_task(timeout=TIMEOUT, prefix='flashsale.xiaolumm.tasks_mama_carry_total.')
def task_update_team_carry_total(mama_id):
    return
    MamaTeamCarryTotal.get_by_mama_id(mama_id).refresh_data()
