#-*- coding:utf8 -*-
import datetime
from pyExcelerator import *
from models import BabyPhone


def minimalist_xldate_as_datetime(xldate, datemode):
    # datemode: 0 for 1900-based, 1 for 1904-based
    return (
        datetime.datetime(1899, 12, 30)
        + datetime.timedelta(days=xldate + 1462 * datemode)
        )

#保存新生儿信息
def save_babyphone_from_xls(filename):
    sheets = parse_xls(filename)
    for sheet in sheets:
        title,content=sheet
        index_list = [a for a,b in content.keys()]
        max_lines = index_list and max(index_list) or 0
        for i in xrange(0,max_lines):
            try:
                baby,state  = BabyPhone.objects.get_or_create(id=content[(i,2)])
                baby.father = content[(i,0)]
                baby.sex    = content[(i,1)]
                baby.address = content[(i,3)]
                baby.code   = content[(i,4)]
                baby.born   = minimalist_xldate_as_datetime(int(content[(i,5)]),0)
                baby.hospital = content[(i,6)]
                baby.save()
            except Exception,exc:
                print exc.message

#获取重复号码，及重复次数
def get_repeat_phone_list(filename):
    
    phones  = set([])
    repeats = {}
    sheets = parse_xls(filename)
    for sheet in sheets:
        title,content=sheet
        index_list = [a for a,b in content.keys()]
        max_lines = index_list and max(index_list) or 0
        for i in xrange(0,max_lines):
            c  = content[(i,2)]
            try:
                phones.remove(c)
            except:
                phones.add(c)
            else:
                phones.add(c)
                if repeats.has_key(c):
                    repeats[c] += 1
                else:
                    repeats[c] = 1
    return repeats
            
#电话号码差分析
def analysis_difference_baby_phone():            
    pass

