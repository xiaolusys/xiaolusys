import sys
from datetime import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models import Q
from shopback.items.models import Product

def calc_top_unsale_proudct():
    
    outer_idset = set([])
    sale_top    = {}
    product_qs = Product.objects.filter(status=Product.NORMAL,collect_num__gt=0).extra(where=["CHAR_LENGTH(outer_id)>=9"])\
                .filter(Q(outer_id__startswith="9")|Q(outer_id__startswith="1")|Q(outer_id__startswith="8"))
    
    for product in product_qs:
        outer_id  = product.outer_id
        router_id = outer_id[0:-1]
        if  outer_id in outer_idset:
            continue
        outer_idset.add(outer_id)
        if router_id not in sale_top:
            sale_top[router_id] = {'name':product.name,'collect_num':product.collect_num}
        else:
            sale_top[router_id]['collect_num'] += product.collect_num
            
    sale_list = sorted(sale_top.items(),key=lambda d:d[1]['collect_num'],reverse=True)
    
    return sale_list

if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        print >> sys.stderr, "usage: python *.py  top_num"
        sys.exit(1)
    
    top = int(sys.argv[1])

    top_list = calc_top_unsale_proudct()[0:top]
    for p in top_list:
        print p[0],p[1]['name'],p[1]['collect_num']

