#-*- coding:utf8 -*-
import datetime
from django.db.models import Q

from pyExcelerator import *

from models import BabyPhone

state=['北京','天津','上海','重庆','河北','山西','辽宁','吉林','黑龙','江苏','浙江','安徽',
       '福建','江西','山东','河南','湖南','湖北','广东','海南','四川','贵州','云南','陕西',
       '甘肃','青海','台湾','西藏','内蒙古','广西','宁夏','新疆']

def minimalist_xldate_as_datetime(xldate, datemode):
    # datemode: 0 for 1900-based, 1 for 1904-based
    return (
        datetime.datetime(1899, 12, 30)
        + datetime.timedelta(days=xldate + 1462 * datemode)
        )

def get_state_throught_addr(addr):

    if not addr or len(addr)<2:
        return ''

    for s in state:
        index = addr.find(s.decode('utf8'))
        if index >=0:
            return s
    return ''


#保存新生儿信息,返回保存重复信息
def save_babyphone_from_xls(filename):
    fn=3;fm=4;mn=1;mm=2;bn=-1;addr=5;se=-1;br=0;cd=-1;hp=-1

    sheets = parse_xls(filename)
    repeats = {}
    for sheet in sheets:
        title,content=sheet
        index_list = [a for a,b in content.keys()]
        max_lines = index_list and max(index_list) or 0
        for i in xrange(0,max_lines):
            father_name   = fn>=0 and content.get((i,fn),None) or ''
            father_mobile = fm>=0 and content.get((i,fm),'').isdigit() and int(content[(i,fm)]) or None
            mather_name   = mn>=0 and content.get((i,mn),None) or ''
            mather_mobile = mm>=0 and content.get((i,mm),'').isdigit() and int(content[(i,mm)]) or None
            baby_name     = bn>=0 and content.get((i,bn),None) or ''
            address       = addr>=0 and content.get((i,addr),None) or ''
            sex           = se>=0 and content.get((i,se),None) or ''
            #born          =minimalist_xldate_as_datetime(int(content[(i,5)]),0)

            born_time = content.get((i,br),None)
            if type(born_time) == int:
                born  = minimalist_xldate_as_datetime(born_time,0)
            elif  type(born_time) == str:
                born  = datetime.datetime.strptime(born_time,'%Y-%m-%d')
            else:
                born = None

            code          = cd>=0 and content.get((i,cd),None) or ''
            hospital      = hp>=0 and content.get((i,hp),None) or ''

            query =None
            if father_mobile :
                query = Q(fa_mobile=father_mobile)|Q(ma_mobile=father_mobile)

            if mather_mobile:
                query = Q(fa_mobile=mather_mobile)|Q(ma_mobile=mather_mobile)

            is_phone_exist = BabyPhone.objects.filter(query).count()>0
            if is_phone_exist:
                if repeats.has_key((father_mobile,mather_mobile)):
                    repeats[(father_mobile,mather_mobile)] += 1
                else:
                    repeats[(father_mobile,mather_mobile)] = 1

            baby,state    = BabyPhone.objects.get_or_create(fa_mobile=father_mobile,ma_mobile=mather_mobile)
            baby.father   = father_name
            baby.mather   = mather_name
            baby.name     = baby_name
            baby.sex      = sex
            baby.state    = get_state_throught_addr(address)
            baby.address  = address
            baby.code     = code
            baby.born     = born
            baby.hospital = hospital
            baby.save()

    return repeats


#电话号码差分析
def analysis_difference_baby_phone():
    pass

