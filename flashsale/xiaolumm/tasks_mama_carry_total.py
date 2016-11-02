# -*- encoding:utf-8 -*-
from celery.task import task
from common.taskutils import single_instance_task
from flashsale.xiaolumm.models.carry_total import ActivityMamaCarryTotal
from flashsale.xiaolumm.models.rank import WeekMamaCarryTotal, WeekMamaTeamCarryTotal, WeekRank
from django.conf import settings
import datetime
TIMEOUT = 15 * 60 if not settings.DEBUG else 15

import logging, sys

logger = logging.getLogger('celery.handler')


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


@task()
def task_fortune_update_week_carry_total(mama_id):
    WeekMamaCarryTotal.update_or_create(mama_id)


@task()
def task_fortune_update_activity_carry_total(activity, mama_id):
    ActivityMamaCarryTotal.update_or_create(activity, mama_id)


@task()
def task_schedule_update_carry_total_ranking():
    logger.warn("task_schedule_update_carry_total_ranking: %s" % (get_cur_info(),))
    # 周一把上周的也重设一次排名
    if datetime.datetime.now().weekday() == 1:
        WeekMamaCarryTotal.reset_rank(WeekRank.last_week_time())
        WeekMamaCarryTotal.reset_duration_rank(WeekRank.last_week_time())
    WeekMamaCarryTotal.reset_rank()
    WeekMamaCarryTotal.reset_rank_duration()


@task()
def task_schedule_update_team_carry_total_ranking():
    logger.warn(" task_schedule_update_carry_total_ranking: %s" % (get_cur_info(),))
    if datetime.datetime.now().weekday() == 1:
        WeekMamaTeamCarryTotal.reset_rank(WeekRank.last_week_time())
        WeekMamaTeamCarryTotal.reset_duration_rank(WeekRank.last_week_time())
    WeekMamaTeamCarryTotal.reset_rank()
    WeekMamaTeamCarryTotal.reset_rank_duration()
