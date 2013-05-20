#-*- coding:utf8 -*-
import datetime
from daemonextension import DaemonCommand
from django.core.management import call_command
from shopback.items.models import Product,ProductSku
from shopback import paramconfig as pcfg


class Command(DaemonCommand):

    def handle_daemon(self, *args, **options):
        
        target_file  = options.get('file_path','/tmp/dumpprodsku.txt')
        encoding     = options.get('encoding','utf8')
        
        prods = Product.objects.filter(status=pcfg.NORMAL)
        with open(target_file,'w') as f:
            for prod in prods:
                prod_skus = prod.prod_skus.filter(status=pcfg.NORMAL)
                has_sku_char   = '1' if prod_skus.count()>0 else '0'
                
                if prod_skus.count() == 0 :
                    print >> f,has_sku_char,',',prod.outer_id,',',prod.name.encode(encoding),',','-',',','-',',',prod.std_purchase_price
                else:
                    for sku in prod_skus:
                        print >> f,has_sku_char,',',prod.outer_id,',',prod.name.encode(encoding),',',sku.outer_id,',',sku.properties_name.encode(encoding),',',sku.std_purchase_price
                        
                print >> f, '\n'