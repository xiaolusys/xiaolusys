# encoding=utf8
from django.conf import settings
from datetime import datetime, timedelta

import sqlparse
import simplejson
from django.shortcuts import render

from flashsale.daystats.lib.db import execute_sql
from flashsale.daystats.lib.chart import (
    generate_chart,
    generate_date,
    generate_chart_data,
)
from flashsale.daystats.lib.db import get_cursor
from flashsale.daystats.lib.util import (
    process_data,
    groupby,
    process,
    format_datetime,
)
from flashsale.pay.models.user import Customer
from flashsale.pay.models.trade import SaleTrade, SaleOrder
from flashsale.coupon.models import OrderShareCoupon
from flashsale.xiaolumm.models import XlmmFans, PotentialMama, XiaoluMama
from flashsale.xiaolumm.models.models_fortune import CarryRecord, OrderCarry, ReferalRelationship
from shopapp.weixin.models_base import WeixinFans


def get_date_from_req(req):
    now = datetime.now()
    last = now - timedelta(days=7)
    p_start_date = req.GET.get('start_date', '%s-%s-%s' % (last.year, last.month, last.day))
    p_end_date = req.GET.get('end_date', '%s-%s-%s' % (now.year, now.month, now.day+1))
    start_date = datetime.strptime(p_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(p_end_date, '%Y-%m-%d')
    return p_start_date, p_end_date, start_date, end_date


def generate_sql_from_tokens(tokens):
    sql = ''
    for token in tokens:
        if isinstance(token, sqlparse.sql.Identifier):
            sql += ''.join([x.value for x in token.tokens])
        else:
            sql += token.value
    return sql


def insert_where_clause(tokens, pos, sql):
    tokens.insert(pos, sqlparse.sql.Where(sql))
    return tokens


def index(req):
    p_start_date, p_end_date, start_date, end_date = get_date_from_req(req)
    key = req.GET.get('key', 'created')

    sql = """
        SELECT * FROM xiaoludb.flashsale_xlmm_mamadailyappvisit
        where created > %s
            and created < %s
    """
    items = execute_sql(cursor, sql, [start_date, end_date])

    items = process_data(items, lambda x: x[key])

    weixin_items = {
        '小鹿妈妈日活': [int(x[1]) for x in items],
    }
    x_axis = [x[0] for x in items if x[0] is not None]

    charts = []
    charts.append(generate_chart('xxx', x_axis, weixin_items, width='1000px'))

    return render(req, 'yunying/mama/index.html', locals())


def show(req):
    mama_id = req.GET.get('mama_id', None)
    customer = None
    if mama_id and len(mama_id) == 11:
        mobile = mama_id
        customer = Customer.objects.using('product').filter(mobile=mobile).first()
        if customer:
            mama = XiaoluMama.objects.using('product').filter(openid=customer.unionid).first()
            mama_id = mama.id
    else:
        mama = XiaoluMama.objects.using('product').filter(id=mama_id).first()
        if mama:
            customer = Customer.objects.using('product').filter(unionid=mama.openid).first()

    if customer:
        wx_fans = WeixinFans.objects.using('product').filter(unionid=customer.unionid)
        orders = SaleOrder.objects.using('product').filter(buyer_id=customer.id) \
            .exclude(pay_time__isnull=True).order_by('-created')

    referal_mama = ReferalRelationship.objects.using('product').filter(referal_to_mama_id=mama_id).first() or \
        PotentialMama.objects.using('product').filter(potential_mama=mama_id).first()
    one_mamas = PotentialMama.objects.using('product').filter(referal_mama=mama_id)
    relations = ReferalRelationship.objects.using('product').filter(referal_from_mama_id=mama_id)

    return render(req, 'yunying/mama/show.html', locals())


def home(req):
    pass


def get_where_clause_pos(tokens):
    where_pos = None
    has = False

    for i, token in enumerate(tokens):
        if isinstance(token, sqlparse.sql.Where):
            has = True
        if token.is_keyword and token.value.upper() == 'FROM':
            where_pos = i + 4

    return (has, where_pos)


def update_where_clause(tokens, where):
    for i, token in enumerate(tokens):
        if isinstance(token, sqlparse.sql.Where):
            token.value += where
    return tokens


def fenzu(items, x=None, key=None, y=None, func_groupby=None):
    # 先按key分组
    if not key:
        series = groupby(items, lambda x: 'all')
    else:
        series = groupby(items, lambda x: x[key])

    x_axis = [x.strftime('%Y-%m-%d') for x in generate_date(start_date, end_date)[:-1]]

    for k, v in series.items():
        # 再按x分组
        if y:
            chart_items = process(groupby(v, lambda x: x['x']), lambda x: int(x[0].get(y)))
        else:
            chart_items = process(groupby(v, lambda x: x['x']), len)
        chart_items = dict(chart_items)
        for x in x_axis:
            if not chart_items.get(x, None):
                chart_items[x] = 0
        chart_items = sorted(chart_items.items(), key=lambda x: x[0], reverse=False)
        series[k] = chart_items

mama_cache = {}


def new_mama(req):
    now = datetime.now()
    last = now - timedelta(days=7)
    p_start_date = req.GET.get('start_date', '%s-%s-%s' % (last.year, last.month, last.day))
    p_end_date = req.GET.get('end_date', '%s-%s-%s' % (now.year, now.month, now.day+1))

    start_date = datetime.strptime(p_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(p_end_date, '%Y-%m-%d')

    cursor = get_cursor()

    sql = """
        SELECT id, created, agencylevel, openid FROM xiaoludb.xiaolumm_xiaolumama
        where created >= %s and created < %s
            and agencylevel=3
    """
    mamas = execute_sql(cursor, sql, [format_datetime(start_date), format_datetime(end_date)])
    p_mamas = PotentialMama.objects.using('product').filter(created__gte=start_date).values('referal_mama')
    p_mamas = set([x['referal_mama'] for x in p_mamas])
    xufei_mamas = PotentialMama.objects.using('product')\
        .filter(created__gte=start_date, is_full_member=True).values('potential_mama')
    xufei_mamas = set([x['potential_mama'] for x in xufei_mamas])
    click_mamas = CarryRecord.objects.using('product') \
        .filter(created__gte=start_date, carry_type=CarryRecord.CR_CLICK).values('mama_id')
    click_mamas = set([x['mama_id'] for x in click_mamas])

    def byfunc(item):
        return item['created']

    def pfunc(items):
        return len(list(set([x['id'] for x in items]) & p_mamas))

    def finish_task_func(items):
        o_mamas = set([x['id'] for x in items])
        return len(list(o_mamas & p_mamas & click_mamas))

    def buyfunc(items):
        count = 0
        for item in items:
            unionid = item['openid']
            customer = Customer.objects.using('product').filter(unionid=unionid).first()
            has_buy = SaleTrade.objects.using('product').filter(buyer_id=customer.id, total_fee__gt=1).exists()
            if has_buy:
                count += 1
        return count

    def xufeifunc(items):
        return len(list(set([x['id'] for x in items]) & xufei_mamas))

    x_axis, new_chart_items = generate_chart_data(
        mamas, xaris='created', key=None, yaris=len, start_date=start_date, end_date=end_date)
    x_axis, chart_items = generate_chart_data(
        mamas, xaris='created', key=None, yaris=pfunc, start_date=start_date, end_date=end_date)
    # x_axis, buy_chart_items = generate_chart_data(
    #     mamas, xaris='created', key=None, yaris=buyfunc, start_date=start_date, end_date=end_date)
    x_axis, xufei_chart_items = generate_chart_data(
        mamas, xaris='created', key=None, yaris=xufeifunc, start_date=start_date, end_date=end_date)
    x_axis, finish_task_chart_items = generate_chart_data(
        mamas, xaris='created', key=None, yaris=finish_task_func, start_date=start_date, end_date=end_date)

    z_items = {}
    yaoqing_data = chart_items.values()[0]
    new_mama_data = new_chart_items.values()[0]
    xufei_mama_data = xufei_chart_items.values()[0]
    finish_task_data = finish_task_chart_items.values()[0]
    # buy_mama_data = buy_chart_items.values()[0]

    ratio_data = []

    for i, item in enumerate(new_mama_data):
        try:
            ratio = round(float(yaoqing_data[i] * 100.0 / item), 2)
        except Exception, e:
            ratio = 0
        ratio_data.append(ratio)

    charts = [generate_chart('小鹿妈妈', x_axis, z_items, width='1000px')]
    y1 = max(new_mama_data) + 100
    y1_interval = int(y1 / 10)
    y2 = max(ratio_data) + 10
    y2_interval = int(y2 / 10)

    return render(req, 'yunying/mama/new_mama.html', locals())


def tab(req):
    p_start_date, p_end_date, start_date, end_date = get_date_from_req(req)
    query = req.GET.get('sql', '')
    query_name = req.GET.get('query_name', 'xx')
    func_groupby = req.GET.get('func_groupby', '')
    date_field = req.GET.get('date_field', 'created')
    p_key_desc = req.GET.get('key_desc', '')

    if not date_field:
        date_field = 'created'

    if func_groupby.strip() == '':
        func_groupby = ''

    if not query:
        return render(req, 'yunying/mama/index.html', locals())

    if p_key_desc:
        key_desc = simplejson.loads(p_key_desc)
    else:
        key_desc = None

    tokens = sqlparse.parse(query)[0].tokens
    has_where, where_pos = get_where_clause_pos(tokens)

    if not has_where:
        where = " where {0} > '{1}' and {0} < '{2}' ".format(date_field, start_date, end_date)
        tokens = insert_where_clause(tokens, where_pos, where)
    else:
        where = " and {0} > '{1}' and {0} < '{2}' ".format(date_field, start_date, end_date)
        tokens = update_where_clause(tokens, where)

    sql = generate_sql_from_tokens(tokens)

    items = execute_sql(get_cursor(), sql)

    if items:
        key = 'k' if 'k' in items[0].keys() else None
        y = 'y' if 'y' in items[0].keys() else None

    # 先按key分组
    if not key:
        if func_groupby:
            exec func_groupby in locals()
            series = groupby(items, func_g)
        else:
            series = groupby(items, lambda x: 'all')
    else:
        series = groupby(items, lambda x: x[key])

    x_axis = [x.strftime('%Y-%m-%d') for x in generate_date(start_date, end_date)[:-1]]

    for k, v in series.items():
        # 再按x分组
        if y:
            chart_items = process(groupby(v, lambda x: x['x']), lambda x: int(x[0].get(y)))
        else:
            chart_items = process(groupby(v, lambda x: x['x']), len)
        chart_items = dict(chart_items)
        for x in x_axis:
            if not chart_items.get(x, None):
                chart_items[x] = 0
        chart_items = sorted(chart_items.items(), key=lambda x: x[0], reverse=False)
        series[k] = chart_items

    weixin_items = {}
    for k, v in series.items():
        if key_desc:
            k = key_desc.get(str(k), 'UNKOWN')
        weixin_items[k] = [x[1] for x in v]

    charts = []
    charts.append(generate_chart(query_name, x_axis, weixin_items, width='1000px'))

    return render(req, 'yunying/mama/index.html', locals())


def get_mama_new_task(mama_id):
    mama = XiaoluMama.objects.using('product').filter(id=mama_id).first()
    customer = Customer.objects.using('product').filter(unionid=mama.openid).first()

    # 新手任务
    subscribe_weixin = WeixinFans.objects.using('product').filter(
        unionid=customer.unionid, subscribe=True, app_key=settings.WXPAY_APPID).exists()

    carry_record = CarryRecord.objects.using('product') \
        .filter(mama_id=mama_id, carry_type=CarryRecord.CR_CLICK).exists()

    coupon_share = OrderShareCoupon.objects.using('product').filter(share_customer=customer.id).exists()

    fans_record = XlmmFans.objects.using('product').filter(xlmm=mama_id).exists()

    mama_recommend = PotentialMama.objects.using('product').filter(referal_mama=mama_id).exists() or \
        ReferalRelationship.objects.filter(referal_from_mama_id=mama_id).exists()

    commission = OrderCarry.objects.using('product').filter(mama_id=mama_id).exists()

    mama_task = {
        'subscribe_weixin': subscribe_weixin,
        'carry_record': carry_record,
        'coupon_share': coupon_share,
        'fans_record': fans_record,
        'mama_recommend': mama_recommend,
        'commission': commission,
    }
    return mama_task


def new_task(req):
    mama_id = req.GET.get('mama_id', '')
    if mama_id:
        mama_task = get_mama_new_task(mama_id)
    return render(req, 'yunying/mama/new_task.html', locals())
