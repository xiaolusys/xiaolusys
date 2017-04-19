# coding: utf8
from __future__ import absolute_import, unicode_literals

from shopmanager import celery_app as app

from ..adapter.ware.pull.pms import union_sku_and_supplier
from ..models import OutwareSku, OutwareSkuStock

import logging
logger = logging.getLogger(__name__)

@app.task()
def task_outware_union_supplier_and_sku(sku_codes=[]):
    if sku_codes:
        union_skus = OutwareSku.objects.filter(is_unioned=False, sku_code__in=sku_codes)
    else:
        union_skus = OutwareSku.objects.filter(is_unioned=False)

    for ow_sku in union_skus.iterator():
        try:
            union_sku_and_supplier(ow_sku)
        except Exception, exc:
            logger.error(str(exc), exc_info=True)


@app.task()
def task_sync_sku_stocks():
    skucodes = [sku.sku_code for sku in OutwareSku.objects.filter(is_unioned=False)]
    i = 0
    LEN = 50
    now_piece = skucodes[i * LEN, (i+1) * LEN]
    while now_piece:
        OutwareSkuStock.sync_outsys(now_piece)
        i += 1
        now_piece = skucodes[i * LEN, (i+1) * LEN]
