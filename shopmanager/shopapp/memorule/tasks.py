#-*- coding:utf8 -*-
import json
import time
import datetime
from celery.task import task
from django.db.models import Q
from shopback.trades.models import MergeTrade
from shopback.orders.models import Order,Trade
from shopapp.memorule.models import RuleMemo,TradeRule
from shopback.logistics.models import LogisticsCompany
from shopback.signals import rule_signal
import logging

logger = logging.getLogger('memorule.handler')

@task()
def updateTradeAndOrderByRuleMemo():
    
    rule_memos = RuleMemo.objects.filter(is_used=False)
    for rule_memo in rule_memos:
        rule_memo_dict = json.loads(rule_memo.rule_memo)
        try:
            merge_trade = MergeTrade.objects.get(tid=rule_memo_dict['tid'])
        except MergeTrade.DoesNotExist:
            pass
        else:
            try:
                express_name = rule_memo_dict.get('post',None)
                if express_name :
                    express_name = express_name.strip()
                    try:
                        logistics_company = LogisticsCompany.objects.get(name=express_name)
                    except:
                        pass
                    else:
                        merge_trade.logistics_company_name = express_name
                        merge_trade.logistics_company_code = logistics_company.code
                address = rule_memo_dict.get('addr',None)
                if address:
                    merge_trade.receiver_address = address
                
                orders_data = rule_memo_dict['data']
                for o in orders_data:
                    order = Order.objects.get(Q(outer_id=o['pid'])|Q(outer_sku_id=o['pid']),trade=rule_memo_dict['tid'])
                    sku_properties = ' '.join([v for k,v in o['property'].items()])
                    order.sku_properties_name += sku_properties
                    order.save()
                merge_trade.save()
                
                rule_signal.send(sender='trade_rule',trade_id=merge_trade.tid)
                
                rule_memo.is_used = True
                rule_memo.save()
            except Exception,exc:
                logger.error('update rule error',exc_info=True)
            
            