from shopback.trades.models import MergeTrade
from common.utils import format_date

def parseWeight(weight):
    if not weight:
        return '0.2'
    
    if weight.rfind('.') < 0:
            return str(round(int(weight)/1000.0,2))
        
    return weight

def calc(source_file,to_file):
    
    fs = open(source_file,'r')
    ft = open(to_file,'w+')
     
    for l in fs.readlines():
        ss = l.split()
        if ss[1][0] == '9':
            continue
        
        trades = MergeTrade.objects.filter(out_sid=ss[1],
                                sys_status="FINISHED",is_express_print=True)
        
        if trades.count()>0:
            trade = trades[0]
            print >>ft,','.join(ss),',',parseWeight(trade.weight),',',trade.receiver_state.encode('utf8'),',',trade.weight_time and format_date(trade.weight_time) or ''
        else:
            print >> ft,','.join(ss),',','',',','',',',''
            
            
    fs.close()
    ft.close()
   
if __name__ == '__main__':
    
    if len(sys.argv) != 3:
        print >> sys.stderr,'usage:python *.py <source.csv> <to.csv>'
        sys.exit()
        
    calc(sys.argv[1],sys.argv[2])