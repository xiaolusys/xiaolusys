# coding=utf-8
from __future__ import unicode_literals, absolute_import
from rest_framework import serializers
from flashsale.xiaolumm.models import CashOut

import logging

logger = logging.getLogger(__name__)


class CashOueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashOut
        fields = ('id',
                  "xlmm",
                  "value_money",
                  "get_status_display",
                  "status",
                  "approve_time",
                  "date_field",
                  "get_cash_out_type_display",
                  "created")
