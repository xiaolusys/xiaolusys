# coding: utf8
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

import datetime

from ..models import PackageOrder, PackageSkuItem
from shopback.warehouse.models import WareHouse

import logging
logger = logging.getLogger(__name__)

@app.task()
def task_push_packageorder_to_fengchao():
    """　推送包裹到蜂巢仓库 """
    from shopback.outware.adapter.mall.push import order

    push_deadline = datetime.datetime.now() - datetime.timedelta(seconds=30 * 60)
    fengchao_whs_ids = list(WareHouse.get_fengchao_warehouses().values_list('id',flat=True))
    packages = PackageOrder.objects.filter(
        ware_by__in=fengchao_whs_ids,
        sys_status=PackageOrder.WAIT_PREPARE_SEND_STATUS,
        created__lte=push_deadline,
    )

    batch_no = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    logger.info({
        'action': 'task_push_packages_to_fengchao_start',
        'action_time': datetime.datetime.now(),
        'count': packages.count(),
        'push_deadline': push_deadline,
        'batch_no': batch_no,
    })

    for package in packages.iterator():
        try:
            order.push_outware_order_by_package(package)
        except Exception, exc:
            logger.error(str(exc), exc_info=True)
        else:
            package.status = PackageOrder.WAIT_OUTWARE_SEND_CALLBACK
            package.save()

    logger.info({
        'action': 'task_push_packages_to_fengchao_end',
        'action_time': datetime.datetime.now(),
        'batch_no': batch_no,
    })




