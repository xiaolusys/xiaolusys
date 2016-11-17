# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app
from celery import group

import datetime
from django.db import IntegrityError
from django.conf import settings

from core.utils import week_range
from flashsale.xiaolumm import constants
from flashsale.xiaolumm.models import XiaoluMama, AwardCarry, OrderCarry, \
    GroupRelationship, MamaMission, MamaMissionRecord, get_mama_week_sale_amount

import logging
logger = logging.getLogger(__name__)

@app.task(max_retries=3, default_retry_delay=60)
def task_push_mission_state_msg_to_weixin_user(mission_record_id, state):
    """state: staging,任务未完成状态通知; finished,任务完成奖励通知； confirm,任务奖励确认通知; cancel,任务奖励取消通知;"""
    try:
        from shopapp.weixin.weixin_push import WeixinPush
        mama_mission = MamaMissionRecord.objects.filter(id=mission_record_id).first()
        if not settings.MAMA_MISSION_PUSH_SWITCH and  mama_mission.mama_id > 135:
            return

        base_mission = mama_mission.mission
        wxpush = WeixinPush()
        if state == MamaMissionRecord.STAGING:
            week_end_time = datetime.datetime.strptime('%s-0' % mama_mission.year_week, '%Y-%W-%w')
            mission_kpi_unit = base_mission.kpi_type == MamaMission.KPI_COUNT and u'个' or u'元'
            params = {
                'header': u'女王，您还有一个奖励任务未完成，快到小鹿美美app看看吧！',
                'footer': u'小鹿妈妈在截止日期前完成任务可获取额外奖励 (本周业绩越好，下周可获取额外奖励越高，点击查看奖励规则).',
                'task_name': base_mission.name,
                'award_amount': u'￥%.2f' % mama_mission.get_award_amount(),
                'deadline': u'%s' % week_end_time.strftime('%Y-%m-%d'),
                'target_state': u'已完成 %s %s/(目标数 %s %s)' % (
                    mama_mission.get_finish_value(), mission_kpi_unit,
                    mama_mission.get_target_value(), mission_kpi_unit),
                'description': base_mission.desc,
            }
            wxpush.push_mission_state_task(mama_mission.mama_id, header=params.get('header'),
                                           footer=params.get('footer'), to_url=constants.WEEKLY_AWARD_RULES_URL,
                                           params=params)

        elif state == MamaMissionRecord.FINISHED:
            params  = {
                'header': u'女王，本周有一任务已完成，奖励已生成，请到小鹿美美app任务列表查看吧！',
                'footer': u'小鹿妈妈在截止日期前完成任务可获取额外奖励 (妈妈销售奖励预计收益，需７天后变成确认收益，退款会影响收益到账哦).',
                'task_name': u'%s, 赏￥%.2f元' % (base_mission.name, mama_mission.get_award_amount()),
                'task_type': base_mission.get_cat_type_display(),
                'finish_time': mama_mission.finish_time
            }
            wxpush.push_new_mama_task(mama_mission.mama_id, header=params.get('header'),
                                      footer=params.get('footer'), to_url=constants.WEEKLY_AWARD_RULES_URL, params=params)

        elif state == MamaMissionRecord.CONFIRM:
            params = {
                'header': u'女王，(%s)周任务奖励已到账，请到小鹿美美app任务列表查看吧！' %mama_mission.year_week,
                'footer': u'小鹿妈妈在截止日期前完成任务可获取额外奖励 (本周业绩越好，下周可获取额外奖励越高，点击查看奖励规则).',
                'task_name': u'%s, 赏￥%.2f元' % (base_mission.name, mama_mission.get_award_amount()),
                'task_type': base_mission.get_cat_type_display(),
                'finish_time': mama_mission.finish_time
            }
            wxpush.push_new_mama_task(mama_mission.mama_id, header=params.get('header'),
                                      footer=params.get('footer'), to_url=constants.WEEKLY_AWARD_RULES_URL, params=params)

        elif state == MamaMissionRecord.CANCEL:
            week_end_time = datetime.datetime.strptime('%s-0' % mama_mission.year_week, '%Y-%W-%w')
            mission_kpi_unit = base_mission.kpi_type == MamaMission.KPI_COUNT and u'个' or u'元'
            params = {
                'header': u'女王，您有笔交易退款，导致(%s)周销售任务未达预期奖励取消，请到小鹿美美app任务列表查看吧！'%mama_mission.year_week,
                'footer': u'妈妈销售奖励预计收益，需７天后变成确认收益，退款会影响收益到账哦( 如有疑问请咨询客服热线: 400-823-5355，点击查看奖励规则)',
                'task_name': base_mission.name,
                'award_amount': u'￥%.2f' % mama_mission.get_award_amount(),
                'deadline': u'%s' % week_end_time.strftime('%Y-%m-%d'),
                'target_state': u'已完成 %s %s/(目标数 %s %s)' % (
                    mama_mission.get_finish_value(), mission_kpi_unit,
                    mama_mission.get_target_value(), mission_kpi_unit),
                'description': base_mission.desc,
            }
            wxpush.push_mission_state_task(mama_mission.mama_id, header=params.get('header'),
                                           footer=params.get('footer'), to_url=constants.WEEKLY_AWARD_RULES_URL,
                                           params=params)

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
    # task_push_mission_state_msg_to_weixin_user.delay(mama_mission.id)



def create_or_update_once_mission(xiaolumama, mission):
    """ 对应一次性任务进行更新 """
    year_week = datetime.datetime.now().strftime('%Y-%W')
    mama_id = xiaolumama.id
    if mission.cat_type == mission.CAT_FIRST_ORDER:
        first_orderaward = AwardCarry.objects.filter(
            mama_id=mama_id, carry_type=AwardCarry.AWARD_FIRST_ORDER)\
            .exclude(status=AwardCarry.CANCEL).only('id').first()
        if first_orderaward:
            return
        order_carry = OrderCarry.objects.filter(mama_id=mama_id, carry_type__in=(
            OrderCarry.WAP_ORDER, OrderCarry.APP_ORDER)).first()
        if order_carry:
            return
        if xiaolumama.charge_time < datetime.datetime(2016,7,23):
            return

    if mission.cat_type == mission.CAT_OPEN_COURSE:
        first_orderaward = AwardCarry.objects.filter(
            mama_id=mama_id, carry_type=AwardCarry.AWARD_OPEN_COURSE) \
            .exclude(status=AwardCarry.CANCEL).only('id').first()
        if first_orderaward:
            return

    mama_mission = MamaMissionRecord.objects.filter(
        mission=mission, mama_id=mama_id).first()

    mission_receiveable = mission.is_receivable(mama_id)
    if mission_receiveable and not mama_mission:
        func_push_award_mission_to_mama(xiaolumama, mission, year_week)
    elif mission_receiveable and mama_mission and not mama_mission.is_finished():
        if mama_mission.year_week != year_week:
            mama_mission.year_week = year_week
            mama_mission.status = MamaMissionRecord.STAGING
            mama_mission.save()

            # # 消息通知妈妈一次性任务还未完成
            # task_push_mission_state_msg_to_weixin_user.delay(mama_mission.id)
    elif not mission_receiveable and mama_mission and not mama_mission.is_finished():
        mama_mission.status = MamaMissionRecord.CLOSE
        mama_mission.save()


def create_or_update_weekly_mission(xiaolumama, mission, year_week):
    """ 对应周任务进行更新 return: -1表示关闭或不存在, 0 正在进行, 1表示已完成"""
    cur_year_week = datetime.datetime.now().strftime('%Y-%W')
    mama_id  = xiaolumama.id
    mama_mission = MamaMissionRecord.objects.filter(
        mission=mission, mama_id=mama_id, year_week=year_week).first()

    if mission.is_receivable(mama_id) and not mama_mission and year_week == cur_year_week:
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


@app.task
def task_create_or_update_mama_mission_state(mama_id):
    """
    妈妈周激励任务生成条件:
      1, 连续两周有订单;
    """
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


@app.task
def task_batch_create_or_update_mama_mission_state(params_list):
    """ small batch execute a larget tasks """
    jobs = group([task_create_or_update_mama_mission_state.s(*param) for param in params_list])
    jobs.delay()

@app.task
def task_batch_push_mission_state_msg_to_weixin_user(params_list):
    """ small batch execute a larget tasks """
    jobs = group([task_push_mission_state_msg_to_weixin_user.s(*param) for param in params_list])
    jobs.delay()


@app.task
def task_update_all_mama_mission_state():
    xiaolumms = XiaoluMama.objects.filter(
        status=XiaoluMama.EFFECT,
        charge_status=XiaoluMama.CHARGED,
        last_renew_type__in=(XiaoluMama.HALF, XiaoluMama.FULL)
    )
    xiaolumama_ids = xiaolumms.values_list('id', flat=True)
    batch_number = 500
    for i in range(0, len(xiaolumama_ids), batch_number):
        mama_ids = xiaolumama_ids[i : i + batch_number]
        params = [(mama_id, ) for mama_id in mama_ids]
        task_batch_create_or_update_mama_mission_state.delay(params)


@app.task
def task_notify_all_mama_staging_mission():
    """ 消息通知妈妈还有哪些未完成任务 """
    year_week = datetime.datetime.now().strftime('%Y-%W')
    twelve_hours_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    # 12小时内产生的任务不重复发送消息
    mama_missions = MamaMissionRecord.objects.filter(
        year_week = year_week,
        mission__date_type=MamaMission.TYPE_WEEKLY,
        status = MamaMissionRecord.STAGING,
        created__gte=twelve_hours_ago
    ).order_by('-mission__cat_type')

    logger.info('task_notify_all_mama_staging_mission start: date=%s, count=%s'%(
        datetime.datetime.now(), mama_missions.count()))
    mission_ids = mama_missions.values_list('id', flat=True)

    batch_number = 500
    for i in range(0, len(mission_ids), batch_number):
        mama_ids = mission_ids[i: i + batch_number]
        params = [(mama_id, MamaMissionRecord.STAGING) for mama_id in mama_ids]
        task_batch_push_mission_state_msg_to_weixin_user.delay(params)



@app.task(max_retries=3, default_retry_delay=5)
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
        award_carry = AwardCarry.objects.filter(uni_key=uni_key).first()
        if award_carry and award_carry.is_cancel():
            award_carry.status  = AwardCarry.STAGING
            award_carry.save()
        else:
            AwardCarry.send_award(xiaolumm, award_amount,
                                  xiaolumm.weikefu, award_name,
                                  uni_key, AwardCarry.STAGING,
                                  AwardCarry.AWARD_MAMA_SALE)
        # 通知妈妈任务完成，奖励发放
        task_push_mission_state_msg_to_weixin_user.delay(mission_record_id, MamaMissionRecord.FINISHED)
    except Exception, exc:
        raise task_send_mama_weekly_award.retry(exc=exc)


@app.task(max_retries=3, default_retry_delay=60)
def task_cancel_or_finish_mama_mission_award(mission_record_id):
    try:
        mama_mission = MamaMissionRecord.objects.filter(
            id=mission_record_id).first()

        week_start, week_end = week_range(datetime.datetime.strptime('%s-1'%mama_mission.year_week, '%Y-%W-%w'))
        some_week_finish_value = get_mama_week_sale_amount([mama_mission.mama_id], week_start, week_end)

        mama_mission.update_mission_value(some_week_finish_value)

        if some_week_finish_value >= mama_mission.target_value:
            uni_key = mama_mission.gen_uni_key()
            award_carry = AwardCarry.objects.filter(uni_key=uni_key).first()
            award_carry.confirm_award()

            # 通知妈妈奖励到账
            task_push_mission_state_msg_to_weixin_user.delay(mission_record_id, MamaMissionRecord.CONFIRM)

    except Exception, exc:
        raise task_cancel_or_finish_mama_mission_award.retry(exc=exc)



@app.task(max_retries=3, default_retry_delay=5)
def task_update_all_mama_mission_award_states():
    """　更新一周前妈妈周任务激励佣金 """
    aweek_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    staging_awards = AwardCarry.objects.filter(status=AwardCarry.STAGING,
                                               created__lt=aweek_ago,
                                               uni_key__startswith=MamaMissionRecord.UNI_NAME)
    staging_award_unikeys = staging_awards.values_list('uni_key', flat=True)
    mission_record_ids = [award_unikey.split('-')[-1] for award_unikey in staging_award_unikeys]

    jobs = group([task_cancel_or_finish_mama_mission_award.s(mid) for mid in mission_record_ids])
    jobs.delay()


@app.task(max_retries=3, default_retry_delay=5)
def task_cancel_mama_weekly_award(mama_id, mission_record_id):
    """ 取消周激励提成 """
    try:
        mama_mission = MamaMissionRecord.objects.filter(
            id=mission_record_id, mama_id=mama_id).first()

        uni_key = mama_mission.gen_uni_key()
        award_carry = AwardCarry.objects.filter(uni_key= uni_key).first()
        if award_carry:
            award_carry.cancel_award()
    except Exception, exc:
        raise task_cancel_mama_weekly_award.retry(exc=exc)


