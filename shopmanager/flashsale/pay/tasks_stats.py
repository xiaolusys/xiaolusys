
from django.db import IntegrityError
from django.db.models import Sum
from celery.task import task

from flashsale.pay.models import ShoppingCart, SaleOrder

import logging
logger = logging.getLogger(__name__)


@task()
def task_update_saletrade_refund_status():
    from flashsale.pay.models import SaleOrder, SaleRefund
    from django.db.models import Q
    so = SaleOrder.objects.filter(Q(refund_status=SaleRefund.REFUND_SUCCESS)|Q(refund_status=SaleRefund.REFUND_CLOSED),
                                  sale_trade__status__in=[2,3,4])
    from flashsale.pay.tasks import tasks_update_sale_trade_status
    for instance in so:
        if instance.status > SaleOrder.WAIT_BUYER_PAY:
            tasks_update_sale_trade_status(instance.sale_trade_id)
