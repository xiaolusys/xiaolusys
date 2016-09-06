# -*- encoding:utf-8 -*-
import datetime

from celery.task import task
from django.db import IntegrityError

from flashsale.xiaolumm import constants
from flashsale.xiaolumm.models import XiaoluMama, AwardCarry, OrderCarry, \
    GroupRelationship, MamaMission, MamaMissionRecord

import logging
logger = logging.getLogger(__name__)

@task(max_retries=3, default_retry_delay=60)
def task_push_mission_state_msg_to_weixin_user(mission_record_id):
    try:
        from shopapp.weixin.weixin_push import WeixinPush

        mama_mission = MamaMissionRecord.objects.filter(id=mission_record_id).first()
        base_mission = mama_mission.mission

        wxpush = WeixinPush()
        if mama_mission.is_finished():
            params  = {
                'header': u'女王大人吉祥，本周有一任务已完成，深得阿玛喜欢，重重有赏！',
                'footer': u'小鹿妈妈在截止日期前完成任务可获取额外奖励 (本周业绩越好，下周可获取额外奖励越高).',
                'task_name': u'%s, 赏￥%.2f元' % (base_mission.name, mama_mission.get_award_amount()),
                'task_type': base_mission.get_cat_type_display(),
                'finish_time': mama_mission.finish_time
            }
            wxpush.push_new_mama_task(mama_mission.mama_id, header=params.get('header'),
                                           footer=params.get('footer'), to_url='', params=params)
        else:
            week_end_time = datetime.datetime.strptime('%s-0' % mama_mission.year_week, '%Y-%W-%w')
            mission_kpi_unit = base_mission.kpi_type == MamaMission.KPI_COUNT and u'个' or u'元'
            params = {
                'header': u'女王大人吉祥，阿玛有封密诏请阅目，按诏中所言处事定有重赏!',
                'footer': u'小鹿妈妈在截止日期前完成任务可获取额外奖励 (本周业绩越好，下周可获取额外奖励越高).',
                'task_name': base_mission.name,
                'award_amount': u'￥%.2f' % mama_mission.get_award_amount(),
                'deadline': u'%s' % week_end_time.strftime('%Y-%m-%d'),
                'target_state': u'已完成 %s %s/(目标数 %s %s)' % (
                    mama_mission.get_target_value(), mission_kpi_unit,
                    mama_mission.get_finish_value(), mission_kpi_unit),
                'description': base_mission.desc,
            }
            wxpush.push_mission_state_task(mama_mission.mama_id, header=params.get('header'),
                                      footer=params.get('footer'), to_url=constants.APP_DOWNLOAD_URL, params=params)
    except Exception, exc:
        raise task_push_mission_state_msg_to_weixin_user.retry(exc=exc)


def func_push_award_mission_to_mama(xiaolumama, mission, year_week):

    referal_mama = XiaoluMama.objects.filter(mobile=xiaolumama.referal_from).first()
    mama_group = GroupRelationship.objects.filter(member_mama_id=xiaolumama.id).first()

    year_week_first_day = datetime.datetime.strptime('%s-1'%year_week, '%Y-%W-%w')
    target_value, award_amount = mission.get_mama_target_value(xiaolumama, year_week_first_day)

    mama_mission = MamaMissionRecord(
        mission_id=mission.id,
        mama_id = xiaolumama.id,
        referal_from_mama_id = referal_mama and referal_mama.id or 0,
        group_leader_mama_id = mama_group and mama_group.leader_mama_id or 0 ,
        year_week = year_week, # 2016-32
        finish_value = 0,
        award_amount = award_amount,
        target_value = target_value,
        status = MamaMissionRecord.STAGING
    )
    mama_mission.save()

    # TODO@meron 消息通知妈妈新任务产生
    task_push_mission_state_msg_to_weixin_user.delay(mama_mission.id)



def create_or_update_once_mission(xiaolumama, mission):
    """ 对应一次性任务进行更新 """
    year_week = datetime.datetime.now().strftime('%Y-%W')
    mama_mission = MamaMissionRecord.objects.filter(
        mission=mission, mama_id=xiaolumama.id).first()

    if mission.is_receivable() and not mama_mission:
        func_push_award_mission_to_mama(xiaolumama, mission, year_week)
    elif mission.is_receivable() and not mama_mission.is_finished():
        if mama_mission.year_month == year_week:
            mama_mission.year_month = year_week
            mama_mission.status = MamaMissionRecord.STAGING
            mama_mission.save()
    elif not mission.is_receivable() and not mama_mission.is_finished():
        mama_mission.status = MamaMissionRecord.CLOSE
        mama_mission.save()


def create_or_update_weekly_mission(xiaolumama, mission, year_week):
    """ 对应周任务进行更新 return: -1表示关闭或不存在, 0 正在进行, 1表示已完成"""
    cur_year_week = datetime.datetime.now().strftime('%Y-%W')
    mama_mission = MamaMissionRecord.objects.filter(
        mission=mission, mama_id=xiaolumama.id, year_week=year_week).first()

    if mission.is_receivable() and not mama_mission and year_week == cur_year_week:
        func_push_award_mission_to_mama(xiaolumama, mission, year_week)
        return 0

    elif mama_mission and mama_mission.is_staging() and year_week < cur_year_week:
        mama_mission.status = MamaMissionRecord.CLOSE
        mama_mission.save()
        return -1

    elif mama_mission and mama_mission.is_finished():
        return 1

    return -1


def fresh_mama_weekly_mission_bycat(xiaolumama, cat_type, year_week):

    queryset = MamaMission.objects.filter(
        date_type=MamaMission.TYPE_WEEKLY,
        cat_type=cat_type,
        status=MamaMission.PROGRESS
    ).order_by('target_value')

    for mission in queryset:
        state = create_or_update_weekly_mission(xiaolumama, mission, year_week)
        if state != 1:
            break


@task
def task_create_or_update_mama_mission_state(mama_id):

    # 首单任务检查, 如果未成交则更新year_week未当前时间；
    # 妈妈授课任务, 如果未成交则更新year_week未当前时间；
    # TODO@meron 需要修改之前首单红包十单红包逻辑, 已发放妈妈状态更新
    # TODO@meron 修改根据妈妈授课记录更新对应的任务状态, 已授课妈妈状态更新
    xiaolumama = XiaoluMama.objects.filter(id=mama_id).first()
    once_missions = MamaMission.objects.filter(date_type=MamaMission.TYPE_ONCETIME)
    for mission in once_missions:
        create_or_update_once_mission(xiaolumama, mission)

    year_week = datetime.datetime.now().strftime('%Y-%W')
    # trial mama weekly
    fresh_mama_weekly_mission_bycat(xiaolumama, MamaMission.CAT_TRIAL_MAMA, year_week)

    # referal mama weekly
    fresh_mama_weekly_mission_bycat(xiaolumama, MamaMission.CAT_REFER_MAMA, year_week)

    # mama sale weekly
    fresh_mama_weekly_mission_bycat(xiaolumama, MamaMission.CAT_SALE_MAMA, year_week)

    mama_group = GroupRelationship.objects.filter(leader_mama_id=mama_id).first()
    if mama_group:
        # TODO@meron 新增团队妈妈
        # group mama weekly
        fresh_mama_weekly_mission_bycat(xiaolumama, MamaMission.CAT_GROUP_MAMA, year_week)

        # TODO@meron 个人团队销售激励
        # group mama sale weekly
        fresh_mama_weekly_mission_bycat(xiaolumama, MamaMission.CAT_SALE_GROUP, year_week)

    # 关闭上周未关闭任务
    pre_year_week = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%W')
    staging_missions = MamaMissionRecord.objects.filter(
        mama_id=mama_id, year_week=pre_year_week, status=MamaMissionRecord.STAGING)
    for record in staging_missions:
        create_or_update_weekly_mission(xiaolumama, record.mission, pre_year_week)


@task
def task_update_all_mama_mission_state():

   xiaolumms = XiaoluMama.objects.filter(status=XiaoluMama.EFFECT,
                                         charge_status=XiaoluMama.CHARGED)
   for xiaolumm in xiaolumms:
       task_create_or_update_mama_mission_state.delay(xiaolumm.id)


@task
def task_notify_all_mama_staging_mission():
    """ 消息通知妈妈还有哪些未完成任务 """
    year_week = datetime.datetime.now().strftime('%Y-%W')
    mama_missions = MamaMissionRecord.objects.filter(
        year_week = year_week,
        status = MamaMissionRecord.STAGING
    )
    for mama_mission in mama_missions:
        task_push_mission_state_msg_to_weixin_user.delay(mama_mission.id)


@task(max_retries=3, default_retry_delay=5)
def task_send_mama_weekly_award(mama_id, mission_record_id):
    """ 发放妈妈周激励奖励 """
    # TODO@meron 需要个时间将提成确认
    try:
        xiaolumm = XiaoluMama.objects.filter(id=mama_id).first()
        mama_mission = MamaMissionRecord.objects.filter(
            id=mission_record_id, mama_id=mama_id).first()
        base_mission = mama_mission.mission
        award_name = u'%s(%s)奖励'%(base_mission.name, mama_mission.year_week)

        award_amount = mama_mission.award_amount * 0.01
        uni_key = mama_mission.gen_uni_key()
        AwardCarry.send_award(xiaolumm, award_amount,
                              xiaolumm.weikefu, award_name,
                              uni_key, AwardCarry.STAGING,
                              AwardCarry.AWARD_MAMA_SALE)
        # 通知妈妈任务完成，奖励发放
        task_push_mission_state_msg_to_weixin_user.delay(mission_record_id)

    except Exception, exc:
        raise task_send_mama_weekly_award.retry(exc=exc)


@task(max_retries=3, default_retry_delay=5)
def task_cancel_mama_weekly_award(mama_id, mission_record_id):
    """ 取消周激励提成 """
    try:
        mama_mission = MamaMissionRecord.objects.filter(
            id=mission_record_id, mama_id=mama_id).first()

        uni_key = mama_mission.gen_uni_key()
        award_carry = AwardCarry.objects.filter(uni_key= uni_key).first()
        award_carry.cancel_award()
    except Exception, exc:
        raise task_cancel_mama_weekly_award.retry(exc=exc)


