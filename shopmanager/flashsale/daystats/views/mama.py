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
)
from flashsale.daystats.lib.db import get_cursor
from flashsale.daystats.lib.util import (
    process_data,
    groupby,
    process,
)


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


def new_mama(req):
    from flashsale.coupon.models import OrderShareCoupon
    from flashsale.xiaolumm.models import XlmmFans, PotentialMama, XiaoluMama
    from flashsale.xiaolumm.models.models_fortune import CarryRecord, OrderCarry, ReferalRelationship
    from shopapp.weixin.models_base import WeixinFans

    sql = """
    SELECT id FROM xiaoludb.xiaolumm_xiaolumama
    where created > '2016-08-26' and created < '2016-08-27' and agencylevel=3
    """
    mama_ids = execute_sql(get_cursor(), sql)

    mama_tasks = {}

    for mama_id in mama_ids:
        mama_id = mama_id['id']
        mama = XiaoluMama.objects.filter(id=mama_id).first()
        customer = mama.get_customer()

        # 新手任务
        subscribe_weixin = WeixinFans.objects.filter(
            unionid=customer.unionid, subscribe=True, app_key=settings.WXPAY_APPID).exists()

        carry_record = CarryRecord.objects.filter(mama_id=mama_id, carry_type=CarryRecord.CR_CLICK).exists()

        coupon_share = OrderShareCoupon.objects.filter(share_customer=customer.id).exists()

        fans_record = XlmmFans.objects.filter(xlmm=mama_id).exists()

        mama_recommend = PotentialMama.objects.filter(referal_mama=mama_id).exists() or \
            ReferalRelationship.objects.filter(referal_from_mama_id=mama_id).exists()

        commission = OrderCarry.objects.filter(mama_id=mama_id).exists()

        mama_tasks[mama_id] = {
            'subscribe_weixin': subscribe_weixin,
            'carry_record': carry_record,
            'coupon_share': coupon_share,
            'fans_record': fans_record,
            'mama_recommend': mama_recommend,
            'commission': commission,
        }
        print mama_tasks[mama_id]
