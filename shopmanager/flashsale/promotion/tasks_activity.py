# -*- encoding:utf-8 -*-
import datetime
from celery.task import task
from flashsale.xiaolumm import util_description

import logging

logger = logging.getLogger('celery.handler')

from flashsale.pay.models_user import Customer, BudgetLog, UserBudget
from flashsale.promotion.models_freesample import RedEnvelope, XLSampleApply, AwardWinner, AppDownloadRecord
from utils import get_application

import sys, random


def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name



def gen_cash_value():
    values = [28,28,36,38,46,48,56,58,66,66,68,78,88,88,118,128]
    x = random.choice(values)
    return x


def gen_envelope_type_value_pair(customer_id, event_id):
    records = RedEnvelope.objects.filter(customer_id=customer_id, event_id=event_id, type=1)
    if records.count() >= 9:
        return (0, gen_cash_value())

    if random.random() <= 0.5:
        # cash
        return (0, gen_cash_value())
    else:
        # card
        slots = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        for item in records:
            slots.remove(item.value)
        return (1, random.choice(slots))
    
from flashsale.push import push_activity


@task()
def task_generate_red_envelope(application):
    """
    We generate redenvelope only if the application is activated, that means we
    already know who owns this application, we know the applicant's customer id.
    """

    if not application.is_activated():
        return

    event_id = application.event_id
    customer_id = application.customer_id
    from_customer_id = application.from_customer
    uni_key1 = '%s-%s' % (event_id, customer_id)

    # problem: how could we apply the red-envelope policy here, such that
    # first day people get all cards easier than people join later days??
    #
    # or, simply an easy policy: every envelope has 50% percent chance bing a card.

    # whoever invites my get a red envelope upon activating my application
    if from_customer_id:
        count = RedEnvelope.objects.filter(uni_key=uni_key1).count()
        if count <= 0:
            type, value = gen_envelope_type_value_pair(from_customer_id, event_id)
            envelope1 = RedEnvelope(customer_id=from_customer_id, event_id=event_id, uni_key=uni_key1, type=type,
                                    value=value, friend_img=application.headimgurl, friend_nick=application.nick)
            envelope1.save()
            # 给推荐人发送红包的发放推送
            push_activity.activity_red_packet_release_push(from_customer_id)

    # when activating my application, i get one red envelope (with type 'card')
    type = 1  # card
    uni_key2 = 'self-' + uni_key1
    count = RedEnvelope.objects.filter(uni_key=uni_key2).count()
    if count <= 0:
        #value = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        value = 1 # give the first card as default
        envelope2 = RedEnvelope(customer_id=customer_id, event_id=event_id, uni_key=uni_key2, type=type,
                                value=value, friend_img=application.headimgurl, friend_nick=application.nick)
        envelope2.save()
        # 推送发红消息给customer
        push_activity.activity_red_packet_release_push(customer_id)


@task()
def task_activate_application(event_id, customer, imei):
    unionid, mobile = customer.unionid, customer.mobile
    if not unionid or not mobile:
        # user must have both unionid and mobile to activate
        return 
    application = get_application(event_id, unionid, mobile)

    if application and not application.is_activated():
        application.status = XLSampleApply.ACTIVED
        application.customer_id = customer.id
        application.headimgurl = customer.thumbnail
        application.user_openid = customer.openid
        application.user_unionid = unionid
        if imei:
            application.event_imei = str(event_id) + "_" + imei
        application.nick = customer.nick
        application.save()


@task()
def task_envelope_create_budgetlog(envelope):
    budget_logs = BudgetLog.objects.filter(customer_id=envelope.customer_id, referal_id=envelope.uni_key)
    if budget_logs.count() > 0:
        return

    budget_type = BudgetLog.BUDGET_IN
    budget_log_type = BudgetLog.BG_ENVELOPE
    status = BudgetLog.CANCELED  # initially we put the status as "canceled"
    budget_date = datetime.datetime.now().date()

    budget_log = BudgetLog(customer_id=envelope.customer_id, flow_amount=envelope.value, budget_type=budget_type,
                           budget_log_type=budget_log_type, budget_date=budget_date, referal_id=envelope.uni_key,
                           status=status)
    budget_log.save()


@task()
def task_envelope_update_budgetlog(envelope):
    if not envelope.is_cashable():
        return

    budget_logs = BudgetLog.objects.filter(customer_id=envelope.customer_id, referal_id=envelope.uni_key)
    if budget_logs.count() > 0:
        budget_log = budget_logs[0]
        budget_log.status = BudgetLog.CONFIRMED
        budget_log.save()
        # 拆红包推送
        push_activity.activity_open_red_packet_push(envelope.customer_id)


@task()
def task_userinfo_update_application(userinfo):
    nickname = userinfo.get("nickname")
    headimgurl = userinfo.get("headimgurl")
    openid = userinfo.get("openid")
    unionid = userinfo.get("unionid")

    applications = XLSampleApply.objects.filter(user_openid=openid)
    if applications.count() > 0:
        application = applications[0]
        update = False
        if unionid and application.user_unionid != unionid:
            application.user_unionid = unionid
            update = True
        if headimgurl and application.headimgurl != headimgurl:
            application.headimgurl = headimgurl
            update = True
        if nickname and application.nick != nickname:
            application.nick = nickname
            update = True
        if update:
            application.save()


@task()
def task_decide_award_winner(envelope):
    card_num = RedEnvelope.objects.filter(customer_id=envelope.customer_id, type=1, status=1).count()
    if card_num < 9:
        return

    event_id = envelope.event_id
    customer_id = envelope.customer_id

    uni_key = "%s-%s" % (event_id, customer_id)
    winners = AwardWinner.objects.filter(uni_key=uni_key)
    if winners.count() > 0:
        return

    invite_num = XLSampleApply.objects.filter(from_customer=customer_id, event_id=event_id, status=XLSampleApply.ACTIVED).count()
    customer = Customer.objects.get(id=customer_id)
    winner = AwardWinner(customer_id=customer_id, customer_img=customer.thumbnail,
                         customer_nick=customer.nick, event_id=event_id,
                         uni_key=uni_key, invite_num=invite_num)
    winner.save()


def get_appdownloadrecord(unionid, mobile):
    if unionid:
        records = AppDownloadRecord.objects.filter(unionid=unionid)
        if records.count() > 0:
            return records[0]
    if mobile:
        records = AppDownloadRecord.objects.filter(mobile=mobile)
        if records.count() > 0:
            return records[0]
    return None


@task()
def task_sampleapply_update_appdownloadrecord(application):
    """
    We make sure the appdownloadrecord will be created only if we have unionid or mobile.
    
    Note: This creates difficulty for h5's appdownload link working (user should either 
    logged in or input his/her mobile number ... to win coupon)
    """
    if not (application.user_unionid or application.mobile):
        # We dont create downloadrecord if both unionid and mobile are missing.
        return

    if not application.from_customer:
        #自己下载的,不是别人推荐的,那么直接退出
        return

    record = get_appdownloadrecord(application.user_unionid, application.mobile)
    if not record:
        record = AppDownloadRecord(from_customer=application.from_customer, openid=application.user_openid,
                                   unionid=application.user_unionid, mobile=application.mobile)
        record.save()
    else:
        if not record.unionid and application.user_unionid:
            # if the appdownloadrecord only have mobile, it's the chance to update it's unionid.
            record.unionid = application.user_unionid
            record.save()


@task()
def task_appdownloadrecord_update_fans(record):
    """
    All fans logic/relationship starts from here. Any other fans logic should be canceled.
    
    1) Only XiaoluMama can have fans;
    2) If I am a XiaoluMama, I should not be a fan of any other XiaoluMama;
    3) I should not be a fan of myself.
    """

    if not record.is_activated():
        return
    
    customer_unionid = record.unionid
    customer_mobile = record.mobile
    customer = None
    if customer_unionid:
        customers = Customer.objects.filter(unionid=customer_unionid)
        if customers.count() > 0:
            customer = customers[0]
    elif customer_mobile:
        customers = Customer.objects.filter(mobile=customer_mobile)
        if customers.count() > 0:
            customer = customers[0]
    if not customer:
        return
    
    referal_customer_id = record.from_customer
    customers = Customer.objects.filter(id=referal_customer_id)
    if customers.count() <= 0:
        return
    referal_customer = customers[0]

    
    from_mama = referal_customer.getXiaolumm()
    mama_id, mama_customer_id = None, None
    if from_mama:
        mama_id = from_mama.id
        mama_customer_id = from_customer
    else:
        # if my parent is not xiaolumama, then find out indirect xiaolumama
        fan_records = XlmmFans.objects.filter(fans_cusid=referal_customer_id)
        if fan_records.count() <= 0:
            return
        fan_record = fan_records[0]
        mama_id = fan_record.xlmm
        mama_customer_id = fan_record.xlmm_cusid

    fans = XlmmFans.objects.filter(fans_cusid=customer.id)
    if fans.count() > 0:
        return

    if mama_customer_id == customer.id:
        # self canot be self's fan
        return

    logger.warn("task_login_update_fans|mama_id:%s,mama_customer_id:%s,referal_customer_id:%s,fan_customer_id:%s, fan_nick:%s" % (mama_id, mama_customer_id, referal_customer_id, customer.id, customer.nick))
    fan = XlmmFans(xlmm=mama_id, xlmm_cusid=mama_customer_id, refreal_cusid=referal_customer_id, fans_cusid=customer.id,
                   fans_nick=customer.nick, fans_thumbnail=customer.thumbnail)
    fan.save()
    
