# coding=utf-8
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import sys, datetime
from django.db import IntegrityError
from django.db.models import Sum, Count, F, Q
from common.utils import update_model_fields

from flashsale.xiaolumm.models.models_fortune import MamaFortune, ActiveValue, OrderCarry, ReferalRelationship, \
    CarryRecord, GroupRelationship, MAMA_FORTUNE_HISTORY_LAST_DAY
from flashsale.xiaolumm.models import CashOut
from flashsale.xiaolumm.models.models_fans import XlmmFans

import logging
logger = logging.getLogger('celery.handler')
service_logger = logging.getLogger('service')


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


@app.task(max_retries=3, default_retry_delay=6)
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


@app.task(max_retries=3, default_retry_delay=6)
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


@app.task(max_retries=3, default_retry_delay=6)
def task_carryrecord_update_mamafortune(mama_id):
    #print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    carrys = CarryRecord.objects.filter(mama_id=mama_id, date_field__gt=MAMA_FORTUNE_HISTORY_LAST_DAY).values(
        'status').annotate(carry=Sum('carry_num'))
    carry_pending, carry_confirmed, carry_cashout = 0, 0, 0
    for entry in carrys:
        if entry["status"] == 1:  # pending
            carry_pending = entry["carry"]
        elif entry["status"] == 2:  # confirmed
            carry_confirmed = entry["carry"]

    fortune = MamaFortune.objects.filter(mama_id=mama_id).first()
    if fortune:
        if fortune.carry_pending != carry_pending or fortune.carry_confirmed != carry_confirmed:
            fortune.carry_pending   = carry_pending
            fortune.carry_confirmed = carry_confirmed
            fortune.save(update_fields=['carry_pending','carry_confirmed'])
    else:
        try:
            create_mamafortune_with_integrity(mama_id, carry_pending=carry_pending, carry_confirmed=carry_confirmed)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune carryrecord | mama_id: %s" % (mama_id))
            raise task_carryrecord_update_mamafortune.retry(exc=exc)


@app.task(max_retries=3, default_retry_delay=6)
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


@app.task(max_retries=3, default_retry_delay=6)
def task_update_mamafortune_invite_num(mama_id):
    from flashsale.xiaolumm.models import XiaoluMama
    
    res = ReferalRelationship.objects.filter(referal_from_mama_id=mama_id).values('referal_type').annotate(num=Count('*'))

    invite_num, invite_trial_num = 0,0
    for entry in res:
        num = entry['num'] or 0
        if entry['referal_type'] < XiaoluMama.ELITE:
            invite_trial_num += num
        else:
            invite_num += num

    invite_all_num = invite_num + invite_trial_num

    mama = MamaFortune.objects.filter(mama_id=mama_id).first()
    if mama:
        MamaFortune.objects.filter(mama_id=mama_id).update(invite_num=invite_num, invite_trial_num=invite_trial_num, invite_all_num=invite_all_num)
    else:
        try:
            create_mamafortune_with_integrity(mama_id, invite_num=invite_num, invite_trial_num=invite_trial_num, invite_all_num=invite_all_num)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune invitenum | mama_id: %s" % (mama_id))
            raise task_update_mamafortune_invite_num.retry(exc=exc)


#@app.task()
#def task_update_mamafortune_invite_trial_num(mama_id):
#    #print "%s, mama_id: %s" % (get_cur_info(), mama_id)
#    from flashsale.xiaolumm.models import PotentialMama
#    records = PotentialMama.objects.filter(referal_mama=mama_id)
#    invite_trial_num = records.count()
#    fortune = MamaFortune.get_by_mamaid(mama_id)
#    fortune.invite_trial_num = invite_trial_num
#    fortune.invite_all_num = invite_trial_num + fortune.invite_num
#    fortune.save(update_fields=['invite_trial_num','invite_all_num','modified'])


@app.task(max_retries=3, default_retry_delay=6)
def task_update_mamafortune_mama_level(relationship):
    #print "%s, mama_id: %s" % (get_cur_info(), mama_id)
    from flashsale.xiaolumm.models import XiaoluMama
    from_mama_id = relationship.referal_from_grandma_id
    
    invite_num = ReferalRelationship.objects.filter(referal_from_mama_id=from_mama_id, referal_type__gte=XiaoluMama.HALF).count()
    group_num = ReferalRelationship.objects.filter(referal_from_grandma_id=from_mama_id, referal_type__gte=XiaoluMama.HALF).exclude(referal_to_mama_id=relationship.referal_to_mama_id).count()
    total = invite_num + group_num + 1

    level = 0
    if invite_num >= 15 or total >= 50:
        level = 1
    if total >= 200:
        level = 2
    if total >= 500:
        level = 3
    if total >= 1000:
        level = 4

    mama = MamaFortune.objects.filter(mama_id=from_mama_id).first()
    if mama:
        if mama.mama_level != level:
            mama.mama_level = level
            update_model_fields(mama, update_fields=['mama_level'])
    else:
        try:
            create_mamafortune_with_integrity(from_mama_id, mama_level=level)
        except IntegrityError as exc:
            logger.warn("IntegrityError - MamaFortune mamalevel | mama_id: %s" % (from_mama_id))
            raise task_update_mamafortune_mama_level.retry(exc=exc)


@app.task(max_retries=3, default_retry_delay=6)
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


@app.task(max_retries=3, default_retry_delay=6)
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


@app.task()
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


@app.task()
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


@app.task()
def task_send_activate_award(potential_mama):
    from flashsale.xiaolumm.models import XiaoluMama
    from flashsale.xiaolumm.models.models_fortune import AwardCarry

    mama_id = potential_mama.referal_mama
    mama = XiaoluMama.objects.filter(id=mama_id).first()
    if not mama:
        return

    award_dict = {
          2: 5,
          5: 10,
         10: 15
    }
    award_desc = {
          2: u'已邀请2位店主,奖5元!',
          5: u'已邀请5位店主,再奖10元!',
         10: u'已邀请10位店主,再奖15元!'
    }

    from flashsale.xiaolumm.models import PotentialMama
    trial_num = PotentialMama.objects.filter(referal_mama=mama_id,created__lt=potential_mama.created).count()
    trial_num += 1

    if trial_num in award_dict:
        award_num = award_dict[trial_num]
        award_desc = award_desc[trial_num]
        uni_key = 'activite_award_%d_%d' % (trial_num, mama.id)
        AwardCarry.send_award(mama, award_num, u'邀请1元妈妈奖励', award_desc, uni_key, status=2, carry_type=7)
    elif trial_num % 5 == 0:
        award_num = 10
        award_desc = u'已邀请%d位店主,再奖10元!' % trial_num
        uni_key = 'activite_award_%d_%d' % (trial_num, mama.id)
        AwardCarry.send_award(mama, award_num, u'邀请1元妈妈奖励', award_desc, uni_key, status=2, carry_type=7)


@app.task(max_retries=3, default_retry_delay=6)
def task_first_order_send_award(mama):
    from flashsale.xiaolumm.models.models_fortune import AwardCarry

    oc = OrderCarry.objects.filter(mama_id=mama.id, created__gte=mama.created).exclude(carry_type=3).exclude(status=0).exclude(status=3).first()
    if not oc:
        return

    uni_key = 'trial_first_order_award_%d' % (mama.id,)
    repeat = AwardCarry.objects.filter(uni_key=uni_key).first()
    if repeat:
        return

    AwardCarry.send_award(mama, 5, u'首单奖励', u'首单奖励,继续加油！', uni_key, status=2, carry_type=5)


@app.task(max_retries=3, default_retry_delay=6)
def task_new_guy_task_complete_send_award(mama):
    """
    发送新手任务奖励: 新妈妈发5元，推荐妈妈发10元
    """
    from flashsale.xiaolumm.models import AwardCarry, XiaoluMama, PotentialMama, ReferalRelationship

    if isinstance(mama.charge_time, datetime.datetime):
        uni_key = 'new_guy_task_complete_award_5_%d' % (mama.id,)
        AwardCarry.send_award(mama, 10, u'新手任务奖励', u'完成新手任务奖励', uni_key, status=2, carry_type=4)  # 确定收益

        referal_mama = None
        rr = ReferalRelationship.objects.filter(referal_to_mama_id=mama.id).first()
        if rr:
            referal_mama = XiaoluMama.objects.filter(id=rr.referal_from_mama_id).first()

        if not referal_mama:
            # 当前妈妈的的潜在关系列表中　第一条记录
            potential = PotentialMama.objects.filter(potential_mama=mama.id).order_by('created').first()
            referal_mama = XiaoluMama.objects.filter(id=potential.referal_mama).first()
        if not referal_mama:
            return
        uni_key = 'new_guy_task_complete_award_10_%d' % mama.id
        customer = mama.get_mama_customer()
        AwardCarry.send_award(referal_mama, 10, u'新手任务奖励', u'推荐妈妈完成新手任务奖励', uni_key,
                              status=2, carry_type=6,
                              contributor_nick=customer.nick,
                              contributor_img=customer.thumbnail,
                              contributor_mama_id=mama.id)  # 确定收益


@app.task(max_retries=3, default_retry_delay=6)
def task_subscribe_weixin_send_award(mama):
    """
    新妈妈第一次关注小鹿美美奖励５元
    奖励规则：
    １、已经关注公众号，再加入妈妈，奖励
    ２、已经是妈妈，第一次关注公众号，奖励，之前关注过的再关注均不奖励
    """
    from flashsale.xiaolumm.models import AwardCarry

    uni_key = 'new_guy_task_subscribe_weixin_award_5_%d' % (mama.id,)
    money = 5  # ５元
    carry_plan_name = u'新手任务奖励'
    carry_description = u'新妈妈关注微信奖励'

    AwardCarry.send_award(mama, money, carry_plan_name, carry_description, uni_key, status=2, carry_type=8)  # 确定收益


def get_app_version_from_user_agent(key, user_agent):
    """
    Help function for task_mama_daily_app_visit_stats
    """
    version = 'unknown'
    tokens = user_agent.split()
    for tok in tokens:
        pair = tok.split('/')
        if pair[0] == key:
            version = pair[1]
    return version

@app.task
def task_mama_daily_app_visit_stats(mama_id, user_agent):
    from flashsale.xiaolumm.models import MamaDailyAppVisit
    from flashsale.xiaolumm.models import XiaoluMama

    mama = XiaoluMama.objects.filter(id=mama_id).first()
    renew_type = 0
    if mama:
        renew_type = mama.last_renew_type


    device_type = MamaDailyAppVisit.DEVICE_UNKNOWN
    ua = user_agent.lower()
    version = ""
    if ua[:7].lower() == 'mozilla':
        device_type = MamaDailyAppVisit.DEVICE_MOZILLA
    elif ua.find('android') >= 0:
        device_type = MamaDailyAppVisit.DEVICE_ANDROID
        version = get_app_version_from_user_agent('xlmmapp',ua)
    elif ua.find('ios') >= 0:
        device_type = MamaDailyAppVisit.DEVICE_IOS
        version = get_app_version_from_user_agent('xlmm',ua)

    date_field = datetime.date.today()
    uni_key = MamaDailyAppVisit.gen_uni_key(mama_id, date_field, device_type)
    #uni_key = '%s-%s' % (mama_id, date_field)

    md = MamaDailyAppVisit.objects.filter(uni_key=uni_key).first()
    if not md:
        try:
            md = MamaDailyAppVisit(mama_id=mama_id,uni_key=uni_key,date_field=date_field,
                                   device_type=device_type,version=version,user_agent=user_agent,
                                   renew_type=renew_type)
            md.save()
        except IntegrityError as exc:
            pass
    else:
        update_fields = ['modified']
        if md.version != version:
            md.device_type = device_type
            md.version = version
            md.user_agent = user_agent
            update_fields.append('device_type')
            update_fields.append('version')
            update_fields.append('user_agent')

        md.num_visits += 1
        update_fields.append('num_visits')
        md.save(update_fields=update_fields)

    service_logger.info({
        'action': 'xlmm_open_app_home',
        'mama_id': mama_id,
        'user_agent': user_agent
    })


@app.task
def task_mama_daily_tab_visit_stats(mama_id, stats_tab):
    from flashsale.xiaolumm.models import MamaDailyTabVisit

    date_field = datetime.date.today()
    uni_key = '%s-%s-%s' % (mama_id, stats_tab, date_field)

    md = MamaDailyTabVisit.objects.filter(uni_key=uni_key).first()
    if not md:
        try:
            md = MamaDailyTabVisit(mama_id=mama_id,uni_key=uni_key,date_field=date_field,stats_tab=stats_tab)
            md.save()
        except IntegrityError as exc:
            pass
    else:
        md.save(update_fields=['modified'])


@app.task
def task_repair_mama_wallet(hour=2):
    # type: (int) -None
    """修复妈妈钱包余额不一致问题定时任务,等修改signal代码后删除 2016-12-30
    """
    # todo: remove this func after replace signal mechanism

    from flashsale.xiaolumm.tasks import task_cashout_update_mamafortune

    lg = logging.getLogger(__name__)

    t = datetime.datetime.now() - datetime.timedelta(hours=hour)

    carrys = CarryRecord.objects.filter(Q(created__gte=t) | Q(modified__gte=t)).values('mama_id')
    cashouts = CashOut.objects.filter(Q(created__gte=t) | Q(modified__gte=t)).values('xlmm')

    lg.info({
        'action': 'mama_period_wallet_repair',
        'time': datetime.datetime.now(),
        'carry_count': carrys.count(),
        'cashout_count': cashouts.count()
    })

    for carry in carrys:
        task_carryrecord_update_mamafortune(carry['mama_id'])

    for cashout in cashouts:
        task_cashout_update_mamafortune(cashout['xlmm'])
