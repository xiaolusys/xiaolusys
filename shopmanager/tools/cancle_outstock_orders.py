from shopback.trades.models import MergeTrade,MergeOrder

def cancle_out_orders(outer_id,outer_sku_id=None,limit=-1):
    
    mos = MergeOrder.objects.filter(outer_id=outer_id,merge_trade__sys_status='WAIT_AUDIT')
    if outer_sku_id:
        mos = mos.filter(outer_sku_id=outer_sku_id)

    mos = mos.order_by('pay_time')

    sids = set([ t.merge_trade.id for t in mos ])

    trades = MergeTrade.objects.filter(id__in=sids)[0:limit]
    
    for t in trades:
        print 'tid:',t.id
        ods = MergeOrder.objects.filter(merge_trade=t,outer_id=outer_id)
        for o in ods:
            o.out_stock = False
            o.save()
