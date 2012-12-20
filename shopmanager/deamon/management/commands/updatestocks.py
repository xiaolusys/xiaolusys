#-*- coding:utf8 -*-
import datetime
from daemonextension import DaemonCommand
from django.core.management import call_command
from shopback.items.models import Product,ProductSku
from shopback import paramconfig as pcfg


class Command(DaemonCommand):

    def handle_daemon(self, *args, **options):
        
        source_file  = options.get('file_path','')
        if not source_file:
            return
        
        with open(source_file,'r') as f:
            lines = f.readlines()
            prod_outer_id = ''
            for line in lines:
                items = line.split(',')
                items = self.clearEmptyFields(items)
                if items[0] == '+':
                    prod_outer_id = items[2]
                    if items[1] == '0':
                        Product.objects.filter(outer_id=prod_outer_id).update(collect_num=items[4])
                elif items[0] == '-':
                    ProductSku.objects.filter(outer_id=items[1],product__outer_id=prod_outer_id).update(quantity=items[3])
                    
                
                
    def clearEmptyFields(self,array):
        return [a.strip() for a in array if a!='' or a!=None ]