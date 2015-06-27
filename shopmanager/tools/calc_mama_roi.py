#-*- coding:utf-8 -*-
import sys
import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models import Sum

from flashsale.xiaolumm.models import XiaoluMama
from flashsale.clickcount.tasks import ClickCount
from flashsale.clickrebeta.tasks import StatisticsShoppingByDay

def calc_mama_roi(xlmm,day_stage=None):
    
    xlmm_id = xlmm.id
    target_date = datetime.date.today() - datetime.timedelta(days=day_stage)
    
    xlmm_ccs =  ClickCount.objects.filter(date__gte=target_date,linkid=xlmm_id)
    valid_num = xlmm_ccs.aggregate(total_usernum=Sum('user_num')).get('total_usernum') or 0
    
    xlmm_ssd = StatisticsShoppingByDay.objects.filter(tongjidate__gte=target_date,linkid=xlmm_id)
    buyer_num = xlmm_ssd.aggregate(total_buyernum=Sum('buyercount')).get('total_buyernum') or 0
    
    return valid_num, buyer_num, valid_num and (buyer_num / (valid_num * 1.0)) or 0 
    
    
def get_all_mama_roi(day_stage=None):
    
    xlmms = XiaoluMama.objects.filter(agencylevel=2)
    roi_xlmms = []
    for xlmm in xlmms:
        charge_date = xlmm.charge_time and xlmm.charge_time.date()
        roi_tp = calc_mama_roi(xlmm,day_stage=day_stage)
        roi_xlmms.append((xlmm.id,charge_date,roi_tp[0],roi_tp[1],roi_tp[2]))
        
    return roi_xlmms

import csv

def dump_to_file(rois):
    
    filename = datetime.datetime.now().strftime('%y%m%d-%h')
    with file('%s.csv'%filename, 'w+') as csvfile:
        writer = csv.writer(csvfile)
        #writer.writerow([u'妈妈编号', u'接管时间', u'点击人数', u'购买人数', u'转化率'])
        writer.writerows(rois)
        
        
if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print >> sys.stderr, "usage: python *.py <stage days> "
    
    sdays = int(sys.argv[1])
    
    rois = get_all_mama_roi(sdays)
    
    dump_to_file(rois)
        
    
    
    
        
    