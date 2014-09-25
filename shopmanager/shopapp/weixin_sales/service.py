import os
import time
import urllib2
from django.conf import settings

from shopapp.weixin.models import WeiXinUser,AnonymousWeixinUser
from shopapp.weixin.weixin_apis import WeiXinAPI
from .models import WeixinUserPicture

from common.utils import handle_uploaded_file
WEIXIN_PICTURE_PATH  = 'weixin'
import logging
logger = logging.getLogger('django.request')

class WeixinSaleService():
    
    _wx_user = None
    _wx_api  = None
    
    def __init__(self,wx_user):
        
        if not isinstance(wx_user,WeiXinUser):
            try:
                wx_user = WeiXinUser.objects.get(openid=wx_user)
            except:
                wx_user = AnonymousWeixinUser()
            
        self._wx_user = wx_user
        self._wx_api  = WeiXinAPI()
    
    def downloadPicture(self,media_id):
        
        file_path = os.path.join(settings.MEDIA_ROOT,WEIXIN_PICTURE_PATH)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        
        media_url = self._wx_api.getMediaDownloadUrl()
        req = urllib2.Request(media_url)
        r   = urllib2.urlopen(req)
        content = r.read()
        
        if r.info().has_key('Content-disposition'):
            # If the response has Content-Disposition, we take file name from it
            fileName = r.info()['Content-disposition'].split('filename=')[1]
            if fileName[0] == '"' or fileName[0] == "'":
                fileName = fileName[1:-1]
        elif r.url != url:
            # if we were redirected, the real file name we take from the final URL
            fileName = url2name(r.url)
        
        with open(os.path.join(file_path,fileName), 'wb') as f:
            f.write(content)
        
        relative_file_name = os.path.join(WEIXIN_PICTURE_PATH,fileName)
            
        WeixinUserPicture.objects.create(user_openid=self._wx_user.openid,
                                         mobile=self._wx_user.mobile,
                                         pic_url=relative_file_name,
                                         pic_type=WeixinUserPicture.COMMENT,
                                         pic_num=1)
        
        
    def downloadMenuPictures(self,pictures):        
        pass
