# coding: utf-8

SP_BRAND = 'brand'
SP_TOP   = 'atop'
SP_SALE  = 'sale'
SP_TOPIC  = 'topic'


from django.conf import settings

if settings.DEBUG:
    XIAOLU_ROOT_CATEGORY_ID = '4'
else:
    XIAOLU_ROOT_CATEGORY_ID = '4'

WAP_PUSH_TAG = u'每日推送'

VENDOR_TO_CUSTOMER = 0
STOCK_TO_CUSTOMER  = 1
STOCKING_MODE_CHOICES = ((VENDOR_TO_CUSTOMER, u'直发'), (STOCK_TO_CUSTOMER, u'备货'))