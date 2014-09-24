from shopapp.weixin.models import WeiXinUser
from .models import WeixinUserPicture

class WeixinSaleService():
    
    _latest_picture = None
    
    def __init__(self,user_openid):
        
        self._latest_picture = self.getUserPicture(user_openid)
    
    def getUserPicture(self,user_openid):
        wx_pics = WeixinUserPicture.objects.filter(user_openid=user_openid).order_by('-created')
        if wx_pics.count() > 0:
            return wx_pics[0]
        return None
        
    def isSaleWaiting(self,user_openid):
        
        
        return False
             
        
    def uploadPicture(self,user_openid,pictures):
        """{u'Count': u'1', u'PicList': {u'item': {u'PicMd5Sum': u'76d89b6f64e738dcc67b081034126d5d'}}}"""
        pass
    
    def updatePictureMemo(self,user_openid,memo):
        pass
    