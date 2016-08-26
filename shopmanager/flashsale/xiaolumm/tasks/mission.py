# -*- encoding:utf-8 -*-
import datetime

from celery.task import task
from django.db import IntegrityError

from flashsale.xiaolumm.models import XiaoluMama, GroupRelationship, MamaMission, MamaMissionRecord

import logging
logger = logging.getLogger(__name__)

def func_push_award_mission_to_mama(mama_id, mission_id, year_week):

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


def create_or_update_once_mission(mama_id, mission):
    """ 对应一次性任务进行更新 """
    year_week = datetime.datetime.now().strftime('%Y-%W')
    mama_mission = MamaMissionRecord.objects.filter(
        mission=mission, mama_id=mama_id).first()

    if mission.is_receivable() and not mama_mission:
        func_push_award_mission_to_mama(mama_id, mission.id, year_week)
    elif mission.is_receivable() and not mama_mission.is_finished():
        if mama_mission.year_month == year_week:
            mama_mission.year_month = year_week
            mama_mission.status = MamaMissionRecord.STAGING
            mama_mission.save()
    elif not mission.is_receivable() and not mama_mission.is_finished():
        mama_mission.status = MamaMissionRecord.CLOSE
        mama_mission.save()


def create_or_update_weekly_mission(mama_id, mission, year_week):
    """ 对应周任务进行更新 return: -1表示关闭或不存在, 0 正在进行, 1表示已完成"""
    cur_year_week = datetime.datetime.now().strftime('%Y-%W')
    mama_mission = MamaMissionRecord.objects.filter(
        mission=mission, mama_id=mama_id, year_week=year_week).first()

    if mission.is_receivable() and not mama_mission and year_week == cur_year_week:
        func_push_award_mission_to_mama(mama_id, mission.id, year_week)
        return 0

    elif mama_mission and mama_mission.is_staging() and year_week < cur_year_week:
        mama_mission.status = MamaMissionRecord.CLOSE
        mama_mission.save()
        return -1

    elif mama_mission and mama_mission.is_finished():
        return 1

    return -1


def fresh_mama_weekly_mission_bycat(mama_id, cat_type, year_week):
    queryset = MamaMission.objects.filter(
        date_type=MamaMission.TYPE_WEEKLY,
        cat_type=cat_type,
        status=MamaMission.PROGRESS
    ).order_by('target_value')

    for mission in queryset:
        state = create_or_update_weekly_mission(mama_id, mission, year_week)
        if state != 1:
            break


@task
def task_create_or_update_mama_mission_state(mama_id):

    # 首单任务检查, 如果未成交则更新year_week未当前时间；
    # 妈妈授课任务, 如果未成交则更新year_week未当前时间；
    # TODO@meron 需要修改之前首单红包十单红包逻辑, 已发放妈妈状态更新
    # TODO@meron 修改根据妈妈授课记录更新对应的任务状态, 已授课妈妈状态更新
    once_missions = MamaMission.objects.filter(date_type=MamaMission.TYPE_ONCETIME)
    for mission in once_missions:
        create_or_update_once_mission(mama_id, mission)

    year_week = datetime.datetime.now().strftime('%Y-%W')
    # trial mama weekly
    fresh_mama_weekly_mission_bycat(mama_id, MamaMission.CAT_TRIAL_MAMA, year_week)

    # referal mama weekly
    fresh_mama_weekly_mission_bycat(mama_id, MamaMission.CAT_REFER_MAMA, year_week)

    # TODO@meron 个人团队销售激励

    # 关闭上周未关闭任务
    pre_year_week = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%W')
    staging_missions = MamaMissionRecord.objects.filter(
        mama_id=mama_id, year_week=pre_year_week, status=MamaMissionRecord.STAGING)
    for mission in staging_missions:
        create_or_update_weekly_mission(mama_id, mission, pre_year_week)
    # 检查下级代理妈妈完成新手任务人数,如果达标生成一条奖励记录，, 如果未成交则更新year_week未当前时间；

    # 妈妈销售额本周累计计算，如果达标生成一条奖励记录，并将任务状态更新为已完成，否则本周已过状态变成未完成；


    # 妈妈新推荐一元妈妈计算，如果达标生成一条奖励记录，并将任务状态更新为已完成，否则本周已过状态变成未完成；

    # 妈妈新推荐小鹿妈妈计数，如果达标生成一条奖励记录，并将任务状态更新为已完成，否则本周已过状态变成未完成；

    # 团队妈妈销售额本周累计计算，如果达标生成一条奖励记录，并将任务状态更新为已完成，否则本周已过状态变成未完成；

    # 团队妈妈新推荐小鹿妈妈计数，如果达标生成一条奖励记录，并将任务状态更新为已完成，否则本周已过状态变成未完成；


@task
def task_update_all_mama_mission_state():

   xiaolumms = XiaoluMama.objects.filter(status=XiaoluMama.EFFECT,
                                         charge_status=XiaoluMama.CHARGED)
   for xiaolumm in xiaolumms:
       task_create_or_update_mama_mission_state.delay(xiaolumm.id)


