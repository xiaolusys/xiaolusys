# -*- encoding:utf-8 -*-

import logging

from celery.task import task
from django.db import IntegrityError
from django.db.models import Sum, Count, F

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models.models_fortune import MamaFortune, ActiveValue, OrderCarry, ReferalRelationship, \
    CarryRecord, GroupRelationship, MAMA_FORTUNE_HISTORY_LAST_DAY
from flashsale.xiaolumm.models import CashOut
from flashsale.xiaolumm.models.models_fans import XlmmFans

import sys, datetime


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


def create_mamafortune_with_integrity(mama_id, **kwargs):
    # try:
    # fortune = MamaFortune(mama_id=mama_id, **kwargs)
    fortune = MamaFortune(mama_id=mama_id)
    for k, v in kwargs.iteritems():
        if hasattr(fortune, k):
            setattr(fortune, k, v)
    fortune.save()
    # except IntegrityError as e:
    # logger.warn("IntegrityError - mama_id: %s, params: %s" % (mama_id, kwargs))
    # The following will very likely cause deadlock, since another
    # thread is creating this record. we decide to just fail it.
    # MamaFortune.objects.filter(mama_id=mama_id).update(**kwargs)


@task(max_retries=3, default_retry_delay=6)
def task_xiaolumama_update_mamafortune(mama_id, cash):
    logger.warn("%s - mama_id: %s, params: %s" % (get_cur_info(), mama_id, cash))
    fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if fortunes.count() > 0:
        fortunes.update(history_confirmed=cash)
        # fortune = fortunes[0]
        # fortune.history_confirmed = cash
        # fortune.save()
    else:
        try:
            create_mamafortune_with_integrity(mama_id, history_confirmed=cash)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune | mama_id: %s, cash: %s" % (mama_id, cash))
            raise task_xiaolumama_update_mamafortune.retry(exc=exc)


CASHOUT_HISTORY_LAST_DAY_TIME = datetime.datetime(2016, 3, 30, 23, 59, 59)


@task(max_retries=3, default_retry_delay=6)
def task_cashout_update_mamafortune(mama_id):
    cashout_sum = CashOut.objects.filter(xlmm=mama_id, approve_time__gt=CASHOUT_HISTORY_LAST_DAY_TIME).values(
        'status').annotate(total=Sum('value'))
    approved_total, pending_total = 0, 0
    for record in cashout_sum:
        if record['status'] == CashOut.APPROVED:
            approved_total = record['total']
        if record['status'] == CashOut.PENDING:
            pending_total = record['total']

    effect_cashout = approved_total + pending_total

    logger.warn("%s - mama_id: %s, effect_cashout: %s|pending:%s,approved:%s" % (
        get_cur_info(), mama_id, effect_cashout, pending_total, approved_total))
    fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if fortunes.count() > 0:
        fortune = fortunes[0]
        if fortune.carry_cashout != effect_cashout:
            fortune.carry_cashout = effect_cashout
            fortune.save(update_fields=['carry_cashout'])
    else:
        try:
            create_mamafortune_with_integrity(mama_id, carry_cashout=effect_cashout)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune cashout | mama_id: %s" % (mama_id))
            raise task_cashout_update_mamafortune.retry(exc=exc)


@task(max_retries=3, default_retry_delay=6)
def task_carryrecord_update_mamafortune(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    carrys = CarryRecord.objects.filter(mama_id=mama_id, date_field__gt=MAMA_FORTUNE_HISTORY_LAST_DAY).values(
        'status').annotate(carry=Sum('carry_num'))
    carry_pending, carry_confirmed, carry_cashout = 0, 0, 0
    for entry in carrys:
        if entry["status"] == 1:  # pending
            carry_pending = entry["carry"]
        elif entry["status"] == 2:  # confirmed
            carry_confirmed = entry["carry"]

    fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if fortunes.count() > 0:
        fortune = fortunes[0]
        if fortune.carry_pending != carry_pending or fortune.carry_confirmed != carry_confirmed:
            fortunes.update(carry_pending=carry_pending, carry_confirmed=carry_confirmed)
            # fortune.carry_pending   = carry_pending
            # fortune.carry_confirmed = carry_confirmed
            # fortune.save()
    else:
        try:
            create_mamafortune_with_integrity(mama_id, carry_pending=carry_pending, carry_confirmed=carry_confirmed)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune carryrecord | mama_id: %s" % (mama_id))
            raise task_carryrecord_update_mamafortune.retry(exc=exc)


@task(max_retries=3, default_retry_delay=6)
def task_activevalue_update_mamafortune(mama_id):
    """
    更新妈妈activevalue
    """
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    today = datetime.datetime.now().date()
    effect_day = today - datetime.timedelta(30)

    values = ActiveValue.objects.filter(mama_id=mama_id, date_field__gt=effect_day, status=2).values(
        'mama_id').annotate(value=Sum('value_num'))
    if values.count() <= 0:
        return

    value_num = values[0]["value"]

    mama_fortunes = MamaFortune.objects.filter(mama_id=mama_id)
    if mama_fortunes.count() > 0:
        mama_fortunes.update(active_value_num=value_num)
    else:
        try:
            create_mamafortune_with_integrity(mama_id, active_value_num=value_num)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune activevalue | mama_id: %s" % (mama_id))
            raise task_activevalue_update_mamafortune.retry(exc=exc)


@task(max_retries=3, default_retry_delay=6)
def task_update_mamafortune_invite_num(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    records = ReferalRelationship.objects.filter(referal_from_mama_id=mama_id)
    invite_num = records.count()

    mamas = MamaFortune.objects.filter(mama_id=mama_id)
    if mamas.count() > 0:
        mama = mamas[0]
        if mama.invite_num != invite_num:
            mamas.update(invite_num=invite_num, invite_all_num=F('invite_trial_num') + invite_num)
            # mama.invite_num=invite_num
            # mama.save()
    else:
        try:
            create_mamafortune_with_integrity(mama_id, invite_num=invite_num)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune invitenum | mama_id: %s" % (mama_id))
            raise task_update_mamafortune_invite_num.retry(exc=exc)


@task()
def task_update_mamafortune_invite_trial_num(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    from flashsale.xiaolumm.models import PotentialMama
    records = PotentialMama.objects.filter(referal_mama=mama_id, is_full_member=False)
    invite_trial_num = records.count()
    fortune = MamaFortune.get_by_mamaid(mama_id)
    fortune.invite_trial_num = invite_trial_num
    fortune.invite_all_num = invite_trial_num + fortune.invite_num
    fortune.save()


@task(max_retries=3, default_retry_delay=6)
def task_update_mamafortune_mama_level(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    records = ReferalRelationship.objects.filter(referal_from_mama_id=mama_id)
    invite_num = records.count()

    groups = GroupRelationship.objects.filter(leader_mama_id=mama_id)
    group_num = groups.count()

    total = invite_num + group_num

    level = 0
    if invite_num >= 15 or total >= 50:
        level = 1
    if total >= 200:
        level = 2
    if total >= 500:
        level = 3
    if total >= 1000:
        level = 4

    mamas = MamaFortune.objects.filter(mama_id=mama_id)
    if mamas.count() > 0:
        mama = mamas[0]
        if mama.mama_level != level:
            mamas.update(mama_level=level)
            # mama.mama_level = level
            # mama.save()
    else:
        try:
            create_mamafortune_with_integrity(mama_id, mama_level=level)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune mamalevel | mama_id: %s" % (mama_id))
            raise task_update_mamafortune_mama_level.retry(exc=exc)


@task(max_retries=3, default_retry_delay=6)
def task_update_mamafortune_fans_num(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    fans = XlmmFans.objects.filter(xlmm=mama_id)
    fans_num = fans.count()

    mamas = MamaFortune.objects.filter(mama_id=mama_id)
    if mamas.count() > 0:
        mamas.update(fans_num=fans_num)
    else:
        try:
            create_mamafortune_with_integrity(mama_id, fans_num=fans_num)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune fansnum | mama_id: %s" % (mama_id))
            raise task_update_mamafortune_fans_num.retry(exc=exc)


@task(max_retries=3, default_retry_delay=6)
def task_update_mamafortune_order_num(mama_id):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    records = OrderCarry.objects.filter(mama_id=mama_id).exclude(status=3).values('contributor_id')
    order_num = records.count()

    mamas = MamaFortune.objects.filter(mama_id=mama_id)
    if mamas.count() > 0:
        mamas.update(order_num=order_num)
    else:
        try:
            create_mamafortune_with_integrity(mama_id, order_num=order_num)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune ordernum | mama_id: %s" % (mama_id))
            raise task_update_mamafortune_order_num.retry(exc=exc)


@task()
def task_update_mamafortune_active_num(mama_id):
    from flashsale.xiaolumm.models import XiaoluMama
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    fortune = MamaFortune.get_by_mamaid(mama_id)
    update_fields = ['active_normal_num', 'active_trial_num', 'active_all_num']
    before_modify_data = {f: getattr(fortune, f) for f in update_fields}
    mama = fortune.xlmm
    mmids = mama.get_invite_normal_mama_ids() + mama.get_invite_potential_mama_ids()

    fortune.active_normal_num = XiaoluMama.objects.filter(id__in=mmids, active=True,
                                                          last_renew_type__in=[365, 183]).count()
    fortune.active_trial_num = XiaoluMama.objects.filter(id__in=mmids, active=True, last_renew_type=15).count()
    fortune.active_all_num = XiaoluMama.objects.filter(id__in=mmids, active=True).count()
    after_modify_data = {f: getattr(fortune, f) for f in update_fields}
    if before_modify_data != after_modify_data:
        fortune.save()


@task()
def task_update_mamafortune_hasale_num(mama_id):
    from flashsale.xiaolumm.models import XiaoluMama
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    fortune = MamaFortune.get_by_mamaid(mama_id)
    mama = fortune.xlmm
    update_fields = ['hasale_normal_num', 'hasale_trial_num', 'hasale_all_num']
    before_modify_data = {f: getattr(fortune, f) for f in update_fields}
    mmids = mama.get_invite_normal_mama_ids() + mama.get_invite_potential_mama_ids()
    fortune.hasale_normal_num = XiaoluMama.objects.filter(id__in=mmids, hasale=True,
                                                          last_renew_type__in=[365, 183]).count()
    fortune.hasale_trial_num = XiaoluMama.objects.filter(id__in=mmids, hasale=True, last_renew_type=15).count()
    fortune.hasale_all_num = XiaoluMama.objects.filter(id__in=mmids, hasale=True).count()
    after_modify_data = {f: getattr(fortune, f) for f in update_fields}
    if before_modify_data != after_modify_data:
        fortune.save()


@task()
def task_send_activite_award(mama_id):
    from flashsale.xiaolumm.models import XiaoluMama
    from flashsale.xiaolumm.models.models_fortune import AwardCarry
    mama = XiaoluMama.objects.filter(id=mama_id).first()
    if not mama:
        return
    fortune = MamaFortune.get_by_mamaid(mama_id)
    data = {
        20: 20,
        50: 60,
        100: 120,
        200: 300
    }
    data_desc = {
        20: u'满20人奖20元',
        50: u'满50人再奖60元',
        100: u'满100人再奖120元',
        200: u'满200人再奖300元'
    }
    for num in data:
        if fortune.active_trial_num >= num:
            uni_key = 'activite_award_%d_%d' % (num, mama.id)
            AwardCarry.send_award(mama, data[num], u'激活奖励', data_desc[num], uni_key)


@task(max_retries=3, default_retry_delay=6)
def task_first_order_send_award(mama):
    from flashsale.xiaolumm.models.models_fortune import AwardCarry
    sum_res = OrderCarry.objects.filter(mama_id=mama.id, created__gte=mama.created).values('status').annotate(
        cnt=Count('id'))
    sum_dict = {item['status']: item['cnt'] for item in sum_res}
    uni_key = 'trial_first_order_award_%d' % (mama.id,)
    repeat = AwardCarry.objects.filter(uni_key=uni_key).first()
    if not sum_dict.get(1) and not sum_dict.get(2):
        if repeat and repeat.status != 3:
            repeat.status = 3
            repeat.save()
    elif sum_dict.get(2):
        if repeat:
            if repeat.status != 2:
                repeat.status = 2
                repeat.save()
        else:
            AwardCarry.send_award(mama, 5, u'首单奖励', u'一元小鹿妈妈首单奖励', uni_key)
    elif sum_dict[1]:
        if repeat:
            if repeat.status != 1:
                repeat.status = 1
                repeat.save()
        else:
            AwardCarry.send_award(mama, 5, u'首单奖励', u'一元小鹿妈妈首单奖励', uni_key)


@task(max_retries=3, default_retry_delay=6)
def task_new_guy_task_complete_send_award(mama):
    """
    发送新手任务奖励: 新妈妈发5元，推荐妈妈发10元
    """
    from flashsale.xiaolumm.models import AwardCarry, XiaoluMama, PotentialMama

    active_time = datetime.datetime(2016, 7, 22, 10, 0, 0)
    if isinstance(mama.charge_time, datetime.datetime) and mama.charge_time >= active_time:
        uni_key = 'new_guy_task_complete_award_5_%d' % (mama.id,)
        AwardCarry.send_award(mama, 5, u'新手任务奖励', u'新手妈妈完成新手任务奖励', uni_key, status=2)  # 确定收益
        referal_mama = XiaoluMama.objects.filter(referal_from=mama.referal_from).first()
        if not referal_mama:
            # 当前妈妈的的潜在关系列表中　第一条记录
            potential = PotentialMama.objects.filter(potential_mama=mama.id).order_by('created').first()
            referal_mama = XiaoluMama.objects.filter(id=potential.referal_mama).first()
        if not referal_mama:
            return
        uni_key = 'new_guy_task_complete_award_10_%d' % (referal_mama.id,)
        customer = referal_mama.get_mama_customer()
        AwardCarry.send_award(referal_mama, 10, u'新手任务奖励', u'新手推荐人完成新手任务推荐人奖励', uni_key,
                              status=2,
                              contributor_nick=customer.nick,
                              contributor_img=customer.thumbnail,
                              contributor_mama_id=mama.id)  # 确定收益
