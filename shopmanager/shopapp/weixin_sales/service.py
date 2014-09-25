import os
import time
from django.conf import settings

from shopapp.weixin.models import WeiXinUser,AnonymousWeixinUser
from .models import WeixinUserPicture

from common.utils import handle_uploaded_file
WEIXIN_PICTURE_PATH  = 'weixin'
import logging
logger = logging.getLogger('django.request')

class WeixinSaleService():
    
    _wx_user = None
    
    def __init__(self,wx_user):
        
        if not isinstance(wx_user,WeiXinUser):
            try:
                wx_user = WeiXinUser.objects.get(openid=wx_user)
            except:
                wx_user = AnonymousWeixinUser()
            
        self._wx_user = wx_user

        
    def uploadPicture(self,pictures,attach_files=[]):
        """{u'Count': u'2', 
            u'PicList': {u'item': [{u'PicMd5Sum': u'15fc32129c54e379b0a5082e7d4deff4'},
                                   {u'PicMd5Sum': u'0c4625ecf16790550b91612c0849fcd1'}]}}"""
        logger.error(attach_files)
        file_names = []
        for attach_file in attach_files:
            
            name = attach_file.name
            file_name = '%s_%d%s'%(self._wx_user.openid,
                                   int(time.time()*1000),
                                   name[name.rfind('.'):]) 
            
            file_path = os.path.join(settings.MEDIA_ROOT,WEIXIN_PICTURE_PATH)
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            
            handle_uploaded_file(attach_file,file_name,file_path=file_path)
            
            file_names.append('%s/%s'%(WEIXIN_PICTURE_PATH,file_name))
            
        WeixinUserPicture.objects.create(user_openid=self._wx_user.openid,
                                         mobile=self._wx_user.mobile,
                                         pic_url=','.join(file_names),
                                         pic_type=WeixinUserPicture.COMMENT,
                                         pic_num=pictures['Count'])
        
        
            
    
