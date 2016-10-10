# -*- encoding:utf-8 -*-

import logging

from celery.task import task

from flashsale.xiaolumm import util_description

logger = logging.getLogger('celery.handler')

from flashsale.xiaolumm.models.models_fortune import OrderCarry, ClickCarry, UniqueVisitor, ClickPlan
from flashsale.xiaolumm import util_unikey

import sys
import datetime


# def get_click_plan(order_num):
#    MAX_ORDER_NUM = 5
#    DEFAULT_PRICE = 10
#    DEFAULT_LIMIT = 10
#    DEFAULT_NAME = "Default"
#
#    if order_num > MAX_ORDER_NUM:
#        order_num = MAX_ORDER_NUM
#
#    key = str(order_num)
#
#    click_plans = ClickPlan.objects.filter(status=0)
#    if click_plans.count() > 0:
#        click_plan = click_plans[0]
#        rules = click_plan.order_rules
#
#        if key in rules:
#            price, limit, name = rules[key][0], rules[key][1], click_plan.name
#        else:
#            price, limit, name = DEFAULT_PRICE, DEFAULT_LIMIT, DEFAULT_NAME
#    return price, limit, name




def get_cur_info():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        f = sys.exc_info()[2].tb_frame.f_back
    # return (f.f_code.co_name, f.f_lineno)
    return f.f_code.co_name


def confirm_clickcarry(click_carry, mama_id, date_field):
    """
    Get confirmed order number and write back to clickcarry.
    """

    confirmed_order_num = OrderCarry.objects.filter(mama_id=mama_id, date_field=date_field, status=2, carry_num__gt=0).exclude(
        carry_type=3).values('contributor_id').distinct().count()
    price, limit, name = plan_for_price_limit_name(confirmed_order_num, click_carry.carry_plan_id)
    click_num = click_carry.click_num
    if not click_carry.is_confirmed():
        # first time confirm, we have to double-check the click_num
        click_num = UniqueVisitor.objects.filter(mama_id=mama_id, date_field=date_field).count()
        click_carry.click_num = click_num

    if click_num > limit:
        click_num = limit

    total_value = click_num * price
    click_carry.confirmed_order_num = confirmed_order_num
    click_carry.confirmed_click_price = price
    click_carry.confirmed_click_limit = limit
    click_carry.total_value = total_value
    click_carry.status = 2  # confirm
    click_carry.save()


@task()
def task_confirm_previous_zero_order_clickcarry(mama_id, today_date_field, num_days):
    """
    This is how a zero order clickcarry gets confirmed:
    everytime a new clickcarry gets created, we confirm
    any clickcarry generated in previous 7 days, if and
    only if the clickcarry doesnt have an order related to it.
    e.g init_order_num == 0
    """
    end_date_field = today_date_field - datetime.timedelta(days=num_days)

    click_carrys = ClickCarry.objects.filter(mama_id=mama_id, date_field__lte=end_date_field, status=1,
                                             init_order_num=0).order_by('-date_field')[:7]
    if click_carrys.count() <= 0:
        return

    for click_carry in click_carrys:
        date_field = click_carry.date_field
        click_num = UniqueVisitor.objects.filter(mama_id=mama_id, date_field=date_field).count()
        click_carry.click_num = click_num
        price = click_carry.init_click_price
        limit = click_carry.init_click_limit
        if click_num > limit:
            click_num = limit
        total_value = click_num * price
        click_carry.total_value = total_value
        click_carry.status = 2  # confirm
        click_carry.save()

@task()
def task_confirm_previous_order_clickcarry(mama_id, today_date_field, num_days):
    end_date_field = today_date_field - datetime.timedelta(days=num_days)

    click_carrys = ClickCarry.objects.filter(mama_id=mama_id, date_field__lte=end_date_field, status=1,
                                             init_order_num__gt=0).order_by('-date_field')[:7]

    for click_carry in click_carrys:
        date_field = click_carry.date_field
        pending_order_num = OrderCarry.objects.filter(mama_id=mama_id, date_field=date_field, status=1).exclude(
            carry_type=3).values('contributor_id').distinct().count()
        if pending_order_num == 0:
            confirm_clickcarry(click_carry, mama_id, date_field)


def create_clickcarry_upon_click(mama_id, date_field):
    """
    ClickCarry records are created only upon click happens.
    When we are going to create a clickcarry record, we have
    to get the order_num (all pending+confirmed orders) and
    calculate price, limit, price, etc.
    """

    order_num = OrderCarry.objects.filter(mama_id=mama_id, date_field=date_field).exclude(status=0).exclude(
        status=3).exclude(carry_type=3).values('contributor_id').distinct().count()
    click_num = 1
    status = 1  # pending
    click_plan = get_active_click_plan(mama_id)
    price, limit, name = plan_for_price_limit_name(order_num, click_plan.pk)
    uni_key = util_unikey.gen_clickcarry_unikey(mama_id, date_field)
    carry_description = util_description.get_clickcarry_description()
    total_value = price * click_num
    carry = ClickCarry(mama_id=mama_id, click_num=click_num, init_order_num=order_num,
                       init_click_price=price, init_click_limit=limit, total_value=total_value,
                       carry_plan_name=name, carry_plan_id=click_plan.pk,
                       carry_description=carry_description,
                       date_field=date_field, uni_key=uni_key, status=status)
    carry.save()


def update_clickcarry_upon_order(click_carry, mama_id, date_field):
    """
    We count all pending+confirmed orders, and simply update
    init fields.
    """

    order_num = OrderCarry.objects.filter(mama_id=mama_id, date_field=date_field, carry_num__gt=0).exclude(status=0).exclude(
        status=3).exclude(carry_type=3).values('contributor_id').distinct().count()
    if click_carry.init_order_num != order_num:
        # update price, limit, total_value
        price, limit, name = plan_for_price_limit_name(order_num, click_carry.carry_plan_id)
        click_num = click_carry.click_num
        if click_num > limit:
            click_num = limit
        total_value = click_num * price

        click_carry.init_order_num = order_num
        click_carry.init_click_price = price
        click_carry.init_click_limit = limit
        click_carry.total_value = total_value
        click_carry.save()


def get_active_click_plan(mama_id=None):
    """
    Get the first active click plan, and use it. Thus,
    we have to make sure only 1 active plan exists.
    """

    from flashsale.xiaolumm.models.models_fortune import ClickPlan
    from flashsale.xiaolumm.models import XiaoluMama
    
    if mama_id:
        now = datetime.datetime.now()
        mama = XiaoluMama.objects.filter(id=mama_id, renew_time__lt=now).first()
        if mama:
            #如果妈妈已经过期，则试用体验0元妈妈点击计划
            return ClickPlan.objects.filter(id=26).first()

    return ClickPlan.get_active_clickplan()


def plan_for_price_limit_name(order_num, carry_plan_id):
    try:
        click_plan = ClickPlan.objects.get(id=carry_plan_id)
        rules = click_plan.order_rules

        if order_num > click_plan.max_order_num:
            order_num = click_plan.max_order_num

        key = str(order_num)
        if key in rules:
            price, limit, name = rules[key][0], rules[key][1], click_plan.name
            return price, limit, name
    except:
        pass

    price, limit, name = 10, 10, "Default"
    return price, limit, name


@task()
def task_visitor_increment_clickcarry(mama_id, date_field):
    #print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    uni_key = util_unikey.gen_clickcarry_unikey(mama_id, date_field)
    click_carrys = ClickCarry.objects.filter(uni_key=uni_key)

    if click_carrys.count() <= 0:
        # task_confirm_previous_zero_order_clickcarry.s(mama_id, date_field, 2)()
        create_clickcarry_upon_click(mama_id, date_field)
    else:
        click_carry = click_carrys[0]
        price = click_carry.init_click_price
        limit = click_carry.init_click_limit

        click_num = click_carry.click_num
        if click_num % 10 == 0:
            # every 10 clicks, we check with unique visitors to calculate click_num
            click_num = UniqueVisitor.objects.filter(mama_id=mama_id, date_field=date_field).count()
        else:
            click_num = click_num + 1

        if click_num <= limit:
            total_value = click_num * price
            click_carry.click_num = click_num
            click_carry.total_value = total_value
            click_carry.save(update_fields=['click_num', 'total_value', 'modified'])
        else:
            click_carrys.update(click_num=click_num)


@task()
def task_update_clickcarry_order_number(mama_id, date_field):
    print "%s, mama_id: %s" % (get_cur_info(), mama_id)

    click_carrys = ClickCarry.objects.filter(mama_id=mama_id, date_field=date_field)
    if click_carrys.count() <= 0:
        return

    # now we have click carry record exists.
    click_carry = click_carrys[0]
    today = datetime.datetime.now().date()
    if today == date_field:
        update_clickcarry_upon_order(click_carry, mama_id, date_field)
        return

    # check whether we should confirm the clickcarry
    pending_order_num = OrderCarry.objects.filter(mama_id=mama_id, date_field=date_field, status=1).exclude(
        carry_type=3).values('contributor_id').distinct().count()

    if pending_order_num == 0:
        confirm_clickcarry(click_carry, mama_id, date_field)
    else:
        update_clickcarry_upon_order(click_carry, mama_id, date_field)
