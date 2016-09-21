# encoding=utf8
from datetime import timedelta
from django.template import Template, Context
from flashsale.daystats.mylib.util import (
    process_data,
    groupby,
    process,
)


def generate_chart(name, x_axis, items, width='600px'):

    tpl = Template("""[
    {% for k, v in items.items %}
    {
        name: "{{ k }}",
        type: 'line',
        data: {{ v }},
    },
    {% endfor %}
    ]""")
    context = Context({'items': items})
    series = tpl.render(context)

    legend = [k for k, v in items.items()]

    return {
        'name': name,
        'x_axis': x_axis,
        'series': series,
        'width': width,
        'legend': legend
    }


def generate_date(start_date, end_date):
    date = start_date

    ranges = []
    while date <= end_date:
        ranges.append(date)
        date = date + timedelta(days=1)
    return ranges


def generate_chart_data(items, xaris=None, key=None, yaris=None, start_date=None, end_date=None):
    """
    {
        k1: {
            '2016-08': [{}],
            '2016-09': [{}],
        },
        k2: {
            '2016-08': [{}],
            '2016-09': [{}],
        },
    }
    """
    # 先按key分组
    if not key:
        series = groupby(items, lambda x: 'all')
    else:
        series = groupby(items, key)

    x_axis = [i.strftime('%Y-%m-%d') for i in generate_date(start_date, end_date)[:-1]]

    for k, v in series.items():
        # 再按x分组
        if yaris:
            chart_items = process(groupby(v, lambda x: x[xaris]), yaris)
        else:
            chart_items = process(groupby(v, lambda x: x[xaris]), len)

        # 补全空缺日期
        chart_items = dict(chart_items)
        for x in x_axis:
            if not chart_items.get(x, None):
                chart_items[x] = 0

        # 按日期排序
        chart_items = sorted(chart_items.items(), key=lambda x: x[0], reverse=False)
        series[k] = chart_items

    chart_items = {}
    for k, v in series.items():
        chart_items[k] = [x[1] for x in v]

    return x_axis, chart_items
