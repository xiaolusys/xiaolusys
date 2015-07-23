import sys

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models import Sum
from flashsale.xiaolumm.models import XiaoluMama,CarryLog

def compare_cash_with_log():
    
    over_list = []
    xlmms = XiaoluMama.objects.filter(agencylevel=2)
    for xlmm in xlmms:
        clogs = CarryLog.objects.filter(xlmm=xlmm.id,status=CarryLog.CONFIRMED)
        xlmm_cins = clogs.filter(carry_type=CarryLog.CARRY_IN).aggregate(total_in=Sum('value')).get('total_in') or 0
        xlmm_cout = clogs.filter(carry_type=CarryLog.CARRY_OUT).aggregate(total_out=Sum('value')).get('total_out') or 0
        
        profite = xlmm_cins - xlmm_cout
        if xlmm.cash == profite:
            continue
        
        over_list.append([xlmm.id,xlmm.weikefu,xlmm.cash,profite,xlmm.cash - profite])
                  
    return over_list
    
if __name__ == '__main__':
    if len(sys.argv) != 1:
        print >> sys.stderr, "usage: python *.py "
        sys.exit(1)
#     
#     out_file = sys.argv[1]

    unmatch = compare_cash_with_log()
    print 'unmatch count:',len(unmatch)
    print '===unmatch list====:'
    for l in unmatch:
        print l
    