from shopapp.weixin.models import WeiXinUser
from .models import WeixinUserPicture

class WeixinSaleService():
    
    
    def __init__(self):
        pass
        
    def isWaitingMemo(self,user_openid):
        
        wx_pics = WeixinUserPicture.objects.filter(user_openid=user_openid).order_by('-created')
        if wx_pics.count() > 0:
            return wx_pics[0].upload_ended < datetime.datetime.now()
        return False
             
        
    def uploadPicture(self,user_openid,pictures):
        pass
    
    def updatePictureMemo(self,user_openid,memo):
        pass
    