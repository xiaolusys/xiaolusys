from shopback.trades.models import MergeTrade,MergeOrder
from shopback.signals import rule_signal

def explain_has_repeated(orders):
    
    mps = set()
    for o in orders:
        code = o.outer_id+o.outer_sku_id
        if code not in mps:
            mps.add(code)
        else:
            return True
        
    return False

def get_repeated_trades():

    orders = MergeOrder.objects.filter(gift_type=3,merge_trade__sys_status__in=('WAIT_AUDIT','WAIT_PREPARE_SEND'))
    
    tids = set([o.merge_trade.id for o in orders])
    uncids = []
    
    for i in tids:
        ods = MergeOrder.objects.filter(merge_trade__id=i,gift_type=3)
        if explain_has_repeated(ods):
            uncids.append(i)

    return uncids

def clear_split_orders():
    rpids = get_repeated_trades()
    for i in rpids:
        print i
        rule_signal.send(sender='combose_split_rule',trade_id=trade_id)
