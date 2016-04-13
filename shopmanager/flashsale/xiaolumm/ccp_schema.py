# coding:utf-8
import datetime

CCP_SCHEMA = (
    # (起始时间，结束时间，订单人数，点击价格，点击上限)
    ('2016-03-21', '2016-03-21', 4, 50, 210),
    ('2016-03-21', '2016-03-21', 2, 40, 110),
    ('2016-03-21', '2016-03-21', 1, 30, 60),
    ('2016-03-02', '2016-03-04', 10, 80, 510),
    ('2016-03-02', '2016-03-04', 6, 60, 310),
    ('2016-03-02', '2016-03-04', 4, 50, 210),
    ('2016-03-02', '2016-03-04', 2, 40, 110),
    ('2016-03-02', '2016-03-04', 0, 30, 10),
    ('2016-02-24', '2016-02-26', 0, 30, 10),
)


def parse_date(date_str):
    return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()


def get_ccp_price(day_date, order_num):
    if not isinstance(day_date, datetime.date) or len(CCP_SCHEMA) == 0:
        return None

    ccp_a = CCP_SCHEMA[0]
    ccp_z = CCP_SCHEMA[-1]
    if parse_date(ccp_a[1]) < day_date or day_date < parse_date(ccp_z[0]):
        return None

    for ccp in CCP_SCHEMA:
        if (day_date >= parse_date(ccp[0]) and day_date <= parse_date(ccp[1])) and order_num >= ccp[2]:
            return ccp[3]

    return None


def get_ccp_count(day_date, order_num):
    if not isinstance(day_date, datetime.date) or len(CCP_SCHEMA) == 0:
        return None

    ccp_a = CCP_SCHEMA[0]
    ccp_z = CCP_SCHEMA[-1]
    if parse_date(ccp_a[1]) < day_date or day_date < parse_date(ccp_z[0]):
        return None

    for ccp in CCP_SCHEMA:
        if (day_date >= parse_date(ccp[0]) and day_date <= parse_date(ccp[1])) and order_num >= ccp[2]:
            return ccp[4]

    return None
