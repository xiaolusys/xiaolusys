import sys

from django.core.management import setup_environ
import settings
setup_environ(settings)

from shopback.items.models import Product,ProductSku
from shopback import paramconfig as pcfg

def product_out(out_filename):
    
    with open(out_filename,'w+') as f:
        prods = Product.objects.filter(status__in=(pcfg.NORMAL,pcfg.REMAIN))
        for prod in prods:
            
            skus = prod.pskus.filter(is_split=True)
            if skus.count() > 0:
                for sku in skus:
                    print >>f,prod.outer_id,',',prod.name.encode('utf8'),',',sku.outer_id,',',sku.name.encode('utf8'),',',sku.quantity,',',sku.cost
            else:
                print >>f,prod.outer_id,',',prod.name.encode('utf8'),',','',',','',',',prod.collect_num,',',prod.cost
            print >>f , '\n'
                
                
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >> sys.stderr, "usage: python *.py  <out-file.csv>"
        sys.exit(1)
    
    out_file = sys.argv[1]

    product_out(out_file)

    
    