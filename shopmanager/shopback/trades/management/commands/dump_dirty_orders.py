# coding: utf-8

import datetime
from optparse import make_option

from shopback import paramconfig as pcfg
from shopback.trades.models import MergeOrder, DirtyMergeOrder, MergeTrade
from shopback.trades.models_dirty import DirtyMergeOrder, DirtyMergeTrade

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.forms.models import model_to_dict

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (make_option('-t',
                                                         '--test',
                                                         dest='is_test',
                                                         action='store_true',
                                                         default=False,
                                                         help='测试模式'),)

    def handle(self, *args, **kwargs):
        is_test = kwargs.get('is_test') or False

        threshold_datetime = datetime.datetime(2016, 1, 1)
        trade_ids = []
        for order in MergeOrder.objects.select_related('merge_trade').filter(
                merge_trade__type__in=[pcfg.SALE_TYPE, pcfg.DIRECT_TYPE,
                                       pcfg.REISSUE_TYPE, pcfg.EXCHANGE_TYPE],
                merge_trade__sys_status__in=
            [pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS,
             pcfg.WAIT_CHECK_BARCODE_STATUS, pcfg.WAIT_SCAN_WEIGHT_STATUS,
             pcfg.ON_THE_FLY_STATUS, pcfg.REGULAR_REMAIN_STATUS],
                sys_status=pcfg.IN_EFFECT,
                created__lte=threshold_datetime):

            if not order.pay_time:
                continue
            trade_ids.append(order.merge_trade.id)

            dirty_trade, created = DirtyMergeTrade.objects.get_or_create(id=order.merge_trade.id)
            if created:
                DirtyMergeTrade.objects.filter(pk=order.merge_trade.id).update(**model_to_dict(order.merge_trade))

            dirty_order, created = DirtyMergeOrder.objects.get_or_create(id=order.id)
            if created:
                DirtyMergeOrder.objects.filter(pk=order.id).update(**model_to_dict(order))
        if not is_test:
            print MergeTrade.objects.filter(pk__in=trade_ids).update(sys_status=pcfg.FINISHED_STATUS)
