from shopapp.weixin.models import WeiXinUser,SampleOrder,WeixinUserScore
from shopapp.weixin_score.models import SampleFrozenScore
from shopapp.signals import weixin_sampleconfirm_signal
from django.db.models import F
"""
<WeiXinUser:20140801weixin,>    866988    
    <WeiXinUser:20140802qq,>    668678   
    <WeiXinUser:20140828qinbeiweibo,>    608638    
    <WeiXinUser:20140828qinbeiweixin,>    866678    
    <WeiXinUser:20140802other,>    898786
    <WeiXinUser:20140828weibo,> 678986
"""

def iter_referal(user_openid,rd_dict):
    
    rd_dict[user_openid] = {'h':1,'s':1}
    wx_users = WeiXinUser.objects.filter(referal_from_openid=user_openid)
    max_height = 0 
    for wx_user in wx_users:
        referal_openid = wx_user.openid
        iter_referal(referal_openid,rd_dict)
        referal_dict = rd_dict[referal_openid]
        
        rd_dict[user_openid]['s'] += referal_dict['s']
        max_height = max(referal_dict['h'],max_height)
        
    rd_dict[user_openid]['h'] += max_height

def calc_referal_top10(user_openid): 
      
    rd_dict = {}
     
    iter_referal(user_openid,rd_dict)
    
    return sorted(rd_dict.items(),key=lambda d:d[1]['h'],reverse=True)[0:10]

def calc_sample_order_score():
    
    sods = SampleOrder.objects.filter(sample_product__id=3)
    for sod in sods:
        weixin_sampleconfirm_signal.send(sender=SampleOrder,sample_order_id=sod.id)
        
        
def restore_frozen_score():
    
    sfs = SampleFrozenScore.objects.filter(frozen_score__gt=0)
    for sf in sfs:
        so = SampleOrder.objects.get(user_openid=sf.user_openid,sample_product__id=3)
        if so.status > 0:
            continue
        
        scores = WeixinUserScore.objects.filter(user_openid=sf.user_openid)
        if scores.count() == 0:
            continue
        
        iscore = scores[0]
        iscore.user_score = F('user_score')+sf.frozen_score
        iscore.save()
        
        sf.frozen_score = 0
        sf.save()
        
        
        
        
    