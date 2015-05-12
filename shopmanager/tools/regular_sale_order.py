import sys
import time
import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models import Sum
from shopback import paramconfig as pcfg
from shopback.trades.models import MergeTrade,MergeOrder,Refund

def regular(outer_ids=[],remind_time=datetime.datetime.now()):
    
    start_dt = datetime.datetime(2014,11,1)
    end_dt   = datetime.datetime(2014,12,1)

    mos = MergeOrder.objects.filter(outer_id="2116CG1",outer_sku_id="67ZB")\
        .filter(pay_time__gt=start_dt,pay_time__lt=end_dt,is_merge=False)\
        .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)\
        .exclude(merge_trade__sys_status=pcfg.EMPTY_STATUS)\
        .exclude(merge_trade__type=pcfg.EXCHANGE_TYPE,sys_status=pcfg.INVALID_STATUS)

    print 'total:',mos.filter(is_merge=False).aggregate(total_fee=Sum('payment')),mos.count()
    mtids = set([o.merge_trade.tid for o in mos])
    
    order_qs = MergeOrder.objects.filter(outer_id="2116CG1",outer_sku_id="67ZB",sys_status=pcfg.IN_EFFECT,pay_time__gte=start_dt,pay_time__lte=end_dt,merge_trade__status__in=pcfg.ORDER_SUCCESS_STATUS).exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE).exclude(merge_trade__sys_status__in=(pcfg.INVALID_STATUS,pcfg.ON_THE_FLY_STATUS)).exclude(merge_trade__sys_status=pcfg.FINISHED_STATUS,merge_trade__is_express_print=False)
    print 'real:',order_qs.aggregate(total_fee=Sum('payment')),order_qs.count()
    otids = set([o.merge_trade.tid for o in order_qs])

    effect_oids = [o[0] for o in order_qs.values_list('oid') if len(o[0]) > 6 ]
    refunds = Refund.objects.filter(oid__in=effect_oids,status__in=(pcfg.REFUND_WAIT_SELLER_AGREE,pcfg.REFUND_CONFIRM_GOODS,pcfg.REFUND_SUCCESS))

    print 'refund:',refunds.aggregate(total_refund_fee=Sum('refund_fee')),refunds.count()

    print 'final:',otids - mtids
if __name__ == "__main__":
    
    #if len(sys.argv) != 3:
    #    print >> sys.stderr, "usage: python *.py <outer_ids> <regular_days>"
    
    regular()
    
    

    
