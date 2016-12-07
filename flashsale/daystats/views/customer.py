# encoding=utf8
from itertools import groupby
from datetime import datetime, timedelta
from django.shortcuts import render
from django.db import connections
from django.db.models import Count, Min, Sum, Avg
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from flashsale.pay.models.user import Customer, BudgetLog
from flashsale.pay.models.envelope import Envelop
from mall.xiaolupay.models.weixin_red_envelope import WeixinRedEnvelope
from flashsale.pay.models.trade import SaleTrade
from flashsale.xiaolumm.models import (
    XiaoluMama,
    CashOut
)
from flashsale.xiaolumm.models.models_fortune import (
    CarryRecord, OrderCarry, ReferalRelationship, ClickCarry, AwardCarry,
    MamaDailyAppVisit,
    MamaFortune
)
from flashsale.daystats.mylib.db import (
    get_cursor,
    execute_sql,
)
from flashsale.daystats.mylib.util import (
    groupby,
    process,
)

from flashsale.daystats.mylib.chart import generate_chart, generate_date


def process_data(data):
    def bydate(item):
        return item['created'].date()

    def count(item):
        return item[0], len(list(item[1]))

    data = groupby(data, bydate)
    data = map(count, data)
    return [x[1] for x in data]


@login_required
@cache_page(60 * 15)
def list(req):
    q_customer = req.GET.get('customer')
    q_xlmm = req.GET.get('xlmm')
    q_page = req.GET.get('page') or 1

    sql = """
        SELECT
            flashsale_customer.created,
            flashsale_customer.nick,
            flashsale_customer.mobile,
            xiaolumm_xiaolumama.id as mama_id
        FROM flashsale_customer
        left join xiaolumm_xiaolumama on xiaolumm_xiaolumama.openid=flashsale_customer.unionid
        where flashsale_customer.mobile != ''
    """
    if q_xlmm == 'not':
        sql += """
        and xiaolumm_xiaolumama.id is null
        """

    if q_xlmm == 'yes':
        sql += """
        and xiaolumm_xiaolumama.id is not null
        """

    if q_xlmm in ['3', '15', '183', '365']:
        sql += """
        and xiaolumm_xiaolumama.charge_status = 'charged'
        and xiaolumm_xiaolumama.last_renew_type = %s
        """ % (q_xlmm)

    if q_customer == 'has_buy':
        sql += """
        and flashsale_customer.first_paytime is not null
        """

    if q_customer == 'no_buy':
        sql += """
        and flashsale_customer.first_paytime is null
        """

    sql += """
        order by flashsale_customer.created desc
        limit 1000
    """
    queryset = execute_sql(get_cursor(), sql)

    p = Paginator(queryset, 50)
    cur_page = p.page(q_page)
    p.show_page_range = [x for x in p.page_range if 3 >= (x-cur_page.number) >= -3]
    queryset = cur_page.object_list

    for item in queryset:
        mama_id = item.get('mama_id')
        if not mama_id:
            continue
        sq = """
        SELECT sum(carry_num) as money FROM flashsale_xlmm_order_carry
        where mama_id = %s
            and status in (1, 2)
        """
        order_carrys = execute_sql(get_cursor(), sq, [mama_id])
        order_carry = order_carrys[0]['money'] if order_carrys else None
        item['order_carry'] = order_carry / 100 if order_carry else 0

        sql1 = """
            SELECT * FROM flashsale_xlmm_mamadailyappvisit
            where mama_id = %s
            order by created desc
            limit 30
        """
        visit_record = execute_sql(get_cursor(), sql1, [mama_id])

        def func(item):
            now = datetime.now()
            delta = (now - item['created']).days
            if delta <= 7:
                return '7'
            elif delta <= 14:
                return '14'
            elif delta <= 30:
                return '30'
            else:
                return '>30'

        visit_record = groupby(visit_record, func)
        visit_record['7'] = len(visit_record.get('7', []))
        visit_record['14'] = len(visit_record.get('14', [])) + visit_record['7']
        visit_record['30'] = len(visit_record.get('30', [])) + visit_record['14']

        item['visit'] = visit_record

    return render(req, 'yunying/customer/list.html', locals())


@login_required
def index(req):
    now = datetime.now()
    p_start_date = req.GET.get('start_date', '2016-07-01')
    p_end_date = req.GET.get('end_date', '%s-%s-%s' % (now.year, now.month, now.day+1))
    start_date = datetime.strptime(p_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(p_end_date, '%Y-%m-%d')

    cursor = connections['product'].cursor()

    where = ' created > "{0}" and created < "{1}" '.format(p_start_date, p_end_date)

    sql = """SELECT DATE(created) as day, count(DATE(created))
             FROM flashsale_customer where {0} group by DATE(created);""".format(where)
    customers = execute_sql(cursor, sql)

    sql = """SELECT DATE(created), count(DATE(created))
             FROM xiaolumm_xiaolumama WHERE {0} GROUP by DATE(created) """.format(where)
    xiaolumm = execute_sql(cursor, sql)

    sql = """SELECT DATE(created), count(DATE(created))
             FROM flashsale_trade where {0} group by DATE(created)""".format(where)
    trades_all = execute_sql(cursor, sql)

    sql = """SELECT DATE(created), count(DATE(created))
             FROM flashsale_trade where pay_time is not null and {0} group by DATE(created)""".format(where)
    trades_pay = execute_sql(cursor, sql)

    sql = """
        SELECT DATE(flashsale_trade.pay_time), count(DATE(flashsale_trade.pay_time))
        FROM flashsale_trade
        join flashsale_customer on flashsale_customer.id=flashsale_trade.buyer_id
        join xiaolumm_xiaolumama on flashsale_customer.unionid=xiaolumm_xiaolumama.openid
        where flashsale_trade.created > "{0}"
            and flashsale_trade.created < "{1}"
            and flashsale_trade.pay_time is not null
        group by DATE(flashsale_trade.created)
    """.format(p_start_date, p_end_date)
    xiaolumm_trades = execute_sql(cursor, sql)

    sql = """
        SELECT DATE(subscribe_time), count(DATE(subscribe_time))
        FROM shop_weixin_fans group by DATE(subscribe_time)
    """
    weixin_fans = execute_sql(cursor, sql)

    customer_items = {
        '新增小鹿妈妈': [int(x[1]) for x in xiaolumm],
        '新增用户数': [int(x[1]) for x in customers],
    }
    trade_items = {
        '付款订单数': [int(x[1]) for x in trades_pay],
        '所有订单（含未付款）': [int(x[1]) for x in trades_all],
        '来自小鹿妈妈订单': [int(x[1]) for x in xiaolumm_trades],
    }
    weixin_items = {
        '小鹿美美粉丝': [int(x[1]) for x in weixin_fans],
    }

    x_axis = [x.strftime('%Y-%m-%d') for x in generate_date(start_date, end_date)]
    x1_axis = [x[0].strftime('%Y-%m-%d') for x in weixin_fans if x[0] is not None]

    charts = []
    charts.append(generate_chart('customer', x_axis, customer_items))
    charts.append(generate_chart('trade', x_axis, trade_items))
    charts.append(generate_chart('公众号', x1_axis, weixin_items, width='1200px'))

    return render(req, 'yunying/customer/index.html', {'charts': charts})


# @login_required
def wallet(req):
    mama_id = req.GET.get('mama_id') or ''
    if mama_id and len(mama_id) == 11:
        mobile = mama_id
        customer = Customer.objects.filter(mobile=mobile).first()
        mama = XiaoluMama.objects.filter(openid=customer.unionid).first()
    elif mama_id:
        mama = XiaoluMama.objects.filter(id=mama_id).first()
        customer = Customer.objects.filter(unionid=mama.openid).first()
    else:
        mama = None
        customer = None

    if customer:
        xiaolu_wallet = BudgetLog.objects.filter(customer_id=customer.id).order_by('-created')
        xiaolu_wallet_in = BudgetLog.objects.filter(
            customer_id=customer.id,
            budget_type=BudgetLog.BUDGET_IN,
            status__in=(BudgetLog.PENDING, BudgetLog.CONFIRMED)
        ).aggregate(amount=Sum('flow_amount'))['amount'] * 0.01
        xiaolu_wallet_out = BudgetLog.objects.filter(
            customer_id=customer.id,
            budget_type=BudgetLog.BUDGET_OUT,
            status__in=(BudgetLog.PENDING, BudgetLog.CONFIRMED)
        ).aggregate(amount=Sum('flow_amount'))['amount'] * 0.01
        xiaolu_wallet_remain = xiaolu_wallet_in - xiaolu_wallet_out
        for item in xiaolu_wallet:
            item.flow_amount = item.flow_amount * 0.01
            item.budget_type = dict(BudgetLog.BUDGET_CHOICES).get(item.budget_type)
            item.budget_log_type = dict(BudgetLog.BUDGET_LOG_CHOICES).get(item.budget_log_type)
            item.status = dict(BudgetLog.STATUS_CHOICES).get(item.status)

    if mama:
        mama_wallet = CashOut.objects.filter(xlmm=mama.id).order_by('-created')
        for item in mama_wallet:
            item.value = item.value * 0.01
            item.cash_out_type = dict(CashOut.TYPE_CHOICES).get(item.cash_out_type)
            item.status = dict(CashOut.STATUS_CHOICES).get(item.status)
        fortune = MamaFortune.objects.filter(mama_id=mama_id).first()
        if fortune:
            cash_num = fortune.cash_num_display()
        else:
            cash_num = 0

    query = []
    if mama:
        query.append(mama.id)
    if customer:
        query.append(customer.mobile)

    if query:
        envelopes = Envelop.objects.filter(receiver__in=query).order_by('-created')
        for item in envelopes:
            item.amount = item.amount * 0.01
            item.status = dict(Envelop.STATUS_CHOICES).get(item.status)
            item.wx = WeixinRedEnvelope.objects.filter(mch_billno=item.envelop_id).first()
    return render(req, 'yunying/customer/wallet.html', locals())
