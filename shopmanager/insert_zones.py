#-*- coding:utf8 -*-
from shopapp.shipclassify.models import ClassifyZone

def parse_address(f):
    
    addrs = []
    for line in f.readlines():
        addrs.append(line.decode('gbk').split(','))
        
    return addrs

def insertzones(fn):
    with open(fn,'r') as f:
        pads = parse_address(f)
        
        for l in pads:
            print l[0],l[1],l[2],l[3]
            ClassifyZone.objects.get_or_create(state=l[0],city=l[1],district=l[2],zone=l[3])
