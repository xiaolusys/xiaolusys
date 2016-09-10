# coding: utf8
import re
import time
import datetime
import base64
import hashlib
import urllib2
import random
from django.conf import settings
from django.core.cache import cache
import cStringIO as StringIO

from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.weixin_apis import WeiXinAPI
from core.upload import push_qrcode_to_remote
from core.logger import log_consume_time

from shopapp.weixin.constants import MAMA_MANAGERS_QRCODE_MAP

import logging
logger = logging.getLogger(__name__)


DEFAULT_MAMA_THUMBNAIL = 'http://img.xiaolumeimei.com/undefined1472268058597lADOa301H8zIzMg_200_200.jpg_620x10000q90g.jpg?imageMogr2/thumbnail/80/crop/80x80/format/jpg'
BASE_MAMA_QRCODE_IMG_URL = [
    'http://7xkyoy.com1.z0.glb.clouddn.com/mama_referal_base11.jpg',
    'http://7xkyoy.com1.z0.glb.clouddn.com/mama_referal_base12.jpg',
    #'http://7xkyoy.com1.z0.glb.clouddn.com/mama_referal_base13.jpg',
]
BASE_MAMA_QRCODE_TEMPLATE_URL = """
    {base_url}?watermark/3/text/{message1}/fontsize/480/gravity/North/dy/170
    /image/{thumbnail}/dissolve/100/gravity/North/dx/0/dy/30/ws/0.2
    /image/{qrcode}/dissolve/100/gravity/Center/dy/110/ws/0.75/
    |imageMogr2/thumbnail/!60p/format/jpg/size-limit/400k
""".replace('\n', '').replace(' ', '')


def get_mama_customer(mama_id):
    mama = XiaoluMama.objects.filter(id=mama_id).first()
    if mama:
        return mama.get_customer()
    else:
        return None


@log_consume_time
def gen_mama_custom_qrcode_url(mama_id, thumbnail, message1='', message2=''):
    wx_api = WeiXinAPI()
    wx_api.setAccountId(appKey=settings.WXPAY_APPID)
    resp = wx_api.createQRcode('QR_SCENE', mama_id)

    qrcode_link = ''
    if 'ticket' in resp:
        #qrcode_link = push_qrcode_to_remote('xiaolumm/referal/%s'% mama_id, resp['url'], box_size=4)
        #qrcode_link += '?imageMogr2/strip/format/jpg/quality/100/interlace/1/thumbnail/80/'
        qrcode_link = wx_api.genQRcodeAccesssUrl(resp['ticket'])
    if not qrcode_link:
        return ''

    thumbnail = re.sub('/0$', '/132', thumbnail)
    params = {
        'base_url': random.choice(BASE_MAMA_QRCODE_IMG_URL),
        'message1': base64.urlsafe_b64encode('我是' + str(message1)),
        'message2': base64.urlsafe_b64encode(str(message2)),
        'thumbnail': base64.urlsafe_b64encode(str(thumbnail)),
        'qrcode': base64.urlsafe_b64encode(str(qrcode_link))
    }
    return BASE_MAMA_QRCODE_TEMPLATE_URL.format(**params)

@log_consume_time
def fetch_wxpub_mama_custom_qrcode_media_id(mama_id, userinfo, wxpubId):
    cache_key = 'wxpub_mama_referal_qrcode_mama_id_%s' % mama_id
    cache_value = cache.get(cache_key) and None
    if not cache_value:
        logger.info('fetch_wxpub_mama_custom_qrcode_media_id cache miss: %s' % mama_id)
        thumbnail = userinfo['headimgurl'] or DEFAULT_MAMA_THUMBNAIL
        message1 = u'%s' % userinfo['nickname']
        message2 = u'长按图片, 识别图中二维码\n有效期截止日期: %s'%\
                   (datetime.datetime.now()+datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        media_url = gen_mama_custom_qrcode_url(mama_id, thumbnail, message1, message2)

        media_body = urllib2.urlopen(media_url).read()
        media_stream = StringIO.StringIO(media_body)

        wx_api = WeiXinAPI()
        wx_api.setAccountId(wxpubId=wxpubId)
        response = wx_api.upload_media(media_stream)
        cache_value = response['media_id']
        cache.set(cache_key, cache_value, 2 * 24 *3600)
    else:
        logger.info('fetch_wxpub_mama_custom_qrcode_media_id cache hit: %s' % mama_id)
    return cache_value

@log_consume_time
def fetch_wxpub_mama_manager_qrcode_media_id(mama_id, wxpubId):

    from flashsale.xiaolumm.models import MamaAdministrator
    mama_administrator = MamaAdministrator.get_mama_administrator(mama_id)
    if not mama_administrator:
        logger.warn('fetch_wxpub_mama_manager_qrcode_media_id administrator loss: %s' % mama_id)
        return
    mama_manager_qrcode = mama_administrator.weixin_qr_img
    cache_key = hashlib.sha1(mama_manager_qrcode).hexdigest()
    cache_value = cache.get(cache_key)
    if not cache_value:
        logger.info('fetch_wxpub_mama_manager_qrcode_media_id cache miss: %s' % mama_id)
        media_body = urllib2.urlopen(mama_manager_qrcode).read()
        media_stream = StringIO.StringIO(media_body)

        wx_api = WeiXinAPI()
        wx_api.setAccountId(wxpubId=wxpubId)
        response = wx_api.upload_media(media_stream)
        cache_value = response['media_id']
        cache.set(cache_key, cache_value, 2 * 24 *3600)
    else:
        logger.info('fetch_wxpub_mama_manager_qrcode_media_id cache hit: %s' % mama_id)
    return cache_value









