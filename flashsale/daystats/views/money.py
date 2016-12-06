# encoding=utf8
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from flashsale.pay.models.user import Customer, BudgetLog
from flashsale.xiaolumm.models.models_fortune import CarryRecord
from flashsale.xiaolumm.models import (
    XiaoluMama,
    CashOut
)
from flashsale.daystats.mylib.util import (
    get_date_from_req,
)
from flashsale.daystats.mylib.db import (
    get_cursor,
    execute_sql,
)


@login_required
def index(req):
    """
    红包+退款+退款补邮费+兑换订单+妈妈收益佣金=个人账户增加额+妈妈账户增加额+红包支出+个人账户消费支出+个人账户兑换订单支出
    """
    p_start_date, p_end_date, start_date, end_date = get_date_from_req(req)

    sql = """
        SELECT
            budget_log_type as category, sum(flow_amount)*0.01 as amount, budget_type
        FROM
            flashsale_userbudgetlog
        WHERE
            created > '{0}'
        and created < '{1}'
        group by budget_log_type, budget_type
    """.format(p_start_date, p_end_date)
    xiaolu_wallet = execute_sql(get_cursor(), sql)

    for item in xiaolu_wallet:
        item['category'] = dict(BudgetLog.BUDGET_LOG_CHOICES).get(item['category'])

    xiaolu_wallet_in = [x for x in xiaolu_wallet if x['budget_type'] == 0]
    xiaolu_wallet_out = [x for x in xiaolu_wallet if x['budget_type'] == 1]

    sql = """
        SELECT
            carry_type as category, SUM(carry_num)*0.01 as amount
        FROM
            flashsale_xlmm_carry_record
        WHERE
            created > '{0}'
        and created < '{1}'
        AND STATUS = 2
        GROUP BY
            carry_type
    """.format(p_start_date, p_end_date)
    mama_wallet_in = execute_sql(get_cursor(), sql)

    for item in mama_wallet_in:
        item['category'] = dict(CarryRecord.CARRY_TYPES).get(item['category'])

    sql = """
        SELECT
            sum(value)*0.01 as amount, cash_out_type as category
        from xiaolumm_cashout
        WHERE
            created > '{0}'
        and created < '{1}'
        and status='approved'
        GROUP BY
            cash_out_type
    """.format(p_start_date, p_end_date)
    mama_wallet_out = execute_sql(get_cursor(), sql)

    for item in mama_wallet_out:
        item['category'] = dict(CashOut.TYPE_CHOICES).get(item['category'])

    sql = """
        SELECT
            sum(amount)*0.01 as amount
        FROM
            flashsale_envelop
        WHERE
            created > '{0}'
        and created < '{1}'
        and status='confirm'
    """.format(p_start_date, p_end_date)
    envelope_out = execute_sql(get_cursor(), sql)
    print envelope_out

    return render(req, 'yunying/money/index.html', locals())
