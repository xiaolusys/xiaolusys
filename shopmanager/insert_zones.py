#-*- coding:utf8 -*-
from shopapp.shipclassify.models import ClassifyZone

def parse_address(f):
    
    addrs = []
    for line in f.readlines():
        addrs.append(line.decode('gbk').split(','))
        
    return addrs

def delete_all():
    
    ClassifyZone.objects.all().delete()
    
def insert_zone(fn):
    with open(fn,'r') as f:
        pads = parse_address(f)
        
        for l in pads:
            print l[0],l[1],l[2],l[3]
            ClassifyZone.objects.get_or_create(state=l[0].strip(),city=l[1].strip(),district=l[2].strip(),zone=l[3].strip())
