# coding: utf-8

from django.conf import settings

if settings.DEBUG:
    PAGE_SIZE = 3
else:
    PAGE_SIZE = 20

SALE_TYPES = (
    (1, u'0-50元'),
    (2, u'50-150元'),
    (3, u'150以上'),
    (4, u'引流款')
)

SCHEDULE_API_TYPE_PRICE = 1
SCHEDULE_API_TYPE_SECKILL = 2
SCHEDULE_API_TYPE_WATERMARK = 3
SCHEDULE_API_TYPE_STATUS = 4
