# -*- coding:utf8 -*-
from celery import Task
from celery import group

from shopback.trades.models import (MergeTrade,
                                    MergeOrder)

from shopback.items.tasks import releaseProductTradesTask


class CancelMergeOrderStockOutTask(Task):
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
