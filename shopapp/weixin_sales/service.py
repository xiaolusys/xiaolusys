# -*- encoding:utf8 -*-
import os
import time
import urllib2
from django.conf import settings

from shopapp.weixin.models import (WeiXinUser,
                                   AnonymousWeixinUser,
                                   WeiXinAutoResponse)
from shopapp.weixin.weixin_apis import WeiXinAPI
from .models import WeixinUserPicture, WeixinUserAward

WEIXIN_PICTURE_PATH = 'weixin'
import logging

logger = logging.getLogger('django.request')


class WeixinSaleService():
    _wx_user = None
    _wx_api = None

    def __init__(self, wx_user):

        if not isinstance(wx_user, WeiXinUser):
            try:
                wx_user = WeiXinUser.objects.get(openid=wx_user)
            except:
                wx_user = AnonymousWeixinUser()

        self._wx_user = wx_user
        self._wx_api = WeiXinAPI()

    def downloadPicture(self, media_id):

        file_path = os.path.join(settings.MEDIA_ROOT, WEIXIN_PICTURE_PATH)
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        media_url = self._wx_api.getMediaDownloadUrl(media_id)
        req = urllib2.Request(media_url)
        r = urllib2.urlopen(req)
        content = r.read()

        if not r.info().has_key('Content-disposition'):
            raise Exception(u'下载图片返回数据异常')

        # If the response has Content-Disposition, we take file name from it
        fileName = r.info()['Content-disposition'].split('filename=')[1]
        if fileName[0] == '"' or fileName[0] == "'":
            fileName = fileName[1:-1]

        with open(os.path.join(file_path, fileName), 'wb') as f:
            f.write(content)

        relative_file_name = os.path.join(WEIXIN_PICTURE_PATH, fileName)

        WeixinUserPicture.objects.create(user_openid=self._wx_user.openid,
                                         mobile=self._wx_user.mobile,
                                         pic_url=relative_file_name,
                                         pic_type=WeixinUserPicture.COMMENT,
                                         pic_num=1)

    def downloadMenuPictures(self, pictures):
        pass

    def notifyReferalAward(self, title=u"微信邀请奖励"):

        user_openid = self._wx_user.openid
        user_nick = self._wx_user.nickname

        referal_ships = WeiXinUser.objects.VALID_USER.filter(referal_from_openid=user_openid)

        # 短信通知 deprecated


    def notifyAward(self, title=u"微信邀请奖励"):

        user_openid = self._wx_user.openid
        user_nick = self._wx_user.nickname
        user_mobile = self._wx_user.mobile

        referal_users = WeiXinUser.objects.VALID_USER.filter(referal_from_openid=user_openid)
        referal_names = [u.nickname[0:2] for u in referal_users if len(u.nickname) > 1]
        friend_nicks = referal_names and '..,'.join(referal_names[0:2]) or u'无名'

        # deprecated

