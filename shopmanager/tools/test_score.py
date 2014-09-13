from shopapp.weixin.models import VipCode,SampleOrder,Refund
from shopback.trades.models import MergeTrade
from shopapp.signals import (weixin_referal_signal,
                             weixin_refund_signal,
                             confirm_trade_signal)

def referal_score():
    
    index = 0 
    sos = SampleOrder.objects.exclude(vipcode='None')
    print 'sample order count:',sos.count()
    for so in sos:
        vipcodes = VipCode.objects.filter(code=so.vipcode)
        for vc in vipcodes:
            weixin_referal_signal.send(sender=SampleOrder,
                                       user_openid=so.user_openid,
                                       referal_from_openid=vc.owner_openid.openid)
        if index % 100 == 0:
            print index
        index += 1
            
            
def confirm_trade_score():
    
    index = 0 
    dt = datetime.datetime(2014,8,1)
    mts = MergeTrade.objects.filter(is_express_print=True,
                                    pay_time__gt=dt,
                                    sys_status='FINISHED')
    print 'merge trade count:',mts.count()
    for t in mts:
        confirm_trade_signal.send(sender=MergeTrade,trade_id=t.id)
        
        if index % 100 == 0:
            print index
        index += 1
        
            
def refund_score():
    
    rfs = Refund.objects.filter(refund_type=1)
    print 'refund order count:',rfs.count()
    for rf in rfs:
        if len(rf.user_openid)<25:
            vc = VipCode.objects.filter(code=rf.vip_code,usage_count__gte=10)
            if vc.count() > 0:
                rf.user_openid = vc[0].owner_openid.openid
                rf.save()
                
        if rf.refund_status == 3:
            weixin_refund_signal.send(sender=Refund,
                                       refund_id=rf.id)
            