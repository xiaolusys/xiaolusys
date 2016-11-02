# -*- coding:utf8 -*-
import json
import time
import datetime
from celery.task import task
from django.db.models import Q
from shopback import paramconfig as pcfg
from shopback.trades.models import MergeTrade, MergeBuyerTrade
from shopback.orders.models import Order, Trade
from shopapp.memorule.models import RuleMemo, TradeRule
from shopback.logistics.models import LogisticsCompany
from shopback.monitor.models import SystemConfig
from shopback.signals import rule_signal
from common.utils import parse_datetime, single_instance_task
from auth.apis import taobao_trade_memo_update
import logging

logger = logging.getLogger('django.request')


@single_instance_task(30 * 60, prefix='shopapp.memorule.tasks.')
def updateTradeAndOrderByRuleMemo():
    rule_memos = RuleMemo.objects.filter(is_used=False).exclude(rule_memo='')
    for rule_memo in rule_memos:
        rule_memo_dict = json.loads(rule_memo.rule_memo)
        try:
            merge_trade = MergeTrade.objects.get(tid=rule_memo_dict['tid'])
        except MergeTrade.DoesNotExist:
            pass
        else:
            try:
                has_memo = merge_trade.buyer_message or merge_trade.seller_memo
                has_refunding = merge_trade.has_trade_refunding()
                try:
                    MergeBuyerTrade.objects.get(sub_tid=merge_trade.tid)
                except:
                    is_merge_trade = False
                else:
                    is_merge_trade = True

                express_name = rule_memo_dict.get('post', None)
                if express_name:
                    express_name = express_name.strip()
                    try:
                        logistics_company = LogisticsCompany.objects.get(name=express_name)
                    except:
                        logger.error('get express company(%s) object error.' % express)
                    else:
                        merge_trade.logistics_company_name = express_name
                        merge_trade.logistics_company_code = logistics_company.code
                address = rule_memo_dict.get('addr', None)
                if address:
                    merge_trade.receiver_address = address

                orders_data = rule_memo_dict.get('data', [])
                for o in orders_data:
                    order = Order.objects.get(Q(outer_id=o['pid']) | Q(outer_sku_id=o['pid']),
                                              trade=rule_memo_dict['tid'])
                    sku_properties = ' '.join([v for k, v in o['property'].items()])
                    order.sku_properties_name += sku_properties
                    order.save()

                merge_trade.sys_status = (((pcfg.WAIT_AUDIT_STATUS if has_memo
                                            else pcfg.WAIT_PREPARE_SEND_STATUS)
                                           if not has_refunding else pcfg.WAIT_AUDIT_STATUS)
                                          if not is_merge_trade else pcfg.ON_THE_FLY_STATUS)
                MergeTrade.objects.filter(tid=merge_trade.tid).update(
                    logistics_company_name=merge_trade.logistics_company_name,
                    logistics_company_code=merge_trade.logistics_company_code,
                    receiver_address=merge_trade.receiver_address,
                    sys_status=merge_trade.sys_status,
                )

                # rule_signal.send(sender='trade_rule',trade_id=merge_trade.id)
                RuleMemo.objects.filter(tid=rule_memo.tid).update(is_used=True)
            except Exception, exc:
                logger.error('update rule error', exc_info=True)


@single_instance_task(30 * 60, prefix='shopapp.memorule.tasks.')
def updateTradeSellerFlagTask():
    system_config = SystemConfig.getconfig()
    if system_config and system_config.is_flag_auto:
        dt = datetime.datetime.now()
        start_date = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)
        trades = MergeTrade.objects.filter(sys_status__in=
                                           (pcfg.WAIT_PREPARE_SEND_STATUS,
                                            pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                            pcfg.WAIT_CONFIRM_SEND_STATUS,
                                            pcfg.WAIT_AUDIT_STATUS)) \
            .include(modified__gt=modified,
                     sys_status=pcfg.INVALID_STATUS)

        for trade in trades:
            rule_memo, state = RuleMemo.objects.get_or_create(tid=trade.tid)
            seller_flag = SYS_STATUS_MATCH_FLAGS.get(trade.sys_status, None)
            if seller_flag and seller_flag != rule_memo.seller_flag:
                try:
                    response = taobao_trade_memo_update(tid=trade.tid,
                                                        flag=seller_flag,
                                                        tb_user_id=trade.user.visitor_id)
                    trade_rep = response['trade_memo_update_response']['trade']
                    if trade_rep:
                        RuleMemo.objects.filter(tid=trade.tid).update(seller_flag=seller_flag)
                        MergeTrade.objects.filter(tid=trade_rep['tid']).update(
                            modified=parse_datetime(trade_rep['modified']))
                except:
                    logger.error('update taobao trade flag error', exc_info=True)
