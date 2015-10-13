from __future__ import division
# -*- encoding:utf8 -*-
import datetime

from celery.task import task

from flashsale.pay.models_refund import SaleRefund

import logging

from flashsale.kefu.models import KefuPerformance
from supplychain.supplier.models import SaleProduct, SaleSupplier, SupplierCharge

logger = logging.getLogger('celery.handler')
from django.core.serializers.json import DjangoJSONEncoder
import json


@task(max_retry=1, default_retry_delay=5)
def task_record_kefu_performance(start_date, end_date, record_type="0"):
    """客服操作"""
    try:
        year, month, day = start_date.split('-')
        start_date_time = datetime.datetime(int(year), int(month), int(day))
        year, month, day = end_date.split('-')
        end_date_time = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)
        if record_type == "0":
            all_record = KefuPerformance.objects.filter(operate_time__range=(start_date_time, end_date_time)).order_by(
                "-operate_time")

        else:
            all_record = KefuPerformance.objects.filter(operate_time__range=(start_date_time, end_date_time),
                                                        operation=record_type).order_by("-operate_time")
        result_data = []
        summary_data = {}
        for one_record in all_record:
            temp_dict = {"kefu": one_record.kefu_name, "operate": one_record.get_operation_display(),
                         "operate_time": one_record.operate_time}
            temp_dict = json.dumps(temp_dict, cls=DjangoJSONEncoder)
            result_data.append(temp_dict)
            if one_record.kefu_name in summary_data:
                if one_record.operation == KefuPerformance.CHECK:
                    summary_data[one_record.kefu_name][0] += 1
                if one_record.operation == KefuPerformance.REVIEW:
                    summary_data[one_record.kefu_name][1] += 1
                if one_record.operation == KefuPerformance.DELAY:
                    summary_data[one_record.kefu_name][2] += 1
            else:
                summary_data[one_record.kefu_name] = [1, 1, 1]
    except Exception, exc:
        raise task_record_kefu_performance.retry(exc=exc)
    return {"result_data": result_data, "summary_data": summary_data}

