# coding: utf8
from __future__ import absolute_import, unicode_literals

from shopmanager import celery_app as app

from ..adapter.ware.pull.pms import union_sku_and_supplier
from outware.models import OutwareSku

import logging
logger = logging.getLogger(__name__)

@app.task()
def task_outware_union_supplier_and_sku():

    union_skus = OutwareSku.objects.filter(is_unioned=False)
    for ow_sku in union_skus.iterator():
        try:
            union_sku_and_supplier(ow_sku)
        except Exception, exc:
            logger.error(str(exc), exc_info=True)

