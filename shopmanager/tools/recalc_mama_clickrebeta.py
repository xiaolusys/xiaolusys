import sys
import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShopping,StatisticsShoppingByDay
from flashsale.xiaolumm.models import CarryLog,XiaoluMama
from flashsale.daystats.models import PopularizeCost

def calc_order_count(clog):
    t = clog.carry_date
    mm_linkid = clog.xlmm
    
    start = datetime.datetime(t.year, t.month, t.day)
    end   = datetime.datetime(t.year, t.month, t.day,23,59,59)
    
    xlmm = XiaoluMama.objects.get(id=mm_linkid)
    cc = ClickCount.objects.get(linkid=mm_linkid,date=t)
    
    shopings = StatisticsShopping.objects.filter(linkid=mm_linkid,shoptime__range=(start,end))
    nkcount = shopings.values('wxordernick').distinct().count()
    mbcount = shopings.values('openid').distinct().count()
    
    ordernum = max(nkcount,mbcount)
    
    xlmm = XiaoluMama.objects.get(id=mm_linkid)
    max_count = xlmm.get_Mama_Max_Valid_Clickcount(ordernum,t)
    valid_price = xlmm.get_Mama_Click_Price_By_Day(ordernum,day_date=t)
    
    valid_count = min(cc.user_num, max_count)
    
    calcvalue = valid_count * valid_price
    if clog.value < calcvalue:
        cc.valid_num = valid_count
        cc.save()
        ssp = StatisticsShoppingByDay.objects.filter(linkid=mm_linkid,tongjidate=t)
        if ssp.exists():
            ss = ssp[0]
            ss.buyercount = ordernum
            ss.save()
        diff_value = calcvalue - clog.value
        clog.value += diff_value
        xlmm.cash += diff_value
        xlmm.save()
        print 'xlmm:',xlmm.id,diff_value
        
    return valid_count * valid_price

if __name__ == '__main__':
    
    diff_cnt = 0
    pre_amount = 0
    post_amount = 0
    diff_amount = 0
    clogs = CarryLog.objects.filter(carry_date__range=(datetime.datetime(2016,3,2),
                                                       datetime.datetime(2016,3,4)),
                                    log_type=CarryLog.CLICK_REBETA,
                                    xlmm__in=(12238,15735,4460,))
    print 'total count:',clogs.count()
    
    for clog in clogs:
        pre_amount += clog.value
        pamount = calc_order_count(clog)
        post_amount += pamount
        if clog.value != pamount:
            diff_cnt += 1
            
        if diff_cnt % 50 == 0:
            print diff_cnt
            
    print 'diff:', diff_cnt , pre_amount, post_amount
    

