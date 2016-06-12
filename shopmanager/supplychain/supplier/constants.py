# coding: utf-8

from django.conf import settings

if settings.DEBUG:
    XIAOLU_ROOT_CATEGORY_ID = 4
else:
    XIAOLU_ROOT_CATEGORY_ID = 4

WAP_PUSH_TAG = u'每日推送'
