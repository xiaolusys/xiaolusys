# coding=utf-8

# 订单一一对应记录的订单状态汇总
NOT_PAY = 0
PAID = 1
CANCEL = 2
OUT_STOCK = 3
RETURN_GOODS = 4

STATUS = (
    (NOT_PAY, u'未付款'),
    (PAID, u'已付款'),
    (CANCEL, u'发货前退款'),
    (OUT_STOCK, u'缺货退款'),
    (RETURN_GOODS, u'退货退款'),
)

# 订单一一对应的退货申请状态
HAS_RETURN = 1
NO_RETURN = 0

RETURN_CHOICES = (
    (HAS_RETURN, u'有申请退货'),
    (NO_RETURN, u'无申请退货'),
)

# 统计记录类型的汇总
TYPE_SKU = 1
TYPE_COLOR = 4
TYPE_MODEL = 7
TYPE_SUPPLIER = 13
TYPE_BD = 14
TYPE_AGG = 16
TYPE_SNAPSHOT = 17

RECORD_TYPES = (
    (TYPE_SKU, u'SKU级'),
    (TYPE_COLOR, u'颜色级'),
    (TYPE_MODEL, u'款式级'),
    (TYPE_SUPPLIER, u'供应商级'),
    (TYPE_BD, u'买手BD级'),
    (TYPE_AGG, u'总计'),
    (TYPE_SNAPSHOT, u'每日快照')
)

# 时间 维度统计 维度汇总
TIMELY_TYPE_DATE = 6
TIMELY_TYPE_WEEK = 7
TIMELY_TYPE_MONTH = 8
TIMELY_TYPE_QUARTER = 9
TIMELY_TYPE_YEAR = 10

TIMELY_AGG_TYPE = (
    (TIMELY_TYPE_DATE, u'日报'),
    (TIMELY_TYPE_WEEK, u'周报'),
    (TIMELY_TYPE_MONTH, u'月报'),
    (TIMELY_TYPE_QUARTER, u'季报'),
    (TIMELY_TYPE_YEAR, u'年报')
)

TIMELY_TYPES = TIMELY_AGG_TYPE

