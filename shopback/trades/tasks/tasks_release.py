# -*- coding:utf8 -*-
##################################3
### deprecated
##################################3
from __future__ import absolute_import, unicode_literals
from shopmanager import celery_app as app

from celery import group

from shopback.trades.models import (MergeTrade,
                                    MergeOrder)

from shopback.items.tasks import releaseProductTradesTask

class CancelMergeOrderStockOutTask(object):
    """ 定时检查并取消订单缺货任务 """

    def get_stockout_productcode_tuple(self):
        morders = MergeOrder.objects.filter(out_stock=True,
                                            sys_status=MergeOrder.NORMAL,
                                            merge_trade__status__in=(MergeTrade.REGULAR_REMAIN_STATUS,
                                                                     MergeTrade.WAIT_AUDIT_STATUS))
        return morders.values_list('outer_id').distinct()

    def run(self, *args, **kwargs):
        pcode_tuple = self.get_stockout_productcode_tuple()
        group([releaseProductTradesTask.s(pcode) for pcode in pcode_tuple])()

@app.task()
def task_cancel_mergeorder_stockout(*args, **kwarg):
    CancelMergeOrderStockOutTask().run(*args, **kwarg)


