import sys
from datetime import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db import connection

from shopback.trades.models import MergeTrade,MergeOrder
from shopback.items.models import Product

def dump_hotsale(start,end,limit=150):
     
     sql = ''' 
 select substring(outer_id, 1, CHAR_LENGTH(outer_id) -1) as souter_id,
       sum(num) as cnum
  from shop_trades_mergeorder
 where sys_status= 'IN_EFFECT'
   and pay_time between %s and %s
   and is_merge= 0
   and CHAR_LENGTH(outer_id)>= 9
 group by souter_id
 order by cnum desc
 limit %s;
     '''
     
     cursor = connection.cursor()
     cursor.execute(sql,[start,end,limit])
     plist = cursor.fetchall()
     cursor.close()

     for pt in plist:
          flist = []
          pouter = pt[0].strip()
          psales = int(pt[1])
          ps = Product.objects.filter(outer_id__startswith=pouter,status='normal')
          if ps.count() > 0 :
               p = ps[0]
               print p.sale_time,'\t',pouter,'\t',p.name,'\t',psales,'\t',p.pic_path


if __name__ == "__main__":
     
    if len(sys.argv) != 4:
        print >> sys.stderr, "usage: python *.py  <datefrom> <dateto> <limit>"
        sys.exit(1)
    
    df = datetime.strptime(sys.argv[1],"%Y-%m-%d")
    dt = datetime.strptime(sys.argv[2],"%Y-%m-%d")
    limits = int(sys.argv[3])

    dump_hotsale(df,dt,limits)
