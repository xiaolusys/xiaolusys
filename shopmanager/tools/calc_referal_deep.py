from shopapp.weixin.models import WeiXinUser

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
    